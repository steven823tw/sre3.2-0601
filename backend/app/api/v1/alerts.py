"""Alert API endpoints.

Provides alert listing, acknowledgment, and resolution.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies import AlertServiceDep, CurrentUser
from app.models.alert import AlertSeverity, AlertStatus
from app.schemas.alert import (
    AlertAcknowledgeRequest,
    AlertListResponse,
    AlertResolveRequest,
    AlertResponse,
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List alerts",
    description="List alerts with optional filtering by severity, status, and asset.",
)
async def list_alerts(
    service: AlertServiceDep,
    user: CurrentUser,
    severity: AlertSeverity | None = Query(None, description="Filter by severity"),
    status: AlertStatus | None = Query(None, description="Filter by status"),
    asset_id: int | None = Query(None, description="Filter by asset ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> AlertListResponse:
    items, total = await service.list_alerts(
        severity=severity,
        status=status,
        asset_id=asset_id,
        page=page,
        limit=limit,
    )
    pages = (total + limit - 1) // limit if total > 0 else 0
    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert",
    description="Fetch a single alert by its ID.",
)
async def get_alert(
    alert_id: int,
    service: AlertServiceDep,
    user: CurrentUser,
) -> AlertResponse:
    alert = await service.get_alert(alert_id)
    return AlertResponse.model_validate(alert)


@router.put(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge alert",
    description="Acknowledge an active alert.",
)
async def acknowledge_alert(
    alert_id: int,
    data: AlertAcknowledgeRequest,
    service: AlertServiceDep,
    user: CurrentUser,
) -> AlertResponse:
    alert = await service.acknowledge_alert(alert_id, user, data.notes)
    return AlertResponse.model_validate(alert)


@router.put(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Resolve alert",
    description="Resolve an alert with resolution notes.",
)
async def resolve_alert(
    alert_id: int,
    data: AlertResolveRequest,
    service: AlertServiceDep,
    user: CurrentUser,
) -> AlertResponse:
    alert = await service.resolve_alert(alert_id, user, data.resolution_notes)
    return AlertResponse.model_validate(alert)
