"""Alert repository — extends BaseRepository with alert-specific queries."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Async repository for Alert CRUD and filtering."""

    model = Alert

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def filter_alerts(
        self,
        *,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        asset_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Alert], int]:
        """Filter alerts with optional criteria.

        Returns:
            Tuple of (matching alerts, total count).
        """
        stmt = select(Alert)
        count_stmt = select(func.count()).select_from(Alert)

        if severity is not None:
            stmt = stmt.where(Alert.severity == severity)
            count_stmt = count_stmt.where(Alert.severity == severity)
        if status is not None:
            stmt = stmt.where(Alert.status == status)
            count_stmt = count_stmt.where(Alert.status == status)
        if asset_id is not None:
            stmt = stmt.where(Alert.asset_id == asset_id)
            count_stmt = count_stmt.where(Alert.asset_id == asset_id)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all(), total

    async def count_active(self) -> int:
        """Count alerts with status 'active'."""
        stmt = select(func.count()).select_from(Alert).where(Alert.status == AlertStatus.ACTIVE)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_severity(self) -> list[dict]:
        """Return active alert counts grouped by severity."""
        stmt = (
            select(Alert.severity, func.count().label("count"))
            .where(Alert.status == AlertStatus.ACTIVE)
            .group_by(Alert.severity)
        )
        result = await self._session.execute(stmt)
        return [{"severity": row[0].value, "count": row[1]} for row in result.all()]
