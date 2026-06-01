"""Platform management API endpoints.

Provides CRUD operations for platform connections and
device management (list, sync, test).

All platform configurations are persisted in the database.
Passwords are encrypted before storage.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.dependencies import CurrentUser, PlatformServiceDep
from app.models.platform import PlatformConnection, PlatformType

router = APIRouter(prefix="/platforms", tags=["platforms"])


# ── Request/Response Models ──────────────────────────────────────────────

class PlatformCreateRequest(BaseModel):
    """Request body for creating a platform connection."""
    name: str = Field(..., min_length=1, max_length=100, description="Platform display name")
    platform_type: PlatformType = Field(..., description="Hypervisor type")
    host: str = Field(..., min_length=1, description="Hostname or IP address")
    port: int = Field(default=443, ge=1, le=65535, description="API port")
    username: str = Field(default="", description="Authentication username")
    password: str = Field(default="", description="Authentication password")
    verify_ssl: bool = Field(default=True, description="Verify TLS certificates")
    extra: dict[str, Any] = Field(default_factory=dict, description="Platform-specific config")


class PlatformUpdateRequest(BaseModel):
    """Request body for updating a platform connection."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    verify_ssl: bool | None = None
    extra: dict[str, Any] | None = None


class PlatformResponse(BaseModel):
    """Response model for a platform connection."""
    id: int
    name: str
    platform_type: PlatformType
    host: str
    port: int
    username: str
    verify_ssl: bool
    connected: bool = False


class ConnectionTestResponse(BaseModel):
    """Response model for connection test."""
    success: bool
    latency_ms: int
    version: str
    details: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class DeviceResponse(BaseModel):
    """Response model for a device."""
    id: str
    name: str
    device_type: str
    status: str
    ip_address: str
    platform: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Response helper ─────────────────────────────────────────────────────

def _to_response(platform: PlatformConnection) -> PlatformResponse:
    """Convert database model to API response."""
    return PlatformResponse(
        id=platform.id,
        name=platform.name,
        platform_type=platform.platform_type,
        host=platform.host,
        port=platform.port,
        username=platform.username,
        verify_ssl=platform.verify_ssl,
        connected=platform.connected,
    )


# ── API Endpoints ────────────────────────────────────────────────────────

@router.get("/", response_model=list[PlatformResponse])
async def list_platforms(
    user: CurrentUser,
    service: PlatformServiceDep,
) -> list[PlatformResponse]:
    """List all configured platforms."""
    platforms = await service.list_platforms()
    return [_to_response(p) for p in platforms]


@router.post("/", response_model=PlatformResponse, status_code=201)
async def create_platform(
    req: PlatformCreateRequest,
    user: CurrentUser,
    service: PlatformServiceDep,
) -> PlatformResponse:
    """Add a new platform connection."""
    platform = await service.create_platform(
        name=req.name,
        platform_type=req.platform_type,
        host=req.host,
        port=req.port,
        username=req.username,
        password=req.password,
        verify_ssl=req.verify_ssl,
        extra=req.extra,
    )
    return _to_response(platform)


@router.get("/{platform_id}", response_model=PlatformResponse)
async def get_platform(
    platform_id: int,
    user: CurrentUser,
    service: PlatformServiceDep,
) -> PlatformResponse:
    """Get a platform by ID."""
    platform = await service.get_platform(platform_id)
    return _to_response(platform)


@router.put("/{platform_id}", response_model=PlatformResponse)
async def update_platform(
    platform_id: int,
    req: PlatformUpdateRequest,
    user: CurrentUser,
    service: PlatformServiceDep,
) -> PlatformResponse:
    """Update a platform connection."""
    update_data = req.model_dump(exclude_unset=True)
    platform = await service.update_platform(platform_id, update_data)
    return _to_response(platform)


@router.delete("/{platform_id}", status_code=204)
async def delete_platform(
    platform_id: int,
    user: CurrentUser,
    service: PlatformServiceDep,
) -> None:
    """Delete a platform connection."""
    await service.delete_platform(platform_id)


@router.post("/{platform_id}/test", response_model=ConnectionTestResponse)
async def test_connection(
    platform_id: int,
    user: CurrentUser,
    service: PlatformServiceDep,
) -> ConnectionTestResponse:
    """Test the connection to a platform."""
    result = await service.test_connection(platform_id)
    return ConnectionTestResponse(**result)


@router.post("/{platform_id}/sync")
async def sync_devices(
    platform_id: int,
    user: CurrentUser,
    service: PlatformServiceDep,
) -> dict[str, Any]:
    """Sync devices from a platform (VMs + hosts).

    Connects to the platform, retrieves all VMs and hosts,
    and stores them in the assets table.
    """
    return await service.sync_devices(platform_id)


@router.get("/{platform_id}/devices", response_model=list[DeviceResponse])
async def list_devices(
    platform_id: int,
    user: CurrentUser,
    service: PlatformServiceDep,
) -> list[DeviceResponse]:
    """List all devices for a platform (from assets table)."""
    devices = await service.list_devices(platform_id)
    return [DeviceResponse(**d) for d in devices]
