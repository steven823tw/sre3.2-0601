"""Pydantic schemas for Operation API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.operation import OperationStatus, StepStatus


class OperationStepCreate(BaseModel):
    """Data for creating a step within an operation."""
    step_number: int = Field(..., ge=1)
    action: str = Field(..., min_length=1)
    description: str | None = None
    risk_level: str | None = None
    params: dict[str, Any] | None = None
    estimated_time_ms: int | None = None


class OperationStepResponse(BaseModel):
    """Response for a single operation step."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_number: int
    action: str
    description: str | None
    status: StepStatus
    risk_level: str | None
    params: dict[str, Any] | None
    result: dict[str, Any] | None
    error_message: str | None
    estimated_time_ms: int | None
    started_at: datetime | None
    completed_at: datetime | None


class OperationResponse(BaseModel):
    """Response for a single operation."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: OperationStatus
    intent: str | None
    asset_id: int | None
    created_by: str | None
    approved_by: str | None
    approved_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    result_summary: str | None
    params: dict[str, Any] | None
    steps: list[OperationStepResponse]
    created_at: datetime
    updated_at: datetime


class OperationCreateRequest(BaseModel):
    """Request to create a new operation."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    intent: str | None = None
    asset_id: int | None = None
    steps: list[OperationStepCreate] | None = None
    params: dict[str, Any] | None = None


class OperationListResponse(BaseModel):
    """Paginated list of operations."""
    items: list[OperationResponse]
    total: int
    page: int
    limit: int
    pages: int


class OperationApproveRequest(BaseModel):
    """Request to approve an operation."""
    notes: str | None = None


class OperationRejectRequest(BaseModel):
    """Request to reject an operation."""
    reason: str = Field(..., min_length=1, description="Rejection reason")
