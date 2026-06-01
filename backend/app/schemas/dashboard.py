"""Pydantic schemas for Dashboard API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AssetCountByType(BaseModel):
    """Asset count grouped by type."""
    asset_type: str
    count: int


class AssetCountByStatus(BaseModel):
    """Asset count grouped by status."""
    status: str
    count: int


class AlertCountBySeverity(BaseModel):
    """Alert count grouped by severity."""
    severity: str
    count: int


class RecentOperation(BaseModel):
    """Brief summary of a recent operation."""
    id: int
    title: str
    status: str
    created_at: str


class DashboardSummary(BaseModel):
    """Summary data for the dashboard."""
    total_assets: int
    assets_by_type: list[AssetCountByType]
    assets_by_status: list[AssetCountByStatus]
    active_alerts: int
    alerts_by_severity: list[AlertCountBySeverity]
    recent_operations: list[RecentOperation]
    operations_pending_approval: int


class TrendPoint(BaseModel):
    """A single data point in a trend series."""
    timestamp: str
    value: float


class TrendSeries(BaseModel):
    """A named series of trend data points."""
    name: str
    unit: str
    data: list[TrendPoint]


class DashboardTrends(BaseModel):
    """Trend data for the dashboard."""
    days: int
    cpu_trend: TrendSeries
    memory_trend: TrendSeries
    alert_trend: TrendSeries
