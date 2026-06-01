"""Platform repository — extends BaseRepository with platform-specific queries."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import PlatformConnection, PlatformType
from app.repositories.base import BaseRepository


class PlatformRepository(BaseRepository[PlatformConnection]):
    """Async repository for PlatformConnection CRUD."""

    model = PlatformConnection

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, id_: int) -> PlatformConnection | None:
        """Fetch a platform connection by primary key."""
        return await self._session.get(PlatformConnection, id_)

    async def list_by_type(
        self,
        platform_type: PlatformType | None = None,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[PlatformConnection]:
        """List platform connections, optionally filtered by type."""
        stmt = select(PlatformConnection)
        if platform_type is not None:
            stmt = stmt.where(PlatformConnection.platform_type == platform_type)
        stmt = stmt.order_by(PlatformConnection.id.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_connected(self, platform_id: int, connected: bool) -> None:
        """Update the connected status of a platform."""
        obj = await self.get_by_id(platform_id)
        if obj is not None:
            obj.connected = connected
            await self._session.flush()
