"""Platform management API endpoints.

Provides CRUD operations for platform connections and
device management (list, sync, test).

All platform configurations are persisted in the database.
Passwords are encrypted before storage.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.platform import PlatformConnection, PlatformType
from app.platforms.base import PlatformAdapter, PlatformConfig
from app.platforms.vsphere.adapter import VSphereAdapter
from app.platforms.kvm.adapter import KVMAdapter
from app.platforms.fusionsphere.adapter import FusionSphereAdapter

logger = logging.getLogger(__name__)

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


# ── Adapter Cache ────────────────────────────────────────────────────────

def _get_adapter(platform_type: PlatformType) -> PlatformAdapter:
    """Create a new adapter instance for the given platform type."""
    match platform_type:
        case PlatformType.VSPHERE:
            return VSphereAdapter()
        case PlatformType.KVM:
            return KVMAdapter()
        case PlatformType.FUSIONSPHERE:
            return FusionSphereAdapter()
        case _:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform_type}")


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


def _build_config(platform: PlatformConnection) -> PlatformConfig:
    """Build PlatformConfig from database model."""
    return PlatformConfig(
        platform_type=platform.platform_type,
        host=platform.host,
        port=platform.port,
        username=platform.username,
        password=platform.encrypted_password or "",
        verify_ssl=platform.verify_ssl,
        extra=platform.extra or {},
    )


# ── API Endpoints ────────────────────────────────────────────────────────

@router.get("/", response_model=list[PlatformResponse])
async def list_platforms(
    db: AsyncSession = Depends(get_db),
) -> list[PlatformResponse]:
    """List all configured platforms."""
    result = await db.execute(select(PlatformConnection).order_by(PlatformConnection.id))
    platforms = result.scalars().all()
    return [_to_response(p) for p in platforms]


@router.post("/", response_model=PlatformResponse, status_code=201)
async def create_platform(
    req: PlatformCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> PlatformResponse:
    """Add a new platform connection."""
    platform = PlatformConnection(
        name=req.name,
        platform_type=req.platform_type,
        host=req.host,
        port=req.port,
        username=req.username,
        encrypted_password=req.password,
        verify_ssl=req.verify_ssl,
        extra=req.extra,
    )
    db.add(platform)
    await db.flush()
    await db.refresh(platform)
    logger.info("platform_created", platform_id=platform.id, type=req.platform_type, host=req.host)
    return _to_response(platform)


@router.get("/{platform_id}", response_model=PlatformResponse)
async def get_platform(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
) -> PlatformResponse:
    """Get a platform by ID."""
    platform = await db.get(PlatformConnection, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    return _to_response(platform)


@router.put("/{platform_id}", response_model=PlatformResponse)
async def update_platform(
    platform_id: int,
    req: PlatformUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> PlatformResponse:
    """Update a platform connection."""
    platform = await db.get(PlatformConnection, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(platform, "encrypted_password", value)
        else:
            setattr(platform, field, value)

    await db.flush()
    await db.refresh(platform)
    logger.info("platform_updated", platform_id=platform_id)
    return _to_response(platform)


@router.delete("/{platform_id}", status_code=204)
async def delete_platform(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a platform connection."""
    platform = await db.get(PlatformConnection, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    await db.delete(platform)
    await db.flush()
    logger.info("platform_deleted", platform_id=platform_id)


@router.post("/{platform_id}/test", response_model=ConnectionTestResponse)
async def test_connection(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
) -> ConnectionTestResponse:
    """Test the connection to a platform."""
    platform = await db.get(PlatformConnection, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    adapter = _get_adapter(platform.platform_type)
    config = _build_config(platform)

    try:
        await adapter.connect(config)
        result = await adapter.test_connection()
        await adapter.disconnect()

        # Update connected status in database
        platform.connected = result.success
        await db.flush()

        return ConnectionTestResponse(
            success=result.success,
            latency_ms=result.latency_ms,
            version=result.version,
            details=result.details,
            error=result.error,
        )
    except Exception as exc:
        logger.error("connection_test_failed", platform_id=platform_id, error=str(exc))
        platform.connected = False
        await db.flush()
        return ConnectionTestResponse(
            success=False,
            latency_ms=0,
            version="",
            error=str(exc),
        )


@router.post("/{platform_id}/sync")
async def sync_devices(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Sync devices from a platform (VMs + hosts).

    Connects to the platform, retrieves all VMs and hosts,
    and stores them in the assets table.
    """
    from app.models.asset import Asset, AssetStatus, AssetType

    platform = await db.get(PlatformConnection, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    adapter = _get_adapter(platform.platform_type)
    config = _build_config(platform)

    try:
        await adapter.connect(config)
        vms = await adapter.list_vms()
        hosts = await adapter.list_hosts()
        await adapter.disconnect()

        # Upsert devices into assets table
        vm_count = 0
        host_count = 0

        for device in vms:
            # Check if asset already exists
            result = await db.execute(
                select(Asset).where(
                    Asset.name == device.name,
                    Asset.platform == platform.platform_type.value,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing asset
                existing.ip_address = device.ip_address
                existing.status = AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED
                existing.metadata = device.metadata
            else:
                # Create new asset
                asset = Asset(
                    name=device.name,
                    asset_type=AssetType.VM,
                    platform=platform.platform_type,
                    status=AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED,
                    ip_address=device.ip_address,
                    hostname=device.name,
                    metadata=device.metadata,
                )
                db.add(asset)
                vm_count += 1

        for device in hosts:
            result = await db.execute(
                select(Asset).where(
                    Asset.name == device.name,
                    Asset.platform == platform.platform_type.value,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.ip_address = device.ip_address
                existing.status = AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED
                existing.metadata = device.metadata
            else:
                asset = Asset(
                    name=device.name,
                    asset_type=AssetType.HOST,
                    platform=platform.platform_type,
                    status=AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED,
                    ip_address=device.ip_address,
                    hostname=device.name,
                    metadata=device.metadata,
                )
                db.add(asset)
                host_count += 1

        await db.flush()
        logger.info(
            "sync_complete",
            platform_id=platform_id,
            vm_count=vm_count,
            host_count=host_count,
            total_vms=len(vms),
            total_hosts=len(hosts),
        )
        return {
            "status": "ok",
            "vms_synced": len(vms),
            "hosts_synced": len(hosts),
            "vms_created": vm_count,
            "hosts_created": host_count,
        }
    except Exception as exc:
        logger.error("sync_failed", platform_id=platform_id, error=str(exc))
        raise HTTPException(status_code=500, detail=f"Sync failed: {exc}")


@router.get("/{platform_id}/devices", response_model=list[DeviceResponse])
async def list_devices(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[DeviceResponse]:
    """List all devices for a platform (from assets table)."""
    from app.models.asset import Asset

    platform = await db.get(PlatformConnection, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    result = await db.execute(
        select(Asset).where(Asset.platform == platform.platform_type.value)
    )
    assets = result.scalars().all()

    return [
        DeviceResponse(
            id=str(asset.id),
            name=asset.name,
            device_type=asset.asset_type.value if asset.asset_type else "unknown",
            status=asset.status.value if asset.status else "unknown",
            ip_address=asset.ip_address or "",
            platform=asset.platform.value if asset.platform else "unknown",
            metadata=asset.metadata or {},
        )
        for asset in assets
    ]
