"""Asset repository — extends BaseRepository with asset-specific queries."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetStatus, AssetType, Platform
from app.repositories.base import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    """Async repository for Asset CRUD and search."""

    model = Asset

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        asset_type: AssetType | None = None,
        platform: Platform | None = None,
        status: AssetStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Asset], int]:
        """Search assets with optional filters.

        Returns:
            Tuple of (matching assets, total count).
        """
        stmt = select(Asset)
        count_stmt = select(func.count()).select_from(Asset)

        if asset_type is not None:
            stmt = stmt.where(Asset.asset_type == asset_type)
            count_stmt = count_stmt.where(Asset.asset_type == asset_type)
        if platform is not None:
            stmt = stmt.where(Asset.platform == platform)
            count_stmt = count_stmt.where(Asset.platform == platform)
        if status is not None:
            stmt = stmt.where(Asset.status == status)
            count_stmt = count_stmt.where(Asset.status == status)
        if search:
            # Escape SQL LIKE wildcards to prevent injection
            def _escape_like(s: str) -> str:
                return s.replace(chr(92), chr(92)*2).replace('%', chr(92)+'%').replace('_', chr(92)+'_')
            pattern = f'%{_escape_like(search)}%'
            search_filter = Asset.name.ilike(pattern, escape="\\") | Asset.hostname.ilike(pattern, escape="\\")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        # Count total
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Fetch page
        stmt = stmt.order_by(Asset.id.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all(), total

    async def count_by_type(self) -> list[dict]:
        """Return asset counts grouped by type."""
        stmt = (
            select(Asset.asset_type, func.count().label("count"))
            .group_by(Asset.asset_type)
        )
        result = await self._session.execute(stmt)
        return [{"asset_type": row[0].value, "count": row[1]} for row in result.all()]

    async def count_by_status(self) -> list[dict]:
        """Return asset counts grouped by status."""
        stmt = (
            select(Asset.status, func.count().label("count"))
            .group_by(Asset.status)
        )
        result = await self._session.execute(stmt)
        return [{"status": row[0].value, "count": row[1]} for row in result.all()]
