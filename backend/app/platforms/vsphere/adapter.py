"""VMware vSphere platform adapter using pyVmomi 8.0.3.

Supports vCenter and standalone ESXi 6.5 / 7.0 / 8.0.
All pyVmomi calls are synchronous -- wrapped with asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
import ssl
import time
from typing import Any

import structlog

from app.platforms.base import (
    AdapterError, AuthenticationError, AdapterConnectionError,
    ConnectionTestResult, DeviceInfo, NotFoundError,
    OperationFailedError, PlatformAdapter, PlatformConfig, PlatformType,
)

logger = structlog.get_logger(__name__)

try:
    from pyVim.connect import Disconnect, SmartConnect
    from pyVmomi import vim, vmodl
    _PYVMOMI_AVAILABLE = True
except ImportError:
    _PYVMOMI_AVAILABLE = False
    logger.warning("pyVmomi not installed -- vSphere adapter unavailable")


def _build_ssl_context(verify: bool) -> ssl.SSLContext | None:
    """Return an SSL context that skips cert checks if verify is False."""
    if not verify:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None


def _get_obj_prop(obj: Any, dotted_path: str, default: Any = None) -> Any:
    """Safely traverse dotted attribute paths."""
    current = obj
    for part in dotted_path.split("."):
        if current is None:
            return default
        current = getattr(current, part, None)
    return current if current is not None else default


def _vm_to_device_info(vm: Any) -> DeviceInfo:
    """Convert a pyVmomi VirtualMachine to DeviceInfo."""
    ip_addr = _get_obj_prop(vm, "guest.ipAddress", "")
    status = "unknown"
    ps = vm.runtime.powerState
    if ps == vim.VirtualMachinePowerState.poweredOn:
        status = "running"
    elif ps == vim.VirtualMachinePowerState.poweredOff:
        status = "stopped"
    elif ps == vim.VirtualMachinePowerState.suspended:
        status = "suspended"
    metadata: dict[str, Any] = {
        "cpu_count": _get_obj_prop(vm, "config.hardware.numCPU", 0),
        "memory_mb": _get_obj_prop(vm, "config.hardware.memoryMB", 0),
        "guest_os": _get_obj_prop(vm, "config.guestFullName", ""),
        "host": _get_obj_prop(vm, "runtime.host.name", ""),
        "cluster": _get_obj_prop(vm, "resourcePool.owner.name", ""),
        "datastore": ", ".join(
            ds.name for ds in getattr(vm, "datastore", []) if hasattr(ds, "name")
        ),
        "uuid": _get_obj_prop(vm, "config.instanceUuid", ""),
        "folder": _get_obj_prop(vm, "parent.name", ""),
        "annotation": _get_obj_prop(vm, "config.annotation", ""),
        "connection_state": _get_obj_prop(vm, "runtime.connectionState", ""),
        "boot_time": str(_get_obj_prop(vm, "runtime.bootTime", "")),
    }
    return DeviceInfo(
        id=str(vm._moId), name=vm.name or "", device_type="vm",
        status=status, ip_address=ip_addr or "", platform="vsphere",
        metadata=metadata,
    )


def _host_to_device_info(host: Any) -> DeviceInfo:
    """Convert a pyVmomi HostSystem to DeviceInfo."""
    ip_addr = _get_obj_prop(host, "summary.managementServerIp", "")
    status = "connected" if host.runtime.connectionState == "connected" else "disconnected"
    metadata: dict[str, Any] = {
        "vendor": _get_obj_prop(host, "summary.hardware.vendor", ""),
        "model": _get_obj_prop(host, "summary.hardware.model", ""),
        "cpu_model": _get_obj_prop(host, "summary.hardware.cpuModel", ""),
        "cpu_cores": _get_obj_prop(host, "summary.hardware.numCpuCores", 0),
        "memory_gb": round(_get_obj_prop(host, "summary.hardware.memorySize", 0) / (1024**3), 2),
        "version": _get_obj_prop(host, "config.product.version", ""),
        "build": _get_obj_prop(host, "config.product.build", ""),
        "cluster": _get_obj_prop(host, "parent.name", ""),
    }
    return DeviceInfo(
        id=str(host._moId), name=host.name or "", device_type="host",
        status=status, ip_address=ip_addr or "", platform="vsphere",
        metadata=metadata,
    )


class VSphereAdapter(PlatformAdapter):
    """VMware vSphere adapter backed by pyVmomi."""

    platform_type = PlatformType.VSPHERE

    def __init__(self) -> None:
        self._si: Any | None = None
        self._config: PlatformConfig | None = None
        self._connected: bool = False

    async def connect(self, config: PlatformConfig) -> bool:
        """Open a SmartConnect session to vCenter / ESXi."""
        if not _PYVMOMI_AVAILABLE:
            raise AdapterError("pyVmomi is not installed")
        self._config = config

        def _connect() -> Any:
            ssl_ctx = _build_ssl_context(config.verify_ssl)
            try:
                if ssl_ctx is not None:
                    return SmartConnect(
                        host=config.host, user=config.username,
                        pwd=config.password, port=config.port, sslContext=ssl_ctx,
                    )
                return SmartConnect(
                    host=config.host, user=config.username,
                    pwd=config.password, port=config.port,
                )
            except vim.fault.InvalidLogin as exc:
                raise AuthenticationError(
                    f"Invalid credentials for {config.host}: {exc}"
                ) from exc
            except Exception as exc:
                raise AdapterConnectionError(
                    f"Cannot connect to {config.host}:{config.port}: {exc}"
                ) from exc

        try:
            self._si = await asyncio.to_thread(_connect)
            self._connected = True
            logger.info("vsphere_connected", host=config.host, port=config.port)
            return True
        except (AuthenticationError, AdapterConnectionError):
            raise
        except Exception as exc:
            raise AdapterConnectionError(f"Unexpected error: {exc}") from exc

    async def disconnect(self) -> None:
        """Disconnect from vCenter / ESXi."""
        if self._si is not None:
            try:
                await asyncio.to_thread(Disconnect, self._si)
            except Exception as exc:
                logger.warning("vsphere_disconnect_error", error=str(exc))
            finally:
                self._si = None
                self._connected = False
                logger.info("vsphere_disconnected")

    async def test_connection(self) -> ConnectionTestResult:
        """Ping the vCenter API and return version / latency."""
        if not self._connected or self._si is None:
            return ConnectionTestResult(success=False, latency_ms=0, version="", error="Not connected")
        try:
            t0 = time.monotonic()

            def _query() -> dict[str, Any]:
                about = self._si.content.about
                return {
                    "version": about.version, "build": about.build,
                    "api_type": about.apiType, "api_version": about.apiVersion,
                    "os_type": about.osType, "instance_uuid": about.instanceUuid,
                    "license_product_name": about.licenseProductName,
                }

            info = await asyncio.to_thread(_query)
            latency = int((time.monotonic() - t0) * 1000)
            return ConnectionTestResult(success=True, latency_ms=latency, version=info["version"], details=info)
        except Exception as exc:
            return ConnectionTestResult(success=False, latency_ms=0, version="", error=str(exc))

    def _ensure_connected(self) -> Any:
        """Return the ServiceInstance or raise."""
        if not self._connected or self._si is None:
            raise AdapterError("Not connected -- call connect() first")
        return self._si

    def _find_vm_by_id(self, si: Any, vm_id: str) -> Any:
        """Locate a VM managed object by MOID."""
        container = si.content.viewManager.CreateContainerView(
            si.content.rootFolder, [vim.VirtualMachine], True
        )
        try:
            for vm in container.view:
                if str(vm._moId) == vm_id:
                    return vm
        finally:
            container.Destroy()
        raise NotFoundError(f"VM {vm_id} not found")

    async def list_vms(self) -> list[DeviceInfo]:
        """List all virtual machines."""
        si = self._ensure_connected()

        def _list() -> list[DeviceInfo]:
            container = si.content.viewManager.CreateContainerView(
                si.content.rootFolder, [vim.VirtualMachine], True
            )
            try:
                return [_vm_to_device_info(vm) for vm in container.view]
            finally:
                container.Destroy()

        return await asyncio.to_thread(_list)

    async def list_hosts(self) -> list[DeviceInfo]:
        """List all ESXi hosts."""
        si = self._ensure_connected()

        def _list() -> list[DeviceInfo]:
            container = si.content.viewManager.CreateContainerView(
                si.content.rootFolder, [vim.HostSystem], True
            )
            try:
                return [_host_to_device_info(h) for h in container.view]
            finally:
                container.Destroy()

        return await asyncio.to_thread(_list)

    async def get_vm_status(self, vm_id: str) -> DeviceInfo:
        """Get the status of a single VM by MOID."""
        si = self._ensure_connected()

        def _get() -> DeviceInfo:
            vm = self._find_vm_by_id(si, vm_id)
            return _vm_to_device_info(vm)

        return await asyncio.to_thread(_get)

    async def power_on(self, vm_id: str) -> bool:
        """Power on a VM."""
        si = self._ensure_connected()

        def _power_on() -> bool:
            vm = self._find_vm_by_id(si, vm_id)
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                logger.info("vm_already_powered_on", vm_id=vm_id)
                return True
            task = vm.PowerOnVM_Task()
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(0.5)
            if task.info.state == vim.TaskInfo.State.success:
                return True
            raise OperationFailedError(f"Power-on failed: {task.info.error}")

        return await asyncio.to_thread(_power_on)

    async def power_off(self, vm_id: str, graceful: bool = True) -> bool:
        """Power off a VM."""
        si = self._ensure_connected()

        def _power_off() -> bool:
            vm = self._find_vm_by_id(si, vm_id)
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                logger.info("vm_already_powered_off", vm_id=vm_id)
                return True
            if graceful:
                try:
                    vm.ShutdownGuest()
                    for _ in range(60):
                        time.sleep(1)
                        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                            return True
                    logger.warning("graceful_shutdown_timeout", vm_id=vm_id)
                except Exception:
                    logger.warning("graceful_shutdown_failed", vm_id=vm_id)
            task = vm.PowerOffVM_Task()
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(0.5)
            if task.info.state == vim.TaskInfo.State.success:
                return True
            raise OperationFailedError(f"Power-off failed: {task.info.error}")

        return await asyncio.to_thread(_power_off)

    async def reboot(self, vm_id: str, graceful: bool = True) -> bool:
        """Reboot a VM."""
        si = self._ensure_connected()

        def _reboot() -> bool:
            vm = self._find_vm_by_id(si, vm_id)
            if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
                raise OperationFailedError(f"VM {vm_id} is not powered on")
            if graceful:
                try:
                    vm.RebootGuest()
                    return True
                except Exception:
                    logger.warning("graceful_reboot_failed", vm_id=vm_id)
            task = vm.ResetVM_Task()
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(0.5)
            if task.info.state == vim.TaskInfo.State.success:
                return True
            raise OperationFailedError(f"Reboot failed: {task.info.error}")

        return await asyncio.to_thread(_reboot)

    async def create_snapshot(self, vm_id: str, name: str, description: str = "") -> str:
        """Create a snapshot and return its MOID."""
        si = self._ensure_connected()

        def _create() -> str:
            vm = self._find_vm_by_id(si, vm_id)
            task = vm.CreateSnapshot_Task(name=name, description=description, memory=False, quiesce=True)
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(0.5)
            if task.info.state == vim.TaskInfo.State.success:
                return str(task.info.result._moId)
            raise OperationFailedError(f"Snapshot creation failed: {task.info.error}")

        return await asyncio.to_thread(_create)

    async def list_snapshots(self, vm_id: str) -> list[dict]:
        """Return a flat list of snapshot dicts for a VM."""
        si = self._ensure_connected()

        def _list() -> list[dict]:
            vm = self._find_vm_by_id(si, vm_id)
            snapshots: list[dict] = []

            def _walk(tree: Any) -> None:
                for snap in tree:
                    snapshots.append({
                        "id": str(snap.snapshot._moId), "name": snap.name,
                        "description": snap.description, "created_at": str(snap.createTime),
                        "state": snap.state, "size_bytes": 0,
                    })
                    if hasattr(snap, "childSnapshotList"):
                        _walk(snap.childSnapshotList)

            if vm.snapshot:
                _walk(vm.snapshot.rootSnapshotList)
            return snapshots

        return await asyncio.to_thread(_list)

    async def revert_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        """Revert to a snapshot by MOID."""
        si = self._ensure_connected()

        def _revert() -> bool:
            vm = self._find_vm_by_id(si, vm_id)

            def _find(tree: Any) -> Any:
                for snap in tree:
                    if str(snap.snapshot._moId) == snapshot_id:
                        return snap.snapshot
                    if hasattr(snap, "childSnapshotList"):
                        found = _find(snap.childSnapshotList)
                        if found is not None:
                            return found
                return None

            if vm.snapshot is None:
                raise NotFoundError(f"No snapshots for VM {vm_id}")
            snap_mor = _find(vm.snapshot.rootSnapshotList)
            if snap_mor is None:
                raise NotFoundError(f"Snapshot {snapshot_id} not found for VM {vm_id}")
            task = snap_mor.RevertToSnapshot_Task()
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(0.5)
            if task.info.state == vim.TaskInfo.State.success:
                return True
            raise OperationFailedError(f"Revert failed: {task.info.error}")

        return await asyncio.to_thread(_revert)

    async def migrate(self, vm_id: str, target_host: str | None = None) -> bool:
        """Perform a vMotion migration."""
        si = self._ensure_connected()

        def _migrate() -> bool:
            vm = self._find_vm_by_id(si, vm_id)
            if target_host:
                container = si.content.viewManager.CreateContainerView(
                    si.content.rootFolder, [vim.HostSystem], True
                )
                try:
                    host_mor = None
                    for h in container.view:
                        if h.name == target_host or str(h._moId) == target_host:
                            host_mor = h
                            break
                finally:
                    container.Destroy()
                if host_mor is None:
                    raise NotFoundError(f"Target host {target_host} not found")
                task = vm.MigrateVM_Task(host=host_mor, priority=vim.VirtualMachine.MovePriority.defaultPriority)
            else:
                relocate_spec = vim.vm.RelocateSpec(priority=vim.VirtualMachine.MovePriority.defaultPriority)
                task = vm.RelocateVM_Task(spec=relocate_spec)
            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(1)
            if task.info.state == vim.TaskInfo.State.success:
                return True
            raise OperationFailedError(f"Migration failed: {task.info.error}")

        return await asyncio.to_thread(_migrate)

    async def get_metrics(self, vm_id: str) -> dict:
        """Fetch real-time performance metrics."""
        si = self._ensure_connected()

        def _metrics() -> dict:
            vm = self._find_vm_by_id(si, vm_id)
            perf_manager = si.content.perfManager
            metric_ids = [
                vim.PerformanceManager.MetricId(counterId=6, instance="*"),
                vim.PerformanceManager.MetricId(counterId=24, instance="*"),
                vim.PerformanceManager.MetricId(counterId=16, instance="*"),
                vim.PerformanceManager.MetricId(counterId=17, instance="*"),
                vim.PerformanceManager.MetricId(counterId=12, instance="*"),
                vim.PerformanceManager.MetricId(counterId=13, instance="*"),
            ]
            spec = vim.PerformanceManager.QuerySpec(entity=vm, metricId=metric_ids, startTime=None, maxSample=1)
            try:
                result = perf_manager.QueryStats(querySpec=[spec])
            except Exception as exc:
                logger.warning("metrics_query_failed", vm_id=vm_id, error=str(exc))
                return {}
            metrics: dict[str, float] = {}
            counter_map = {6: "cpu_usage_pct", 24: "memory_usage_pct", 16: "disk_read_kbps", 17: "disk_write_kbps", 12: "net_rx_kbps", 13: "net_tx_kbps"}
            for entity_metrics in result:
                for series in entity_metrics.value:
                    key = counter_map.get(series.id.counterId)
                    if key and series.value:
                        metrics[key] = series.value[-1]
            return metrics

        return await asyncio.to_thread(_metrics)
