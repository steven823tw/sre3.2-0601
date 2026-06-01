"""Asset model — represents infrastructure resources.

Covers VMs, hosts, storage, network devices, and databases.
Each asset belongs to a platform (vSphere, OpenStack, K8s, physical).
"""
from __future__ import annotations

from enum import Enum as PyEnum

from sqlalchemy import JSON, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AssetType(str, PyEnum):
    """Type of infrastructure asset."""
    VM = "vm"
    HOST = "host"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CONTAINER = "container"


class AssetStatus(str, PyEnum):
    """Current operational status of an asset."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class Platform(str, PyEnum):
    """Infrastructure platform — all lowercase for consistency with PlatformType."""
    VSPHERE = "vsphere"
    KVM = "kvm"
    FUSIONSPHERE = "fusionsphere"
    OPENSTACK = "openstack"
    K8S = "kubernetes"
    PHYSICAL = "physical"
    OTHER = "other"


class Asset(Base, TimestampMixin):
    """Infrastructure asset record."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, native_enum=False, length=50), nullable=False, index=True
    )
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform, native_enum=False, length=50), nullable=False, index=True
    )
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, native_enum=False, length=50),
        nullable=False,
        default=AssetStatus.UNKNOWN,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_assets_type_status", "asset_type", "status"),
        Index("ix_assets_platform_type", "platform", "asset_type"),
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name={self.name!r}, type={self.asset_type})>"
