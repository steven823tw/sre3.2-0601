"""Pydantic schemas for Alert API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertSeverity, AlertStatus


class AlertResponse(BaseModel):
    """Response body for a single alert."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    severity: AlertSeverity
    status: AlertStatus
    source: str | None
    asset_id: int | None
    metric_name: str | None
    metric_value: str | None
    threshold: str | None
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    resolved_by: str | None
    resolved_at: datetime | None
    resolution_notes: str | None
    created_at: datetime
    updated_at: datetime


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""
    items: list[AlertResponse]
    total: int
    page: int
    limit: int
    pages: int


class AlertAcknowledgeRequest(BaseModel):
    """Request to acknowledge an alert."""
    notes: str | None = Field(None, description="Optional acknowledgment notes")


class AlertResolveRequest(BaseModel):
    """Request to resolve an alert."""
    resolution_notes: str = Field(
        ..., min_length=1, description="Resolution notes (required)"
    )
