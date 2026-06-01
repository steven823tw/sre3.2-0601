"""Platform service — business logic for platform connection management.

Encapsulates CRUD, connection testing, device sync, encrypt/decrypt,
and adapter management for platform connections.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt, encrypt
from app.exceptions import NotFoundException, ValidationException, OperationFailedException
from app.models.asset import Asset, AssetStatus, AssetType
from app.models.platform import PlatformConnection, PlatformType
from app.platforms.base import PlatformAdapter, PlatformConfig
from app.platforms.fusionsphere.adapter import FusionSphereAdapter
from app.platforms.kvm.adapter import KVMAdapter
from app.platforms.vsphere.adapter import VSphereAdapter
from app.repositories.platform_repo import PlatformRepository

logger = logging.getLogger(__name__)


class PlatformService:
    """Business logic for platform CRUD, connection testing, and device sync."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PlatformRepository(session)

    # ── CRUD ────────────────────────────────────────────────────────────

    async def list_platforms(self) -> list[PlatformConnection]:
        """Return all platform connections ordered by id."""
        return list(await self._repo.list(order_by=PlatformConnection.id))

    async def get_platform(self, platform_id: int) -> PlatformConnection:
        """Fetch a platform by ID or raise 404."""
        platform = await self._repo.get_by_id(platform_id)
        if not platform:
            raise NotFoundException("Platform", platform_id)
        return platform

    async def create_platform(
        self,
        *,
        name: str,
        platform_type: PlatformType,
        host: str,
        port: int,
        username: str,
        password: str,
        verify_ssl: bool,
        extra: dict[str, Any],
    ) -> PlatformConnection:
        """Create a new platform connection with encrypted password."""
        platform = PlatformConnection(
            name=name,
            platform_type=platform_type,
            host=host,
            port=port,
            username=username,
            encrypted_password=encrypt(password) if password else "",
            verify_ssl=verify_ssl,
            extra=extra,
        )
        created = await self._repo.create(platform)
        logger.info("platform_created", platform_id=created.id, type=platform_type, host=host)
        return created

    async def update_platform(
        self,
        platform_id: int,
        update_data: dict[str, Any],
    ) -> PlatformConnection:
        """Partial-update a platform connection.

        ``update_data`` keys should use the Pydantic model field names.
        The ``password`` key is handled specially: encrypted before storage.
        """
        platform = await self.get_platform(platform_id)
        for field, value in update_data.items():
            if field == "password":
                setattr(platform, "encrypted_password", encrypt(value) if value else "")
            else:
                setattr(platform, field, value)
        updated = await self._repo.update(platform)
        logger.info("platform_updated", platform_id=platform_id)
        return updated

    async def delete_platform(self, platform_id: int) -> None:
        """Delete a platform connection or raise 404."""
        platform = await self.get_platform(platform_id)
        await self._repo.delete(platform)
        logger.info("platform_deleted", platform_id=platform_id)

    # ── Connection testing ──────────────────────────────────────────────

    async def test_connection(self, platform_id: int) -> dict[str, Any]:
        """Test connectivity to a platform.

        Returns a dict suitable for ``ConnectionTestResponse``.
        Updates the ``connected`` flag on the platform record.
        """
        platform = await self.get_platform(platform_id)
        adapter = _get_adapter(platform.platform_type)
        config = _build_config(platform)

        try:
            await adapter.connect(config)
            result = await adapter.test_connection()
            await adapter.disconnect()

            platform.connected = result.success
            await self._session.flush()

            return {
                "success": result.success,
                "latency_ms": result.latency_ms,
                "version": result.version,
                "details": result.details,
                "error": result.error,
            }
        except Exception as exc:
            logger.error("connection_test_failed", platform_id=platform_id, error=str(exc))
            platform.connected = False
            await self._session.flush()
            return {
                "success": False,
                "latency_ms": 0,
                "version": "",
                "error": str(exc),
            }

    # ── Device sync ─────────────────────────────────────────────────────

    async def sync_devices(self, platform_id: int) -> dict[str, Any]:
        """Sync VMs and hosts from a platform into the assets table.

        Connects to the platform adapter, retrieves all VMs and hosts,
        then upserts them into the ``assets`` table.
        """
        platform = await self.get_platform(platform_id)
        adapter = _get_adapter(platform.platform_type)
        config = _build_config(platform)

        try:
            await adapter.connect(config)
            vms = await adapter.list_vms()
            hosts = await adapter.list_hosts()
            await adapter.disconnect()

            vm_count = 0
            host_count = 0

            for device in vms:
                result = await self._session.execute(
                    select(Asset).where(
                        Asset.name == device.name,
                        Asset.platform == platform.platform_type.value,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.ip_address = device.ip_address
                    existing.status = AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED
                    existing.metadata_ = device.metadata
                else:
                    asset = Asset(
                        name=device.name,
                        asset_type=AssetType.VM,
                        platform=platform.platform_type.value,
                        status=AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED,
                        ip_address=device.ip_address,
                        hostname=device.name,
                        metadata_=device.metadata,
                    )
                    self._session.add(asset)
                    vm_count += 1

            for device in hosts:
                result = await self._session.execute(
                    select(Asset).where(
                        Asset.name == device.name,
                        Asset.platform == platform.platform_type.value,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.ip_address = device.ip_address
                    existing.status = AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED
                    existing.metadata_ = device.metadata
                else:
                    asset = Asset(
                        name=device.name,
                        asset_type=AssetType.HOST,
                        platform=platform.platform_type.value,
                        status=AssetStatus.RUNNING if device.status == "running" else AssetStatus.STOPPED,
                        ip_address=device.ip_address,
                        hostname=device.name,
                        metadata_=device.metadata,
                    )
                    self._session.add(asset)
                    host_count += 1

            await self._session.flush()
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
            raise OperationFailedException("sync_devices", str(exc))

    # ── Device listing ──────────────────────────────────────────────────

    async def list_devices(self, platform_id: int) -> list[dict[str, Any]]:
        """List all devices (assets) belonging to a platform.

        Returns a list of dicts suitable for ``DeviceResponse``.
        """
        platform = await self.get_platform(platform_id)
        result = await self._session.execute(
            select(Asset).where(Asset.platform == platform.platform_type.value)
        )
        assets = result.scalars().all()

        return [
            {
                "id": str(asset.id),
                "name": asset.name,
                "device_type": asset.asset_type.value if asset.asset_type else "unknown",
                "status": asset.status.value if asset.status else "unknown",
                "ip_address": asset.ip_address or "",
                "platform": asset.platform.value if asset.platform else "unknown",
                "metadata": asset.metadata_ or {},
            }
            for asset in assets
        ]


# ── Module-level helpers ────────────────────────────────────────────────


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
            raise ValidationException(f"Unsupported platform: {platform_type}")


def _safe_decrypt(encrypted: str | None) -> str:
    """Decrypt a password, falling back to plaintext if decryption fails.

    This handles pre-migration records where passwords were stored in plaintext.
    Only catches InvalidToken (wrong key or non-Fernet data), not programming errors.

    TODO(v3.3): Remove plaintext fallback — all passwords must be encrypted by then.
    """
    if not encrypted:
        return ""
    try:
        return decrypt(encrypted)
    except Exception as exc:
        from cryptography.fernet import InvalidToken
        if isinstance(exc, InvalidToken):
            logger.error(
                "password_decrypt_fallback_plaintext",
                hint="pre-migration plaintext — re-save this platform to encrypt",
            )
            return encrypted
        raise


def _build_config(platform: PlatformConnection) -> PlatformConfig:
    """Build PlatformConfig from database model."""
    return PlatformConfig(
        platform_type=platform.platform_type,
        host=platform.host,
        port=platform.port,
        username=platform.username,
        password=_safe_decrypt(platform.encrypted_password),
        verify_ssl=platform.verify_ssl,
        extra=platform.extra or {},
    )
