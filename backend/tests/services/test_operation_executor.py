"""Tests for OperationExecutor — atomic execution and rollback.

Covers:
- Parameter validation
- Execution lifecycle (pending -> running -> completed/failed)
- Timeout handling
- Step execution
- Rollback on failure
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio

from app.core.registry import registry
from app.exceptions import ValidationException
from app.models.operation import OperationStep, StepStatus
from app.services.operation_executor import (
    ExecutionResult,
    ExecutionStatus,
    OperationExecutor,
    operation_executor,
)


class TestOperationExecutorValidation:
    """Test parameter validation."""

    def test_validate_valid_params(self):
        """Valid parameters should not raise."""
        executor = OperationExecutor()
        # Should not raise
        executor.validate_params("infra.ping", {"target": "web-01"})

    def test_validate_missing_params(self):
        """Missing required parameters should raise ValidationException."""
        executor = OperationExecutor()
        with pytest.raises(ValidationException) as exc_info:
            executor.validate_params("infra.ping", {})
        assert "Missing required parameters" in str(exc_info.value)
        assert "target" in str(exc_info.value.details["missing"])

    def test_validate_unknown_operation(self):
        """Unknown operation ID should raise ValidationException."""
        executor = OperationExecutor()
        with pytest.raises(ValidationException) as exc_info:
            executor.validate_params("nonexistent.op", {})
        assert "Unknown operation" in str(exc_info.value)

    def test_validate_none_value(self):
        """None values for required params should raise ValidationException."""
        executor = OperationExecutor()
        with pytest.raises(ValidationException):
            executor.validate_params("infra.ping", {"target": None})


class TestOperationExecutorTimeout:
    """Test timeout configuration."""

    def test_default_timeout_low_risk(self):
        """Low-risk operations should use the low timeout."""
        executor = OperationExecutor()
        timeout = executor.get_timeout("infra.ping")
        assert timeout == 30_000

    def test_default_timeout_high_risk(self):
        """High-risk operations should use the high timeout."""
        executor = OperationExecutor()
        timeout = executor.get_timeout("compute.vm_stop")
        assert timeout == 120_000

    def test_default_timeout_critical_risk(self):
        """Critical-risk operations should use the critical timeout."""
        executor = OperationExecutor()
        timeout = executor.get_timeout("storage.expand_volume")
        assert timeout == 300_000

    def test_timeout_override(self):
        """Timeout overrides should take precedence."""
        executor = OperationExecutor(timeout_overrides={"infra.ping": 5_000})
        timeout = executor.get_timeout("infra.ping")
        assert timeout == 5_000

    def test_timeout_unknown_operation(self):
        """Unknown operations should fall back to low timeout."""
        executor = OperationExecutor()
        timeout = executor.get_timeout("nonexistent.op")
        assert timeout == 30_000


class TestOperationExecutorExecution:
    """Test execution lifecycle."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Successful execution should return COMPLETED status."""
        executor = OperationExecutor()
        result = await executor.execute_atomic(
            "infra.ping", {"target": "web-01"}
        )
        assert result.status == ExecutionStatus.COMPLETED
        assert result.operation_id == "infra.ping"
        assert result.output["status"] == "success"
        assert result.duration_ms >= 0
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_invalid_params_raises(self):
        """Invalid parameters should raise ValidationException."""
        executor = OperationExecutor()
        with pytest.raises(ValidationException):
            await executor.execute_atomic("infra.ping", {})

    @pytest.mark.asyncio
    async def test_execute_unknown_operation_raises(self):
        """Unknown operation should raise ValidationException."""
        executor = OperationExecutor()
        with pytest.raises(ValidationException):
            await executor.execute_atomic("nonexistent.op", {"target": "x"})

    @pytest.mark.asyncio
    async def test_execute_output_contains_target(self):
        """Execution output should include the target."""
        executor = OperationExecutor()
        result = await executor.execute_atomic(
            "compute.vm_status", {"vm": "db-01"}
        )
        assert result.output["target"] == "db-01"

    @pytest.mark.asyncio
    async def test_execute_running_operations_tracking(self):
        """Running operations should be tracked during execution."""
        executor = OperationExecutor()
        # After execution, running list should be empty
        result = await executor.execute_atomic(
            "infra.ping", {"target": "web-01"}
        )
        assert executor.running_operations == []


class TestOperationExecutorStep:
    """Test step-level execution."""

    @pytest.mark.asyncio
    async def test_execute_step_updates_status(self):
        """Executing a step should update its status fields."""
        executor = OperationExecutor()
        step = OperationStep(
            step_number=1,
            action="infra.ping",
            description="Ping target",
            status=StepStatus.PENDING,
            params={"target": "web-01"},
        )
        result = await executor.execute_step(step)
        assert result.status == ExecutionStatus.COMPLETED
        assert step.status == StepStatus.COMPLETED
        assert step.started_at is not None
        assert step.completed_at is not None
        assert step.result is not None

    @pytest.mark.asyncio
    async def test_execute_step_failure_marks_failed(self):
        """A failed step should be marked as FAILED."""
        executor = OperationExecutor()
        step = OperationStep(
            step_number=1,
            action="infra.ping",
            description="Ping target",
            status=StepStatus.PENDING,
            params={},  # Missing required 'target'
        )
        result = await executor.execute_step(step)
        assert result.status == ExecutionStatus.FAILED
        assert step.status == StepStatus.FAILED
        assert step.error_message is not None

    @pytest.mark.asyncio
    async def test_execute_step_with_param_overrides(self):
        """Step params can be overridden at execution time."""
        executor = OperationExecutor()
        step = OperationStep(
            step_number=1,
            action="infra.ping",
            description="Ping target",
            status=StepStatus.PENDING,
            params={"target": "original"},
        )
        result = await executor.execute_step(step, params={"target": "override"})
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output["target"] == "override"


class TestOperationExecutorRollback:
    """Test rollback on failure."""

    @pytest.mark.asyncio
    async def test_all_steps_complete(self):
        """All steps completing should not trigger rollback."""
        executor = OperationExecutor()
        steps = [
            OperationStep(
                step_number=1,
                action="infra.ping",
                description="Step 1",
                status=StepStatus.PENDING,
                params={"target": "web-01"},
            ),
            OperationStep(
                step_number=2,
                action="compute.vm_status",
                description="Step 2",
                status=StepStatus.PENDING,
                params={"vm": "web-01"},
            ),
        ]
        results = await executor.execute_with_rollback(steps)
        assert len(results) == 2
        assert all(r.status == ExecutionStatus.COMPLETED for r in results)
        assert all(s.status == StepStatus.COMPLETED for s in steps)

    @pytest.mark.asyncio
    async def test_failure_stops_execution(self):
        """A failing step should stop subsequent steps from executing."""
        executor = OperationExecutor()
        steps = [
            OperationStep(
                step_number=1,
                action="infra.ping",
                description="Step 1",
                status=StepStatus.PENDING,
                params={"target": "web-01"},
            ),
            OperationStep(
                step_number=2,
                action="infra.ping",
                description="Step 2 (bad params)",
                status=StepStatus.PENDING,
                params={},  # Missing target — will fail
            ),
            OperationStep(
                step_number=3,
                action="compute.vm_status",
                description="Step 3",
                status=StepStatus.PENDING,
                params={"vm": "web-01"},
            ),
        ]
        results = await executor.execute_with_rollback(steps)
        # Only 2 results — step 3 should not have executed
        assert len(results) == 2
        assert results[0].status == ExecutionStatus.COMPLETED
        assert results[1].status == ExecutionStatus.FAILED
        # Step 3 should still be pending
        assert steps[2].status == StepStatus.PENDING

    @pytest.mark.asyncio
    async def test_rollback_reversible_steps(self):
        """Completed reversible steps should be marked for rollback."""
        executor = OperationExecutor()
        steps = [
            OperationStep(
                step_number=1,
                action="compute.vm_snapshot",  # reversible=True
                description="Create snapshot",
                status=StepStatus.PENDING,
                params={"vm": "web-01", "name": "snap-1", "memory": False},
            ),
            OperationStep(
                step_number=2,
                action="infra.ping",
                description="Will fail",
                status=StepStatus.PENDING,
                params={},  # Missing target — will fail
            ),
        ]
        results = await executor.execute_with_rollback(steps)
        # Step 1 completed, step 2 failed
        assert results[0].status == ExecutionStatus.COMPLETED
        assert results[1].status == ExecutionStatus.FAILED
        # Step 1 should be rolled back (marked FAILED with rollback message)
        assert steps[0].status == StepStatus.FAILED
        assert "Rolled back" in steps[0].error_message

    @pytest.mark.asyncio
    async def test_no_rollback_irreversible_steps(self):
        """Non-reversible steps should not be rolled back."""
        executor = OperationExecutor()
        steps = [
            OperationStep(
                step_number=1,
                action="infra.ping",  # reversible=False
                description="Ping",
                status=StepStatus.PENDING,
                params={"target": "web-01"},
            ),
            OperationStep(
                step_number=2,
                action="infra.ping",
                description="Will fail",
                status=StepStatus.PENDING,
                params={},  # Missing target
            ),
        ]
        results = await executor.execute_with_rollback(steps)
        # Step 1 should remain COMPLETED (not reversible)
        assert steps[0].status == StepStatus.COMPLETED
        assert results[1].status == ExecutionStatus.FAILED
