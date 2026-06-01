"""Operation API endpoints.

Provides operation CRUD and workflow management (approve/reject).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, OperationServiceDep
from app.models.operation import OperationStatus
from app.schemas.operation import (
    OperationApproveRequest,
    OperationCreateRequest,
    OperationListResponse,
    OperationRejectRequest,
    OperationResponse,
)

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get(
    "",
    response_model=OperationListResponse,
    summary="List operations",
    description="List operations with optional filtering by status and asset.",
)
async def list_operations(
    service: OperationServiceDep,
    user: CurrentUser,
    status: OperationStatus | None = Query(None, description="Filter by status"),
    asset_id: int | None = Query(None, description="Filter by asset ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> OperationListResponse:
    items, total = await service.list_operations(
        status=status,
        asset_id=asset_id,
        page=page,
        limit=limit,
    )
    pages = (total + limit - 1) // limit if total > 0 else 0
    return OperationListResponse(
        items=[OperationResponse.model_validate(o) for o in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/{operation_id}",
    response_model=OperationResponse,
    summary="Get operation",
    description="Fetch a single operation by its ID with all steps.",
)
async def get_operation(
    operation_id: int,
    service: OperationServiceDep,
    user: CurrentUser,
) -> OperationResponse:
    operation = await service.get_operation(operation_id)
    return OperationResponse.model_validate(operation)


@router.post(
    "",
    response_model=OperationResponse,
    status_code=201,
    summary="Create operation",
    description="Create a new operation with optional steps.",
)
async def create_operation(
    data: OperationCreateRequest,
    service: OperationServiceDep,
    user: CurrentUser,
) -> OperationResponse:
    operation = await service.create_operation(data, user)
    return OperationResponse.model_validate(operation)


@router.put(
    "/{operation_id}/approve",
    response_model=OperationResponse,
    summary="Approve operation",
    description="Approve a pending operation.",
)
async def approve_operation(
    operation_id: int,
    data: OperationApproveRequest,
    service: OperationServiceDep,
    user: CurrentUser,
) -> OperationResponse:
    operation = await service.approve_operation(operation_id, user)
    return OperationResponse.model_validate(operation)


@router.put(
    "/{operation_id}/reject",
    response_model=OperationResponse,
    summary="Reject operation",
    description="Reject a pending operation with a reason.",
)
async def reject_operation(
    operation_id: int,
    data: OperationRejectRequest,
    service: OperationServiceDep,
    user: CurrentUser,
) -> OperationResponse:
    operation = await service.reject_operation(operation_id, user, data.reason)
    return OperationResponse.model_validate(operation)
