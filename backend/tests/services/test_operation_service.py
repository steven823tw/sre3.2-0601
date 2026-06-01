"""Tests for OperationService workflow logic."""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictException, NotFoundException
from app.models.operation import Operation, OperationStatus
from app.repositories.operation_repo import OperationRepository
from app.schemas.operation import OperationCreateRequest, OperationStepCreate
from app.services.operation_service import OperationService


@pytest.mark.asyncio
async def test_create_operation(db_session: AsyncSession):
    """Creating an operation persists it with PENDING status."""
    service = OperationService(db_session)
    data = OperationCreateRequest(
        title="Test operation",
        description="A test operation",
        intent="diagnose",
    )
    operation = await service.create_operation(data, user="test-user")
    assert operation.id is not None
    assert operation.status == OperationStatus.PENDING
    assert operation.created_by == "test-user"


@pytest.mark.asyncio
async def test_create_operation_with_steps(db_session: AsyncSession):
    """Creating an operation with steps persists all steps."""
    service = OperationService(db_session)
    data = OperationCreateRequest(
        title="Multi-step operation",
        steps=[
            OperationStepCreate(
                step_number=1,
                action="infra.ping",
                description="Ping target",
                risk_level="low",
                estimated_time_ms=5000,
            ),
            OperationStepCreate(
                step_number=2,
                action="compute.vm_status",
                description="Check VM",
                risk_level="low",
                estimated_time_ms=10000,
            ),
        ],
    )
    operation = await service.create_operation(data, user="test-user")
    assert len(operation.steps) == 2


@pytest.mark.asyncio
async def test_approve_operation(db_session: AsyncSession):
    """Approving a pending operation changes status to APPROVED."""
    service = OperationService(db_session)
    data = OperationCreateRequest(title="To be approved")
    operation = await service.create_operation(data, user="test-user")

    approved = await service.approve_operation(operation.id, user="admin")
    assert approved.status == OperationStatus.APPROVED
    assert approved.approved_by == "admin"


@pytest.mark.asyncio
async def test_reject_operation(db_session: AsyncSession):
    """Rejecting a pending operation changes status to REJECTED."""
    service = OperationService(db_session)
    data = OperationCreateRequest(title="To be rejected")
    operation = await service.create_operation(data, user="test-user")

    rejected = await service.reject_operation(operation.id, user="admin", reason="Not needed")
    assert rejected.status == OperationStatus.REJECTED
    assert "Not needed" in rejected.result_summary


@pytest.mark.asyncio
async def test_approve_non_pending_raises(db_session: AsyncSession):
    """Approving a non-pending operation raises ConflictException."""
    service = OperationService(db_session)
    data = OperationCreateRequest(title="Already approved")
    operation = await service.create_operation(data, user="test-user")

    await service.approve_operation(operation.id, user="admin")

    with pytest.raises(ConflictException):
        await service.approve_operation(operation.id, user="admin")


@pytest.mark.asyncio
async def test_get_nonexistent_operation_raises(db_session: AsyncSession):
    """Getting a non-existent operation raises NotFoundException."""
    service = OperationService(db_session)
    with pytest.raises(NotFoundException):
        await service.get_operation(99999)


@pytest.mark.asyncio
async def test_count_pending(db_session: AsyncSession):
    """Counting pending operations returns correct count."""
    service = OperationService(db_session)

    assert await service.count_pending() == 0

    await service.create_operation(OperationCreateRequest(title="Op 1"), user="u1")
    await service.create_operation(OperationCreateRequest(title="Op 2"), user="u1")

    assert await service.count_pending() == 2


@pytest.mark.asyncio
async def test_list_operations_by_status(db_session: AsyncSession):
    """Listing operations by status returns only matching operations."""
    service = OperationService(db_session)

    op1 = await service.create_operation(OperationCreateRequest(title="Pending"), user="u1")
    op2 = await service.create_operation(OperationCreateRequest(title="Also pending"), user="u1")
    await service.approve_operation(op2.id, user="admin")

    pending, total = await service.list_operations(status=OperationStatus.PENDING)
    assert total == 1
    assert pending[0].id == op1.id
