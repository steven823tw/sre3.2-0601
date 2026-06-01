"""Atomic operation registry API.

Exposes the registry of all 109 atomic operations for the frontend
operation palette and documentation.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.registry import OpCategory
from app.dependencies import CurrentUser, RegistryDep

router = APIRouter(prefix="/atomics", tags=["Atomic Operations"])


class AtomicOperationResponse(BaseModel):
    """Response for a single atomic operation."""
    id: str
    name: str
    category: str
    description: str
    risk_level: str
    estimated_time_ms: int
    params_schema: dict[str, Any]
    requires_approval: bool
    reversible: bool


class AtomicOperationListResponse(BaseModel):
    """List of atomic operations."""
    items: list[AtomicOperationResponse]
    total: int
    categories: list[str]


@router.get(
    "",
    response_model=AtomicOperationListResponse,
    summary="List atomic operations",
    description="List all registered atomic operations with optional category filter.",
)
async def list_atomics(
    user: CurrentUser,
    registry: RegistryDep,
    category: OpCategory | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search by name or description"),
) -> AtomicOperationListResponse:
    """Return all registered atomic operations."""
    if search:
        ops = registry.search(search)
    elif category:
        ops = registry.by_category(category)
    else:
        ops = registry.list_all()

    return AtomicOperationListResponse(
        items=[
            AtomicOperationResponse(
                id=op.id,
                name=op.name,
                category=op.category.value,
                description=op.description,
                risk_level=op.risk_level.value,
                estimated_time_ms=op.estimated_time_ms,
                params_schema=op.params_schema,
                requires_approval=op.requires_approval,
                reversible=op.reversible,
            )
            for op in ops
        ],
        total=len(ops),
        categories=[c.value for c in OpCategory],
    )


@router.get(
    "/{operation_id}",
    response_model=AtomicOperationResponse,
    summary="Get atomic operation",
    description="Fetch a single atomic operation by its dot-notation ID.",
)
async def get_atomic(operation_id: str, user: CurrentUser, registry: RegistryDep) -> AtomicOperationResponse:
    """Return a single atomic operation by ID."""
    op = registry.get(operation_id)
    if op is None:
        from app.exceptions import NotFoundException
        raise NotFoundException("AtomicOperation", operation_id)
    return AtomicOperationResponse(
        id=op.id,
        name=op.name,
        category=op.category.value,
        description=op.description,
        risk_level=op.risk_level.value,
        estimated_time_ms=op.estimated_time_ms,
        params_schema=op.params_schema,
        requires_approval=op.requires_approval,
        reversible=op.reversible,
    )
