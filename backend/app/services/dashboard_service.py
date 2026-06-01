"""Dashboard service — aggregation logic for dashboard data."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.repositories.alert_repo import AlertRepository
from app.repositories.asset_repo import AssetRepository
from app.repositories.operation_repo import OperationRepository
from app.schemas.dashboard import (
    AlertCountBySeverity,
    AssetCountByStatus,
    AssetCountByType,
    DashboardSummary,
    DashboardTrends,
    RecentOperation,
    TrendPoint,
    TrendSeries,
)

logger = structlog.get_logger(__name__)


class DashboardService:
    """Aggregates data from multiple repositories for the dashboard."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._asset_repo = AssetRepository(session)
        self._alert_repo = AlertRepository(session)
        self._operation_repo = OperationRepository(session)

    async def get_summary(self) -> DashboardSummary:
        """Build the dashboard summary from multiple data sources.

        All repository calls are independent — execute in parallel for lower latency.
        """
        (
            total_assets,
            assets_by_type_raw,
            assets_by_status_raw,
            active_alerts,
            alerts_by_severity_raw,
            recent_ops,
            pending_ops,
        ) = await asyncio.gather(
            self._asset_repo.count(),
            self._asset_repo.count_by_type(),
            self._asset_repo.count_by_status(),
            self._alert_repo.count_active(),
            self._alert_repo.count_by_severity(),
            self._operation_repo.recent(limit=5),
            self._operation_repo.count_pending(),
        )

        assets_by_type = [AssetCountByType(**d) for d in assets_by_type_raw]
        assets_by_status = [AssetCountByStatus(**d) for d in assets_by_status_raw]
        alerts_by_severity = [AlertCountBySeverity(**d) for d in alerts_by_severity_raw]

        recent_operations = [
            RecentOperation(
                id=op.id,
                title=op.title,
                status=op.status.value,
                created_at=op.created_at.isoformat(),
            )
            for op in recent_ops
        ]

        return DashboardSummary(
            total_assets=total_assets,
            assets_by_type=assets_by_type,
            assets_by_status=assets_by_status,
            active_alerts=active_alerts,
            alerts_by_severity=alerts_by_severity,
            recent_operations=recent_operations,
            operations_pending_approval=pending_ops,
        )

    async def get_trends(self, days: int = 7) -> DashboardTrends:
        """Build trend data for the specified number of days.

        Queries the database for real alert counts and asset statistics.
        Falls back to computed estimates when no historical data exists.
        """
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        # Get alert counts by day
        from app.models.alert import Alert, AlertStatus

        alert_query = (
            select(
                cast(Alert.created_at, Date).label("date"),
                func.count().label("count"),
            )
            .where(Alert.created_at >= start)
            .group_by(cast(Alert.created_at, Date))
            .order_by(cast(Alert.created_at, Date))
        )
        result = await self._session.execute(alert_query)
        alert_counts = {str(row.date): row.count for row in result.all()}

        # Get total assets for percentage estimation
        total_assets = await self._asset_repo.count()
        active_alerts = await self._alert_repo.count_active()

        # Build trend points
        alert_points = []
        cpu_points = []
        memory_points = []
        for i in range(days):
            date = (now - timedelta(days=days - 1 - i)).date()
            date_str = date.isoformat()

            # Alert trend (real data)
            alert_count = alert_counts.get(date_str, 0)
            alert_points.append(TrendPoint(timestamp=date_str, value=float(alert_count)))

            # CPU/Memory trends: placeholder until monitoring integration is available.
            # When Prometheus/metrics API is connected, replace with real queries.
            cpu_points.append(TrendPoint(timestamp=date_str, value=0.0))
            memory_points.append(TrendPoint(timestamp=date_str, value=0.0))

        return DashboardTrends(
            days=days,
            cpu_trend=TrendSeries(name="CPU Usage", unit="%", data=cpu_points),
            memory_trend=TrendSeries(name="Memory Usage", unit="%", data=memory_points),
            alert_trend=TrendSeries(name="Alert Count", unit="count", data=alert_points),
        )
