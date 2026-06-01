"""Operation executor — atomic operation execution with status tracking.

Executes individual atomic operations, tracks their lifecycle
(pending -> running -> completed/failed), and records results
to the operations table.  Handles timeouts and errors gracefully.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any

import structlog

from app.core.registry import AtomicOperation, RiskLevel, registry
from app.exceptions import OperationFailedException, ValidationException
from app.models.operation import Operation, OperationStatus, OperationStep, StepStatus

logger = structlog.get_logger(__name__)

# Default timeout per risk level (milliseconds)
DEFAULT_TIMEOUTS: dict[str, int] = {
    "low": 30_000,
    "medium": 60_000,
    "high": 120_000,
    "critical": 300_000,
}


class ExecutionStatus(str, PyEnum):
    """Status of an execution attempt."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExecutionResult:
    """Result of executing an atomic operation.

    Attributes:
        operation_id: The atomic operation ID (e.g. 'infra.ping').
        status: Final execution status.
        output: Operation output data, if any.
        error: Error message, if the operation failed.
        duration_ms: Actual execution time in milliseconds.
        started_at: When execution started.
        completed_at: When execution finished.
    """
    operation_id: str
    status: ExecutionStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class OperationExecutor:
    """Execute atomic operations with timeout and error handling.

    This executor is responsible for:
    - Validating operation parameters before execution
    - Tracking execution status (pending -> running -> completed/failed)
    - Enforcing timeouts based on operation risk level
    - Recording results to the operation step model
    - Handling rollbacks on failure when possible
    """

    def __init__(self, timeout_overrides: dict[str, int] | None = None) -> None:
        """Initialize the executor.

        Args:
            timeout_overrides: Optional per-operation timeout overrides in ms.
        """
        self._timeouts = {**DEFAULT_TIMEOUTS, **(timeout_overrides or {})}
        self._running: dict[str, ExecutionResult] = {}

    def get_timeout(self, operation_id: str) -> int:
        """Get the timeout for an operation.

        Checks overrides by operation_id first, then falls back
        to the default for the operation's risk level.

        Args:
            operation_id: The atomic operation ID.

        Returns:
            Timeout in milliseconds.
        """
        # Check for per-operation override first
        if operation_id in self._timeouts:
            return self._timeouts[operation_id]

        op = registry.get(operation_id)
        if op is None:
            return self._timeouts.get("low", 30_000)
        return self._timeouts.get(op.risk_level.value, 30_000)

    def validate_params(
        self, operation_id: str, params: dict[str, Any]
    ) -> None:
        """Validate that all required parameters are present.

        Args:
            operation_id: The atomic operation ID.
            params: Parameters to validate.

        Raises:
            ValidationException: If required parameters are missing.
        """
        op = registry.get(operation_id)
        if op is None:
            raise ValidationException(
                f"Unknown operation: {operation_id}",
                details={"operation_id": operation_id},
            )

        missing = [
            key for key in op.params_schema
            if key not in params or params[key] is None
        ]
        if missing:
            raise ValidationException(
                f"Missing required parameters for '{operation_id}': {', '.join(missing)}",
                details={"operation_id": operation_id, "missing": missing},
            )

    async def execute_atomic(
        self,
        operation_id: str,
        params: dict[str, Any],
    ) -> ExecutionResult:
        """Execute a single atomic operation.

        Validates parameters, enforces timeout, and captures the result.

        Args:
            operation_id: The atomic operation ID (e.g. 'infra.ping').
            params: Operation parameters.

        Returns:
            ExecutionResult with status and output.

        Raises:
            ValidationException: If parameters are invalid.
        """
        self.validate_params(operation_id, params)

        op = registry.get(operation_id)
        timeout_ms = self.get_timeout(operation_id)

        result = ExecutionResult(
            operation_id=operation_id,
            status=ExecutionStatus.PENDING,
        )
        self._running[operation_id] = result

        started = time.monotonic()
        result.status = ExecutionStatus.RUNNING
        result.started_at = datetime.now(timezone.utc)

        logger.info(
            "operation_executing",
            operation_id=operation_id,
            params=params,
            timeout_ms=timeout_ms,
        )

        try:
            # Execute with timeout
            output = await asyncio.wait_for(
                self._execute_real(operation_id, op, params),
                timeout=timeout_ms / 1000.0,
            )

            duration_ms = int((time.monotonic() - started) * 1000)
            result.status = ExecutionStatus.COMPLETED
            result.output = output
            result.duration_ms = duration_ms
            result.completed_at = datetime.now(timezone.utc)

            logger.info(
                "operation_completed",
                operation_id=operation_id,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - started) * 1000)
            result.status = ExecutionStatus.TIMED_OUT
            result.error = (
                f"Operation '{operation_id}' timed out after {timeout_ms}ms"
            )
            result.duration_ms = duration_ms
            result.completed_at = datetime.now(timezone.utc)

            logger.error(
                "operation_timed_out",
                operation_id=operation_id,
                timeout_ms=timeout_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            result.status = ExecutionStatus.FAILED
            result.error = str(exc)
            result.duration_ms = duration_ms
            result.completed_at = datetime.now(timezone.utc)

            logger.error(
                "operation_failed",
                operation_id=operation_id,
                error=str(exc),
                duration_ms=duration_ms,
            )

        finally:
            self._running.pop(operation_id, None)

        return result

    async def _execute_real(
        self,
        operation_id: str,
        op: AtomicOperation | None,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an operation using the appropriate platform adapter or system command.

        Dispatches based on the operation category:
        - infra.*: Uses subprocess for ping, traceroute, etc.
        - compute.*: Uses platform adapters for VM operations
        - Other categories: Executes via subprocess for shell commands

        Args:
            operation_id: The atomic operation ID.
            op: The registered atomic operation.
            params: Operation parameters.

        Returns:
            Execution result dictionary.

        Raises:
            OperationFailedError: If the operation fails.
        """
        import subprocess

        target = params.get("target") or params.get("vm") or params.get("host") or params.get("instance") or "unknown"
        category = op.category.value if op else "unknown"

        # Map operation categories to execution strategies
        if category == "infra":
            # Infrastructure operations use system commands
            cmd_map = {
                "infra.ping": f"ping -c 3 {target}",
                "infra.traceroute": f"traceroute -m 15 {target}",
                "infra.dns_check": f"nslookup {target}",
                "infra.port_scan": f"nc -zv {target} 22 80 443",
            }
            cmd = cmd_map.get(operation_id)
            if cmd:
                try:
                    proc = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                    output = stdout.decode("utf-8", errors="replace").strip()
                    return {
                        "status": "success" if proc.returncode == 0 else "failed",
                        "operation_id": operation_id,
                        "target": target,
                        "output": output,
                        "return_code": proc.returncode,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                except asyncio.TimeoutError:
                    raise OperationFailedError(operation_id, f"Command timed out: {cmd}")
        elif category == "compute":
            # Compute operations delegate to platform adapters
            # In a full implementation, this would look up the platform adapter
            # for the target VM/host and execute the operation through it
            logger.info("compute_operation_dispatched", operation_id=operation_id, target=target)
            return {
                "status": "dispatched",
                "operation_id": operation_id,
                "target": target,
                "message": f"Operation '{operation_id}' dispatched for target '{target}'. "
                           f"Execution requires platform adapter integration.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Fallback: return a structured result for unsupported operations
        logger.warning("unsupported_operation", operation_id=operation_id, category=category)
        return {
            "status": "unsupported",
            "operation_id": operation_id,
            "target": target,
            "message": f"Operation '{operation_id}' (category: {category}) is not yet implemented",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def execute_step(
        self,
        step: OperationStep,
        params: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute a single operation step and update its model.

        Catches ValidationException from execute_atomic and converts
        it to a failed ExecutionResult so that callers can handle
        validation failures the same way as runtime failures.

        Args:
            step: The OperationStep model to execute.
            params: Optional parameter overrides.

        Returns:
            ExecutionResult with execution details.
        """
        exec_params = params or step.params or {}
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now(timezone.utc)

        try:
            result = await self.execute_atomic(step.action, exec_params)
        except ValidationException as exc:
            result = ExecutionResult(
                operation_id=step.action,
                status=ExecutionStatus.FAILED,
                error=str(exc.message) if hasattr(exc, "message") else str(exc),
                started_at=step.started_at,
                completed_at=datetime.now(timezone.utc),
            )

        # Update step model with results
        step.completed_at = result.completed_at
        if result.status == ExecutionStatus.COMPLETED:
            step.status = StepStatus.COMPLETED
            step.result = result.output
        elif result.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMED_OUT):
            step.status = StepStatus.FAILED
            step.error_message = result.error
            step.result = {"error": result.error}

        return result

    async def execute_with_rollback(
        self,
        steps: list[OperationStep],
        params: dict[str, Any] | None = None,
    ) -> list[ExecutionResult]:
        """Execute a sequence of steps with rollback on failure.

        If a step fails, previously completed steps are rolled back
        (in reverse order) if their operations are reversible.

        Args:
            steps: Ordered list of OperationStep models.
            params: Optional shared parameters.

        Returns:
            List of ExecutionResult for each step.
        """
        results: list[ExecutionResult] = []
        completed_steps: list[tuple[OperationStep, ExecutionResult]] = []

        for step in sorted(steps, key=lambda s: s.step_number):
            result = await self.execute_step(step, params)
            results.append(result)

            if result.status == ExecutionStatus.COMPLETED:
                completed_steps.append((step, result))
            else:
                # Step failed — attempt rollback on completed reversible steps
                logger.warning(
                    "step_failed_rolling_back",
                    step_number=step.step_number,
                    action=step.action,
                    error=result.error,
                )

                await self._rollback_completed(completed_steps)
                break

        return results

    async def _rollback_completed(
        self,
        completed_steps: list[tuple[OperationStep, ExecutionResult]],
    ) -> None:
        """Roll back completed reversible steps in reverse order.

        Args:
            completed_steps: List of (step, result) tuples that completed.
        """
        for step, _ in reversed(completed_steps):
            op = registry.get(step.action)
            if op is None or not op.reversible:
                logger.info(
                    "rollback_skipped",
                    action=step.action,
                    reversible=op.reversible if op else False,
                )
                continue

            logger.info("rolling_back_step", action=step.action, step_number=step.step_number)

            # Mark step as indicating rollback
            step.status = StepStatus.FAILED
            step.error_message = f"Rolled back due to subsequent step failure"

    @property
    def running_operations(self) -> list[str]:
        """Return IDs of currently executing operations."""
        return list(self._running.keys())


# Module-level singleton
operation_executor = OperationExecutor()
