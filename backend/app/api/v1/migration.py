"""Migration API endpoints.

Provides migration planning, execution, status, and rollback.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUser
from pydantic import BaseModel, Field

from app.migration.engine import (
    MigrationEngine, MigrationMethod, MigrationPlan,
    MigrationStatus, MigrationStatusInfo, MigrationStep,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/migration", tags=["migration"])
engine = MigrationEngine()


class MigrationPlanRequest(BaseModel):
    """Request body for generating a migration plan."""
    vm_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class MigrationStepResponse(BaseModel):
    """Response model for a migration step."""
    order: int
    action: str
    description: str
    command: str = ""
    status: str = "pending"
    error: str | None = None


class MigrationPlanResponse(BaseModel):
    """Response model for a migration plan."""
    plan_id: str
    vm_id: str
    source_platform: str
    target_platform: str
    method: str
    steps: list[MigrationStepResponse]
    status: str


class MigrationStatusResponse(BaseModel):
    """Response model for migration status."""
    plan_id: str
    status: str
    current_step: int
    total_steps: int
    progress_pct: float
    error: str | None = None


class MigrationActionResponse(BaseModel):
    """Response model for migration actions (execute/rollback)."""
    success: bool
    message: str


def _plan_to_response(plan: MigrationPlan) -> MigrationPlanResponse:
    """Convert a MigrationPlan to a response model."""
    return MigrationPlanResponse(
        plan_id=plan.plan_id,
        vm_id=plan.vm_id,
        source_platform=plan.source_platform,
        target_platform=plan.target_platform,
        method=plan.method.value,
        steps=[
            MigrationStepResponse(
                order=s.order, action=s.action, description=s.description,
                command=s.command, status=s.status, error=s.error,
            )
            for s in plan.steps
        ],
        status=plan.status.value,
    )


def _status_to_response(info: MigrationStatusInfo) -> MigrationStatusResponse:
    """Convert a MigrationStatusInfo to a response model."""
    return MigrationStatusResponse(
        plan_id=info.plan_id,
        status=info.status.value,
        current_step=info.current_step,
        total_steps=info.total_steps,
        progress_pct=info.progress_pct,
        error=info.error,
    )


@router.post("/plan", response_model=MigrationPlanResponse)
async def create_plan(req: MigrationPlanRequest, user: CurrentUser) -> MigrationPlanResponse:
    """Generate a migration plan for a VM."""
    try:
        plan = await engine.plan_migration(req.vm_id, req.source, req.target)
        return _plan_to_response(plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/execute", response_model=MigrationActionResponse)
async def execute_migration(plan_id: str, user: CurrentUser) -> MigrationActionResponse:
    """Execute a migration plan."""
    try:
        success = await engine.execute_migration(plan_id)
        return MigrationActionResponse(
            success=success,
            message="Migration completed" if success else "Migration failed",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{plan_id}", response_model=MigrationStatusResponse)
async def get_status(plan_id: str, user: CurrentUser) -> MigrationStatusResponse:
    """Get the status of a migration plan."""
    try:
        info = await engine.get_migration_status(plan_id)
        return _status_to_response(info)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{plan_id}/rollback", response_model=MigrationActionResponse)
async def rollback_migration(plan_id: str, user: CurrentUser) -> MigrationActionResponse:
    """Rollback a migration plan."""
    try:
        success = await engine.rollback_migration(plan_id)
        return MigrationActionResponse(
            success=success,
            message="Rollback completed" if success else "Rollback failed",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
