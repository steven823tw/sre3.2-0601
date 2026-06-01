"""Tests for OperationRepository — count_pending and recent."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation import Operation, OperationStatus
from app.repositories.operation_repo import OperationRepository


@pytest.mark.asyncio
async def test_count_pending(db_session: AsyncSession):
    """count_pending returns the number of operations with PENDING status."""
    for title in ["Op-1", "Op-2", "Op-3"]:
        db_session.add(Operation(title=title, status=OperationStatus.PENDING))
    await db_session.flush()

    repo = OperationRepository(db_session)
    assert await repo.count_pending() == 3


@pytest.mark.asyncio
async def test_count_pending_none(db_session: AsyncSession):
    """count_pending returns 0 when there are no operations."""
    repo = OperationRepository(db_session)
    assert await repo.count_pending() == 0


@pytest.mark.asyncio
async def test_count_pending_excludes_non_pending(db_session: AsyncSession):
    """count_pending excludes operations that are not PENDING."""
    ops = [
        Operation(title="Pending op", status=OperationStatus.PENDING),
        Operation(title="Approved op", status=OperationStatus.APPROVED),
        Operation(title="Completed op", status=OperationStatus.COMPLETED),
        Operation(title="Failed op", status=OperationStatus.FAILED),
    ]
    for op in ops:
        db_session.add(op)
    await db_session.flush()

    repo = OperationRepository(db_session)
    assert await repo.count_pending() == 1


@pytest.mark.asyncio
async def test_recent_returns_operations(db_session: AsyncSession):
    """recent returns the most recent operations ordered by created_at desc."""
    for i in range(5):
        db_session.add(Operation(title=f"Op-{i}", status=OperationStatus.PENDING))
    await db_session.flush()

    repo = OperationRepository(db_session)
    recent = await repo.recent()
    assert len(recent) == 5
    # Should be ordered by created_at desc (newest first)
    for i in range(len(recent) - 1):
        assert recent[i].created_at >= recent[i + 1].created_at


@pytest.mark.asyncio
async def test_recent_with_limit(db_session: AsyncSession):
    """recent respects the limit parameter."""
    for i in range(5):
        db_session.add(Operation(title=f"Op-{i}", status=OperationStatus.PENDING))
    await db_session.flush()

    repo = OperationRepository(db_session)
    recent = await repo.recent(limit=2)
    assert len(recent) == 2


@pytest.mark.asyncio
async def test_recent_empty(db_session: AsyncSession):
    """recent returns empty list when no operations exist."""
    repo = OperationRepository(db_session)
    recent = await repo.recent()
    assert recent == []
