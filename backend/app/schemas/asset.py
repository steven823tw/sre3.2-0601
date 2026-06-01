"""Pydantic schemas for Asset API request/response validation.

Uses Pydantic v2 with model_validator and ConfigDict.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import AssetStatus, AssetType, Platform


class AssetBase(BaseModel):
    """Shared asset fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Asset display name")
    asset_type: AssetType = Field(..., description="Type of asset")
    platform: Platform = Field(..., description="Infrastructure platform")
    status: AssetStatus = Field(default=AssetStatus.UNKNOWN, description="Current status")
    ip_address: str | None = Field(None, max_length=45, description="IP address")
    hostname: str | None = Field(None, max_length=255, description="Hostname")
    location: str | None = Field(None, max_length=255, description="Physical location")
    environment: str | None = Field(None, max_length=50, description="Environment (prod/staging/dev)")
    description: str | None = Field(None, description="Asset description")
    tags: dict[str, Any] | None = Field(None, description="Key-value tags")


class AssetCreate(AssetBase):
    """Request body for creating an asset."""
    pass


class AssetUpdate(BaseModel):
    """Request body for partial asset update (PATCH)."""
    name: str | None = Field(None, min_length=1, max_length=255)
    asset_type: AssetType | None = None
    platform: Platform | None = None
    status: AssetStatus | None = None
    ip_address: str | None = None
    hostname: str | None = None
    location: str | None = None
    environment: str | None = None
    description: str | None = None
    tags: dict[str, Any] | None = None


class AssetResponse(AssetBase):
    """Response body for a single asset."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AssetListResponse(BaseModel):
    """Paginated list of assets."""
    items: list[AssetResponse]
    total: int
    page: int
    limit: int
    pages: int


class AssetActionRequest(BaseModel):
    """Request to execute a quick action on an asset."""
    action: str = Field(..., description="Action name (boot/shutdown/restart)")
    confirm: bool = Field(False, description="Confirmation flag for destructive actions")


class AssetActionResponse(BaseModel):
    """Response after executing an asset action."""
    success: bool
    action: str
    message: str
    operation_id: int | None = None
