"""Huawei FusionSphere platform adapter using httpx REST API.

Targets FusionCompute 8.0 REST API.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import structlog

from app.platforms.base import (
    AdapterConnectionError, AdapterError, AuthenticationError,
    ConnectionTestResult, DeviceInfo, NotFoundError,
    OperationFailedError, PlatformAdapter, PlatformConfig, PlatformType,
)

logger = structlog.get_logger(__name__)


class FusionSphereAdapter(PlatformAdapter):
    """Huawei FusionSphere adapter backed by httpx."""

    platform_type = PlatformType.FUSIONSPHERE

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._config: PlatformConfig | None = None
        self._connected: bool = False
        self._token: str = ""
        self._base_url: str = ""

    async def connect(self, config: PlatformConfig) -> bool:
        """Authenticate and get a session token."""
        self._config = config
        # Use configured port; default to 7443 for FusionSphere if port is default 443
        port = config.port
        # Always use HTTPS; verify_ssl only controls certificate verification
        scheme = "https"
        self._base_url = f"{scheme}://{config.host}:{port}"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            verify=config.verify_ssl,
            timeout=30.0,
        )

        try:
            resp = await self._client.post(
                "/service/sessions",
                json={"scope": 0, "username": config.username, "password": config.password},
            )
            if resp.status_code == 401:
                raise AuthenticationError(f"Invalid credentials for {config.host}")
            resp.raise_for_status()
            data = resp.json()
            self._token = data.get("token", "")
            self._client.headers["X-Auth-Token"] = self._token
            self._connected = True
            logger.info("fusionsphere_connected", host=config.host)
            return True
        except AuthenticationError:
            raise
        except httpx.HTTPError as exc:
            raise AdapterConnectionError(f"Cannot connect to {config.host}: {exc}") from exc

    async def disconnect(self) -> None:
        """Logout and close the HTTP client."""
        if self._client is not None:
            try:
                await self._client.delete("/service/sessions")
            except Exception as exc:
                logger.warning("fusionsphere_logout_error", error=str(exc))
            finally:
                await self._client.aclose()
                self._client = None
                self._connected = False
                self._token = ""
                logger.info("fusionsphere_disconnected")

    async def test_connection(self) -> ConnectionTestResult:
        """Test the FusionCompute API connection."""
        if not self._connected or self._client is None:
            return ConnectionTestResult(success=False, latency_ms=0, version="", error="Not connected")
        try:
            t0 = time.monotonic()
            resp = await self._client.get("/service/version")
            resp.raise_for_status()
            data = resp.json()
            latency = int((time.monotonic() - t0) * 1000)
            return ConnectionTestResult(
                success=True, latency_ms=latency,
                version=data.get("version", "unknown"),
                details=data,
            )
        except Exception as exc:
            return ConnectionTestResult(success=False, latency_ms=0, version="", error=str(exc))

    def _ensure_connected(self) -> httpx.AsyncClient:
        """Return the HTTP client or raise."""
        if not self._connected or self._client is None:
            raise AdapterError("Not connected -- call connect() first")
        return self._client

    @staticmethod
    def _vm_to_device_info(vm: dict) -> DeviceInfo:
        """Convert a FusionCompute VM dict to DeviceInfo."""
        status_map = {
            0: "stopped", 1: "running", 2: "paused",
            3: "unknown", 4: "creating", 5: "deleting",
        }
        vm_status = vm.get("status", 0)
        return DeviceInfo(
            id=vm.get("vmId", ""),
            name=vm.get("name", ""),
            device_type="vm",
            status=status_map.get(vm_status, "unknown"),
            ip_address=vm.get("ipAddress", ""),
            platform="fusionsphere",
            metadata={
                "cpu_count": vm.get("cpuNum", 0),
                "memory_mb": vm.get("memory", 0) // 1024 // 1024,
                "cluster": vm.get("cluster", {}).get("name", ""),
                "host": vm.get("host", {}).get("name", ""),
                "description": vm.get("description", ""),
            },
        )

    async def list_vms(self) -> list[DeviceInfo]:
        """List all VMs."""
        client = self._ensure_connected()

        try:
            resp = await client.get("/service/vms")
            resp.raise_for_status()
            data = resp.json()
            vms = data.get("vms", [])
            return [self._vm_to_device_info(vm) for vm in vms]
        except httpx.HTTPError as exc:
            raise AdapterError(f"Failed to list VMs: {exc}") from exc

    async def list_hosts(self) -> list[DeviceInfo]:
        """List all hosts."""
        client = self._ensure_connected()

        try:
            resp = await client.get("/service/hosts")
            resp.raise_for_status()
            data = resp.json()
            hosts = data.get("hosts", [])
            result = []
            for h in hosts:
                result.append(DeviceInfo(
                    id=h.get("hostId", ""),
                    name=h.get("name", ""),
                    device_type="host",
                    status="running" if h.get("status") == 1 else "stopped",
                    ip_address=h.get("managementIp", ""),
                    platform="fusionsphere",
                    metadata={
                        "cpu_cores": h.get("cpuNum", 0),
                        "memory_mb": h.get("memorySize", 0) // 1024 // 1024,
                        "os_version": h.get("osVersion", ""),
                    },
                ))
            return result
        except httpx.HTTPError as exc:
            raise AdapterError(f"Failed to list hosts: {exc}") from exc

    async def get_vm_status(self, vm_id: str) -> DeviceInfo:
        """Get VM status."""
        client = self._ensure_connected()
        try:
            resp = await client.get(f"/service/vms/{vm_id}")
            if resp.status_code == 404:
                raise NotFoundError(f"VM {vm_id} not found")
            resp.raise_for_status()
            return self._vm_to_device_info(resp.json())
        except httpx.HTTPError as exc:
            raise AdapterError(f"Failed to get VM status: {exc}") from exc

    async def power_on(self, vm_id: str) -> bool:
        """Power on a VM."""
        return await self._vm_action(vm_id, "start")

    async def power_off(self, vm_id: str, graceful: bool = True) -> bool:
        """Power off a VM."""
        action = "stop" if graceful else "force-stop"
        return await self._vm_action(vm_id, action)

    async def reboot(self, vm_id: str, graceful: bool = True) -> bool:
        """Reboot a VM."""
        action = "reboot" if graceful else "force-reboot"
        return await self._vm_action(vm_id, action)

    async def _vm_action(self, vm_id: str, action: str) -> bool:
        """Execute a VM action (start/stop/reboot)."""
        client = self._ensure_connected()
        try:
            resp = await client.post(f"/service/vms/{vm_id}/action/{action}")
            if resp.status_code == 404:
                raise NotFoundError(f"VM {vm_id} not found")
            resp.raise_for_status()
            return True
        except NotFoundError:
            raise
        except httpx.HTTPError as exc:
            raise OperationFailedError(f"Action {action} failed: {exc}") from exc

    async def create_snapshot(self, vm_id: str, name: str, description: str = "") -> str:
        """Create a snapshot."""
        client = self._ensure_connected()
        try:
            resp = await client.post(
                f"/service/vms/{vm_id}/snapshots",
                json={"name": name, "description": description},
            )
            if resp.status_code == 404:
                raise NotFoundError(f"VM {vm_id} not found")
            resp.raise_for_status()
            return resp.json().get("snapshotId", "")
        except NotFoundError:
            raise
        except httpx.HTTPError as exc:
            raise OperationFailedError(f"Snapshot creation failed: {exc}") from exc

    async def list_snapshots(self, vm_id: str) -> list[dict]:
        """List all snapshots for a VM."""
        client = self._ensure_connected()
        try:
            resp = await client.get(f"/service/vms/{vm_id}/snapshots")
            if resp.status_code == 404:
                raise NotFoundError(f"VM {vm_id} not found")
            resp.raise_for_status()
            data = resp.json()
            snapshots = data.get("snapshots", [])
            return [
                {
                    "id": s.get("snapshotId", ""),
                    "name": s.get("name", ""),
                    "description": s.get("description", ""),
                    "created_at": s.get("createTime", ""),
                    "state": "ready", "size_bytes": 0,
                }
                for s in snapshots
            ]
        except NotFoundError:
            raise
        except httpx.HTTPError as exc:
            raise AdapterError(f"Failed to list snapshots: {exc}") from exc

    async def revert_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        """Revert to a snapshot."""
        client = self._ensure_connected()
        try:
            resp = await client.post(f"/service/vms/{vm_id}/snapshots/{snapshot_id}/revert")
            if resp.status_code == 404:
                raise NotFoundError(f"Snapshot {snapshot_id} not found")
            resp.raise_for_status()
            return True
        except NotFoundError:
            raise
        except httpx.HTTPError as exc:
            raise OperationFailedError(f"Revert failed: {exc}") from exc

    async def migrate(self, vm_id: str, target_host: str | None = None) -> bool:
        """Migrate a VM to target_host."""
        client = self._ensure_connected()
        if target_host is None:
            raise OperationFailedError("Target host is required for FusionSphere migration")
        try:
            resp = await client.post(
                f"/service/vms/{vm_id}/action/migrate",
                json={"targetHost": target_host},
            )
            if resp.status_code == 404:
                raise NotFoundError(f"VM {vm_id} not found")
            resp.raise_for_status()
            return True
        except NotFoundError:
            raise
        except httpx.HTTPError as exc:
            raise OperationFailedError(f"Migration failed: {exc}") from exc

    async def get_metrics(self, vm_id: str) -> dict:
        """Fetch performance metrics for a VM."""
        client = self._ensure_connected()
        try:
            resp = await client.get(f"/service/vms/{vm_id}/metrics")
            if resp.status_code == 404:
                raise NotFoundError(f"VM {vm_id} not found")
            resp.raise_for_status()
            return resp.json()
        except NotFoundError:
            raise
        except httpx.HTTPError as exc:
            logger.warning("metrics_failed", vm_id=vm_id, error=str(exc))
            return {}
