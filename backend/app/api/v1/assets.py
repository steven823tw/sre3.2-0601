"""Asset API endpoints.

Provides CRUD operations, search, and quick actions for infrastructure assets.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies import AssetServiceDep, CurrentUser
from app.models.asset import AssetStatus, AssetType, Platform
from app.schemas.asset import (
    AssetActionRequest,
    AssetActionResponse,
    AssetCreate,
    AssetListResponse,
    AssetResponse,
    AssetUpdate,
)

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get(
    "",
    response_model=AssetListResponse,
    summary="List assets",
    description="List assets with optional filtering by type, platform, status, and text search.",
)
async def list_assets(
    service: AssetServiceDep,
    user: CurrentUser,
    asset_type: AssetType | None = Query(None, description="Filter by asset type"),
    platform: Platform | None = Query(None, description="Filter by platform"),
    status: AssetStatus | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by name or hostname"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
) -> AssetListResponse:
    items, total = await service.list_assets(
        asset_type=asset_type,
        platform=platform,
        status=status,
        search=search,
        page=page,
        limit=limit,
    )
    pages = (total + limit - 1) // limit if total > 0 else 0
    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Get asset",
    description="Fetch a single asset by its ID.",
)
async def get_asset(
    asset_id: int,
    service: AssetServiceDep,
    user: CurrentUser,
) -> AssetResponse:
    asset = await service.get_asset(asset_id)
    return AssetResponse.model_validate(asset)


@router.post(
    "",
    response_model=AssetResponse,
    status_code=201,
    summary="Create asset",
    description="Create a new infrastructure asset.",
)
async def create_asset(
    data: AssetCreate,
    service: AssetServiceDep,
    user: CurrentUser,
) -> AssetResponse:
    asset = await service.create_asset(data)
    return AssetResponse.model_validate(asset)


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update asset",
    description="Partially update an existing asset.",
)
async def update_asset(
    asset_id: int,
    data: AssetUpdate,
    service: AssetServiceDep,
    user: CurrentUser,
) -> AssetResponse:
    asset = await service.update_asset(asset_id, data)
    return AssetResponse.model_validate(asset)


@router.delete(
    "/{asset_id}",
    status_code=204,
    summary="Delete asset",
    description="Delete an infrastructure asset.",
)
async def delete_asset(
    asset_id: int,
    service: AssetServiceDep,
    user: CurrentUser,
) -> None:
    await service.delete_asset(asset_id)


@router.post(
    "/{asset_id}/actions",
    response_model=AssetActionResponse,
    summary="Execute action",
    description="Execute a quick action (boot/shutdown/restart) on an asset.",
)
async def execute_action(
    asset_id: int,
    data: AssetActionRequest,
    service: AssetServiceDep,
    user: CurrentUser,
) -> AssetActionResponse:
    result = await service.execute_action(asset_id, data.action, data.confirm)
    return AssetActionResponse(**result)
