"""Operation repository — extends BaseRepository with operation-specific queries."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation import Operation, OperationStatus
from app.repositories.base import BaseRepository


class OperationRepository(BaseRepository[Operation]):
    """Async repository for Operation CRUD and workflow queries."""

    model = Operation

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def filter_operations(
        self,
        *,
        status: OperationStatus | None = None,
        asset_id: int | None = None,
        created_by: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Operation], int]:
        """Filter operations with optional criteria.

        Returns:
            Tuple of (matching operations, total count).
        """
        stmt = select(Operation)
        count_stmt = select(func.count()).select_from(Operation)

        if status is not None:
            stmt = stmt.where(Operation.status == status)
            count_stmt = count_stmt.where(Operation.status == status)
        if asset_id is not None:
            stmt = stmt.where(Operation.asset_id == asset_id)
            count_stmt = count_stmt.where(Operation.asset_id == asset_id)
        if created_by is not None:
            stmt = stmt.where(Operation.created_by == created_by)
            count_stmt = count_stmt.where(Operation.created_by == created_by)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Operation.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all(), total

    async def count_pending(self) -> int:
        """Count operations awaiting approval."""
        stmt = (
            select(func.count())
            .select_from(Operation)
            .where(Operation.status == OperationStatus.PENDING)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def recent(self, limit: int = 5) -> Sequence[Operation]:
        """Return the most recent operations."""
        stmt = select(Operation).order_by(Operation.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()
