"""Platform model — stores hypervisor platform connection configs.

Each platform record holds connection parameters for a single
vSphere, KVM, or FusionSphere instance. Passwords are stored
encrypted (application-level encryption before persistence).
"""
from __future__ import annotations

from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PlatformType(str, PyEnum):
    """Supported hypervisor platforms."""
    VSPHERE = "vsphere"
    KVM = "kvm"
    FUSIONSPHERE = "fusionsphere"


class PlatformConnection(Base, TimestampMixin):
    """Stores a platform connection configuration.

    Attributes:
        id: Auto-increment primary key.
        name: Human-readable display name.
        platform_type: Hypervisor type.
        host: Hostname or IP address.
        port: API port (default 443 for vSphere, 22 for KVM, 7443 for FusionSphere).
        username: Authentication username.
        encrypted_password: Encrypted password (never exposed via API).
        verify_ssl: Whether to verify TLS certificates.
        extra: Platform-specific configuration (e.g. transport, cluster filters).
        connected: Whether the last connection test succeeded.
    """

    __tablename__ = "platform_connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform_type: Mapped[PlatformType] = mapped_column(
        Enum(PlatformType, native_enum=False, length=20), nullable=False, index=True
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    username: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    encrypted_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    connected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return (
            f"<PlatformConnection(id={self.id}, name={self.name!r}, "
            f"type={self.platform_type})>"
        )
