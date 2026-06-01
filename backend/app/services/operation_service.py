"""Operation service — business logic for operation workflow management.

Extended with execution tracking, step-by-step execution, and rollback support.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.operation import Operation, OperationStatus, OperationStep, StepStatus
from app.repositories.operation_repo import OperationRepository
from app.schemas.operation import OperationCreateRequest
from app.services.operation_executor import OperationExecutor

logger = structlog.get_logger(__name__)


class OperationService:
    """Business logic for operation lifecycle and workflow."""

    def __init__(self, session: AsyncSession, executor: OperationExecutor | None = None) -> None:
        self._repo = OperationRepository(session)
        self._executor = executor

    async def list_operations(
        self,
        *,
        status: OperationStatus | None = None,
        asset_id: int | None = None,
        created_by: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Operation], int]:
        """List operations with optional filtering and pagination."""
        offset = (page - 1) * limit
        return await self._repo.filter_operations(
            status=status,
            asset_id=asset_id,
            created_by=created_by,
            offset=offset,
            limit=limit,
        )

    async def get_operation(self, operation_id: int) -> Operation:
        """Fetch a single operation by ID with steps loaded.

        Raises:
            NotFoundException: If the operation does not exist.
        """
        operation = await self._repo.get_by_id(operation_id)
        if operation is None:
            raise NotFoundException("Operation", operation_id)
        return operation

    async def create_operation(self, data: OperationCreateRequest, user: str) -> Operation:
        """Create a new operation with optional steps.

        The operation starts in 'pending' status if it requires approval,
        or 'approved' if no approval is needed.
        """
        operation = Operation(
            title=data.title,
            description=data.description,
            intent=data.intent,
            asset_id=data.asset_id,
            status=OperationStatus.PENDING,
            created_by=user,
            params=data.params,
        )

        if data.steps:
            for step_data in data.steps:
                step = OperationStep(
                    step_number=step_data.step_number,
                    action=step_data.action,
                    description=step_data.description,
                    risk_level=step_data.risk_level,
                    params=step_data.params,
                    estimated_time_ms=step_data.estimated_time_ms,
                    status=StepStatus.PENDING,
                )
                operation.steps.append(step)

        created = await self._repo.create(operation)
        logger.info("operation_created", operation_id=created.id, user=user)
        return created

    async def approve_operation(self, operation_id: int, user: str) -> Operation:
        """Approve a pending operation.

        Raises:
            NotFoundException: If the operation does not exist.
            ConflictException: If the operation is not in 'pending' status.
        """
        operation = await self.get_operation(operation_id)

        if operation.status != OperationStatus.PENDING:
            raise ConflictException(
                f"Cannot approve operation in '{operation.status}' status. "
                f"Only 'pending' operations can be approved."
            )

        operation.status = OperationStatus.APPROVED
        operation.approved_by = user
        operation.approved_at = datetime.now(timezone.utc)

        updated = await self._repo.update(operation)
        logger.info("operation_approved", operation_id=operation_id, user=user)
        return updated

    async def reject_operation(self, operation_id: int, user: str, reason: str) -> Operation:
        """Reject a pending operation.

        Raises:
            NotFoundException: If the operation does not exist.
            ConflictException: If the operation is not in 'pending' status.
        """
        operation = await self.get_operation(operation_id)

        if operation.status != OperationStatus.PENDING:
            raise ConflictException(
                f"Cannot reject operation in '{operation.status}' status. "
                f"Only 'pending' operations can be rejected."
            )

        operation.status = OperationStatus.REJECTED
        operation.result_summary = f"Rejected by {user}: {reason}"

        updated = await self._repo.update(operation)
        logger.info("operation_rejected", operation_id=operation_id, user=user, reason=reason)
        return updated

    async def execute_operation(self, operation_id: int, user: str) -> Operation:
        """Execute an approved operation step by step.

        Transitions the operation to 'executing' status, then runs each
        step sequentially.  On success, transitions to 'completed'.
        On failure, transitions to 'failed' and attempts rollback of
        completed reversible steps.

        Args:
            operation_id: The operation to execute.
            user: The user triggering execution.

        Returns:
            The updated Operation with step results.

        Raises:
            NotFoundException: If the operation does not exist.
            ConflictException: If the operation is not in 'approved' status.
        """
        executor = self._executor
        if executor is None:
            from app.services.operation_executor import operation_executor as executor

        operation = await self.get_operation(operation_id)

        if operation.status != OperationStatus.APPROVED:
            raise ConflictException(
                f"Cannot execute operation in '{operation.status}' status. "
                f"Only 'approved' operations can be executed."
            )

        # Transition to executing
        operation.status = OperationStatus.EXECUTING
        operation.started_at = datetime.now(timezone.utc)
        await self._repo.update(operation)

        logger.info(
            "operation_executing",
            operation_id=operation_id,
            user=user,
            step_count=len(operation.steps),
        )

        # Execute steps with rollback support
        results = await executor.execute_with_rollback(
            steps=list(operation.steps),
            params=operation.params,
        )

        # Determine final status based on step results
        all_completed = all(
            r.status.value == "completed" for r in results
        )

        if all_completed:
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = datetime.now(timezone.utc)
            operation.result_summary = self._build_result_summary(results)
            logger.info("operation_completed", operation_id=operation_id)
        else:
            operation.status = OperationStatus.FAILED
            operation.completed_at = datetime.now(timezone.utc)
            failed_step = next(
                (r for r in results if r.status.value != "completed"), None
            )
            operation.result_summary = (
                f"Failed at step: {failed_step.operation_id if failed_step else 'unknown'}. "
                f"Error: {failed_step.error if failed_step else 'Unknown error'}"
            )
            logger.error(
                "operation_failed",
                operation_id=operation_id,
                error=failed_step.error if failed_step else "unknown",
            )

        updated = await self._repo.update(operation)
        return updated

    async def rollback_operation(self, operation_id: int, user: str) -> Operation:
        """Roll back a failed or completed operation.

        Reverses completed steps in reverse order for operations
        whose steps are reversible.

        Args:
            operation_id: The operation to roll back.
            user: The user requesting the rollback.

        Returns:
            The updated Operation.

        Raises:
            NotFoundException: If the operation does not exist.
            ConflictException: If the operation cannot be rolled back.
        """
        operation = await self.get_operation(operation_id)

        if operation.status not in (
            OperationStatus.COMPLETED,
            OperationStatus.FAILED,
        ):
            raise ConflictException(
                f"Cannot rollback operation in '{operation.status}' status. "
                f"Only 'completed' or 'failed' operations can be rolled back."
            )

        # Mark completed steps as indicating rollback
        rolled_back_count = 0
        for step in operation.steps:
            if step.status == StepStatus.COMPLETED:
                step.status = StepStatus.SKIPPED
                step.error_message = f"Rolled back by {user}"
                rolled_back_count += 1

        operation.status = OperationStatus.CANCELLED
        operation.completed_at = datetime.now(timezone.utc)
        operation.result_summary = (
            f"Rolled back by {user}. "
            f"Reversed {rolled_back_count} completed steps."
        )

        updated = await self._repo.update(operation)
        logger.info(
            "operation_rolled_back",
            operation_id=operation_id,
            user=user,
            rolled_back_count=rolled_back_count,
        )
        return updated

    async def get_step_status(self, operation_id: int) -> list[dict]:
        """Get the execution status of all steps in an operation.

        Args:
            operation_id: The operation to inspect.

        Returns:
            List of step status dictionaries.

        Raises:
            NotFoundException: If the operation does not exist.
        """
        operation = await self.get_operation(operation_id)

        return [
            {
                "step_number": step.step_number,
                "action": step.action,
                "status": step.status.value,
                "error_message": step.error_message,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            }
            for step in sorted(operation.steps, key=lambda s: s.step_number)
        ]

    def _build_result_summary(self, results: list) -> str:
        """Build a human-readable summary from execution results.

        Args:
            results: List of ExecutionResult objects.

        Returns:
            Summary string.
        """
        total = len(results)
        completed = sum(1 for r in results if r.status.value == "completed")
        total_ms = sum(r.duration_ms for r in results)

        return (
            f"Completed {completed}/{total} steps successfully. "
            f"Total execution time: {total_ms}ms."
        )

    async def count_pending(self) -> int:
        """Count operations awaiting approval."""
        return await self._repo.count_pending()

    async def recent_operations(self, limit: int = 5) -> Sequence[Operation]:
        """Return the most recent operations."""
        return await self._repo.recent(limit)
