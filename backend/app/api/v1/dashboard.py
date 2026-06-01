"""Dashboard API endpoints.

Provides aggregated summary and trend data for the dashboard view.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from app.dependencies import CurrentUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dashboard import DashboardSummary, DashboardTrends
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def _get_dashboard_service(
    db: AsyncSession = Depends(get_db),
) -> DashboardService:
    return DashboardService(db)


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Dashboard summary",
    description=(
        "Returns aggregated counts for assets, alerts, and recent operations. "
        "Used to populate the main dashboard view."
    ),
)
async def get_summary(
    user: CurrentUser,
    service: DashboardService = Depends(_get_dashboard_service),
) -> DashboardSummary:
    """Build and return the dashboard summary."""
    return await service.get_summary()


@router.get(
    "/trends",
    response_model=DashboardTrends,
    summary="Dashboard trends",
    description="Returns CPU, memory, and alert trend data for the specified number of days.",
)
async def get_trends(
    user: CurrentUser,
    days: int = Query(7, ge=1, le=90, description="Number of days of trend data"),
    service: DashboardService = Depends(_get_dashboard_service),
) -> DashboardTrends:
    """Build and return trend data."""
    return await service.get_trends(days=days)
