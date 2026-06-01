"""Abstract base classes and shared types for platform adapters."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from app.exceptions import AppException

logger = logging.getLogger(__name__)


class PlatformType(str, Enum):
    """Supported hypervisor platforms."""
    VSPHERE = "vsphere"
    KVM = "kvm"
    FUSIONSPHERE = "fusionsphere"


@dataclass
class PlatformConfig:
    """Connection parameters for a single platform instance."""
    platform_type: PlatformType
    host: str
    port: int = 443
    username: str = ""
    password: str = ""
    verify_ssl: bool = True
    extra: dict = field(default_factory=dict)


@dataclass
class ConnectionTestResult:
    """Returned by PlatformAdapter.test_connection."""
    success: bool
    latency_ms: int
    version: str
    details: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class DeviceInfo:
    """Unified representation of a VM, host, or storage device."""
    id: str
    name: str
    device_type: str
    status: str
    ip_address: str
    platform: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SnapshotInfo:
    """Represents a single VM snapshot."""
    id: str
    name: str
    description: str
    created_at: str
    state: str
    size_bytes: int = 0


class PlatformAdapter(ABC):
    """Contract that every platform adapter must honour."""
    platform_type: PlatformType

    @abstractmethod
    async def connect(self, config: PlatformConfig) -> bool: ...
    @abstractmethod
    async def disconnect(self) -> None: ...
    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult: ...
    @abstractmethod
    async def list_vms(self) -> list[DeviceInfo]: ...
    @abstractmethod
    async def list_hosts(self) -> list[DeviceInfo]: ...
    @abstractmethod
    async def get_vm_status(self, vm_id: str) -> DeviceInfo: ...
    @abstractmethod
    async def power_on(self, vm_id: str) -> bool: ...
    @abstractmethod
    async def power_off(self, vm_id: str, graceful: bool = True) -> bool: ...
    @abstractmethod
    async def reboot(self, vm_id: str, graceful: bool = True) -> bool: ...
    @abstractmethod
    async def create_snapshot(self, vm_id: str, name: str, description: str = "") -> str: ...
    @abstractmethod
    async def list_snapshots(self, vm_id: str) -> list[dict]: ...
    @abstractmethod
    async def revert_snapshot(self, vm_id: str, snapshot_id: str) -> bool: ...
    @abstractmethod
    async def migrate(self, vm_id: str, target_host: str | None = None) -> bool: ...
    @abstractmethod
    async def get_metrics(self, vm_id: str) -> dict: ...


class AdapterError(AppException):
    """Base exception for all adapter errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        error_code: str = "ADAPTER_ERROR",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            error_code=error_code,
            message=message,
            details=details,
        )


class AdapterConnectionError(AdapterError):
    """Platform is unreachable."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            status_code=503,
            error_code="ADAPTER_CONNECTION_ERROR",
            details=details,
        )


class AuthenticationError(AdapterError):
    """Credentials rejected by the platform."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            status_code=401,
            error_code="ADAPTER_AUTHENTICATION_ERROR",
            details=details,
        )


class NotFoundError(AdapterError):
    """Requested resource does not exist."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            status_code=404,
            error_code="ADAPTER_NOT_FOUND",
            details=details,
        )


class OperationFailedError(AdapterError):
    """A platform operation failed."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            status_code=500,
            error_code="ADAPTER_OPERATION_FAILED",
            details=details,
        )
