"""KVM/QEMU platform adapter using libvirt-python.

Connects via qemu+ssh:// URIs.
All libvirt calls are synchronous -- wrapped with asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

from app.platforms.base import (
    AdapterError, AuthenticationError, ConnectionError,
    ConnectionTestResult, DeviceInfo, NotFoundError,
    OperationFailedError, PlatformAdapter, PlatformConfig, PlatformType,
)

logger = structlog.get_logger(__name__)

try:
    import libvirt
    _LIBVIRT_AVAILABLE = True
except ImportError:
    _LIBVIRT_AVAILABLE = False
    logger.warning("libvirt-python not installed -- KVM adapter unavailable")


def _domain_to_device_info(dom: Any) -> DeviceInfo:
    """Convert a libvirt virDomain to DeviceInfo."""
    name = dom.name()
    dom_id = str(dom.UUIDString())
    state, _ = dom.state()
    status_map = {
        libvirt.VIR_DOMAIN_NOSTATE: "unknown",
        libvirt.VIR_DOMAIN_RUNNING: "running",
        libvirt.VIR_DOMAIN_BLOCKED: "blocked",
        libvirt.VIR_DOMAIN_PAUSED: "paused",
        libvirt.VIR_DOMAIN_SHUTDOWN: "shutting_down",
        libvirt.VIR_DOMAIN_SHUTOFF: "stopped",
        libvirt.VIR_DOMAIN_CRASHED: "crashed",
        libvirt.VIR_DOMAIN_PMSUSPENDED: "suspended",
    }
    status = status_map.get(state, "unknown")

    # Try to get IP from lease / interface info
    ip_addr = ""
    try:
        ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE, 0)
        for _, iface in ifaces.items():
            for addr in iface.get("addrs", []):
                if addr.get("type") == 0:  # IPv4
                    ip_addr = addr["addr"]
                    break
            if ip_addr:
                break
    except Exception:
        pass

    # Parse XML for metadata
    info = dom.info()
    metadata: dict[str, Any] = {
        "cpu_count": info[3] if len(info) > 3 else 0,
        "memory_mb": (info[2] // 1024) if len(info) > 2 else 0,
        "max_memory_mb": (info[1] // 1024) if len(info) > 1 else 0,
        "uuid": dom.UUIDString(),
        "autostart": dom.autostart(),
        "persistent": dom.isPersistent(),
    }
    return DeviceInfo(
        id=dom_id, name=name, device_type="vm",
        status=status, ip_address=ip_addr, platform="kvm",
        metadata=metadata,
    )


class KVMAdapter(PlatformAdapter):
    """KVM/QEMU adapter backed by libvirt-python."""

    platform_type = PlatformType.KVM

    def __init__(self) -> None:
        self._conn: Any | None = None
        self._config: PlatformConfig | None = None
        self._connected: bool = False

    def _build_uri(self, config: PlatformConfig) -> str:
        """Build the libvirt connection URI."""
        transport = config.extra.get("transport", "ssh")
        if transport == "ssh":
            return f"qemu+ssh://{config.username}@{config.host}:{config.port}/system"
        elif transport == "tcp":
            return f"qemu+tcp://{config.host}:{config.port}/system"
        elif transport == "tls":
            return f"qemu+tls://{config.host}:{config.port}/system"
        return f"qemu:///system"  # local

    async def connect(self, config: PlatformConfig) -> bool:
        """Open a libvirt connection."""
        if not _LIBVIRT_AVAILABLE:
            raise AdapterError("libvirt-python is not installed")
        self._config = config
        uri = self._build_uri(config)

        def _connect() -> Any:
            try:
                return libvirt.open(uri)
            except libvirt.libvirtError as exc:
                if "authentication" in str(exc).lower():
                    raise AuthenticationError(f"Auth failed for {config.host}: {exc}") from exc
                raise ConnectionError(f"Cannot connect to {config.host}: {exc}") from exc

        try:
            self._conn = await asyncio.to_thread(_connect)
            self._connected = True
            logger.info("kvm_connected", host=config.host, uri=uri)
            return True
        except (AuthenticationError, ConnectionError):
            raise
        except Exception as exc:
            raise ConnectionError(f"Unexpected error: {exc}") from exc

    async def disconnect(self) -> None:
        """Disconnect from libvirt."""
        if self._conn is not None:
            try:
                await asyncio.to_thread(self._conn.close)
            except Exception as exc:
                logger.warning("kvm_disconnect_error", error=str(exc))
            finally:
                self._conn = None
                self._connected = False
                logger.info("kvm_disconnected")

    async def test_connection(self) -> ConnectionTestResult:
        """Test the libvirt connection."""
        if not self._connected or self._conn is None:
            return ConnectionTestResult(success=False, latency_ms=0, version="", error="Not connected")
        try:
            t0 = time.monotonic()

            def _query() -> dict[str, Any]:
                ver = self._conn.getLibVersion()
                hv_ver = self._conn.getVersion()
                hostname = self._conn.getHostname()
                node_info = self._conn.getInfo()
                return {
                    "libvirt_version": f"{ver // 1000000}.{(ver // 1000) % 1000}.{ver % 1000}",
                    "hypervisor_version": str(hv_ver),
                    "hostname": hostname,
                    "model": node_info[0],
                    "memory_mb": node_info[1],
                    "cpu_cores": node_info[2],
                    "cpu_sockets": node_info[3],
                }

            info = await asyncio.to_thread(_query)
            latency = int((time.monotonic() - t0) * 1000)
            return ConnectionTestResult(success=True, latency_ms=latency, version=info["libvirt_version"], details=info)
        except Exception as exc:
            return ConnectionTestResult(success=False, latency_ms=0, version="", error=str(exc))

    def _ensure_connected(self) -> Any:
        """Return the connection or raise."""
        if not self._connected or self._conn is None:
            raise AdapterError("Not connected -- call connect() first")
        return self._conn

    def _find_domain(self, conn: Any, vm_id: str) -> Any:
        """Find a domain by UUID or name."""
        try:
            return conn.lookupByUUIDString(vm_id)
        except libvirt.libvirtError:
            pass
        try:
            return conn.lookupByName(vm_id)
        except libvirt.libvirtError as exc:
            raise NotFoundError(f"VM {vm_id} not found: {exc}") from exc

    async def list_vms(self) -> list[DeviceInfo]:
        """List all virtual machines (running + defined)."""
        conn = self._ensure_connected()

        def _list() -> list[DeviceInfo]:
            domains: list[DeviceInfo] = []
            for dom_id in conn.listDomainsID():
                dom = conn.lookupByID(dom_id)
                domains.append(_domain_to_device_info(dom))
            for name in conn.listDefinedDomains():
                dom = conn.lookupByName(name)
                domains.append(_domain_to_device_info(dom))
            return domains

        return await asyncio.to_thread(_list)

    async def list_hosts(self) -> list[DeviceInfo]:
        """List host info (single node for KVM)."""
        conn = self._ensure_connected()

        def _list() -> list[DeviceInfo]:
            hostname = conn.getHostname()
            node_info = conn.getInfo()
            return [DeviceInfo(
                id=hostname, name=hostname, device_type="host",
                status="connected", ip_address="", platform="kvm",
                metadata={
                    "model": node_info[0], "memory_mb": node_info[1],
                    "cpu_cores": node_info[2], "cpu_sockets": node_info[3],
                },
            )]

        return await asyncio.to_thread(_list)

    async def get_vm_status(self, vm_id: str) -> DeviceInfo:
        """Get VM status."""
        conn = self._ensure_connected()

        def _get() -> DeviceInfo:
            dom = self._find_domain(conn, vm_id)
            return _domain_to_device_info(dom)

        return await asyncio.to_thread(_get)

    async def power_on(self, vm_id: str) -> bool:
        """Power on a VM."""
        conn = self._ensure_connected()

        def _power_on() -> bool:
            dom = self._find_domain(conn, vm_id)
            state, _ = dom.state()
            if state == libvirt.VIR_DOMAIN_RUNNING:
                logger.info("vm_already_running", vm_id=vm_id)
                return True
            try:
                dom.create()
                return True
            except libvirt.libvirtError as exc:
                raise OperationFailedError(f"Power-on failed: {exc}") from exc

        return await asyncio.to_thread(_power_on)

    async def power_off(self, vm_id: str, graceful: bool = True) -> bool:
        """Power off a VM."""
        conn = self._ensure_connected()

        def _power_off() -> bool:
            dom = self._find_domain(conn, vm_id)
            state, _ = dom.state()
            if state == libvirt.VIR_DOMAIN_SHUTOFF:
                logger.info("vm_already_shutoff", vm_id=vm_id)
                return True
            try:
                if graceful:
                    dom.shutdown()
                else:
                    dom.destroy()
                return True
            except libvirt.libvirtError as exc:
                raise OperationFailedError(f"Power-off failed: {exc}") from exc

        return await asyncio.to_thread(_power_off)

    async def reboot(self, vm_id: str, graceful: bool = True) -> bool:
        """Reboot a VM."""
        conn = self._ensure_connected()

        def _reboot() -> bool:
            dom = self._find_domain(conn, vm_id)
            state, _ = dom.state()
            if state != libvirt.VIR_DOMAIN_RUNNING:
                raise OperationFailedError(f"VM {vm_id} is not running")
            try:
                if graceful:
                    dom.reboot()
                else:
                    dom.reset()
                return True
            except libvirt.libvirtError as exc:
                raise OperationFailedError(f"Reboot failed: {exc}") from exc

        return await asyncio.to_thread(_reboot)

    async def create_snapshot(self, vm_id: str, name: str, description: str = "") -> str:
        """Create a snapshot via virDomain.snapshotCreateXML."""
        conn = self._ensure_connected()

        def _create() -> str:
            dom = self._find_domain(conn, vm_id)
            xml = f"<domainsnapshot><name>{name}</name><description>{description}</description></domainsnapshot>"
            try:
                snap = dom.snapshotCreateXML(xml)
                return snap.getName()
            except libvirt.libvirtError as exc:
                raise OperationFailedError(f"Snapshot creation failed: {exc}") from exc

        return await asyncio.to_thread(_create)

    async def list_snapshots(self, vm_id: str) -> list[dict]:
        """List all snapshots for a VM."""
        conn = self._ensure_connected()

        def _list() -> list[dict]:
            dom = self._find_domain(conn, vm_id)
            try:
                snapshots = dom.listAllSnapshotNames()
                result = []
                for snap_name in snapshots:
                    snap = dom.snapshotLookupByName(snap_name)
                    result.append({
                        "id": snap_name, "name": snap_name,
                        "description": "", "created_at": "",
                        "state": "", "size_bytes": 0,
                    })
                return result
            except libvirt.libvirtError as exc:
                logger.warning("list_snapshots_failed", vm_id=vm_id, error=str(exc))
                return []

        return await asyncio.to_thread(_list)

    async def revert_snapshot(self, vm_id: str, snapshot_id: str) -> bool:
        """Revert to a snapshot."""
        conn = self._ensure_connected()

        def _revert() -> bool:
            dom = self._find_domain(conn, vm_id)
            try:
                snap = dom.snapshotLookupByName(snapshot_id)
                dom.revertToSnapshot(snap)
                return True
            except libvirt.libvirtError as exc:
                raise OperationFailedError(f"Revert failed: {exc}") from exc

        return await asyncio.to_thread(_revert)

    async def migrate(self, vm_id: str, target_host: str | None = None) -> bool:
        """Perform live migration to target_host."""
        conn = self._ensure_connected()

        def _migrate() -> bool:
            dom = self._find_domain(conn, vm_id)
            if target_host is None:
                raise OperationFailedError("Target host is required for KVM migration")
            transport = self._config.extra.get("transport", "ssh") if self._config else "ssh"
            uri = f"qemu+{transport}://{target_host}/system"
            try:
                dest_conn = libvirt.open(uri)
                try:
                    new_dom = dom.migrate3(dest_conn, flags=libvirt.VIR_MIGRATE_LIVE)
                    return new_dom is not None
                finally:
                    dest_conn.close()
            except libvirt.libvirtError as exc:
                raise OperationFailedError(f"Migration failed: {exc}") from exc

        return await asyncio.to_thread(_migrate)

    async def get_metrics(self, vm_id: str) -> dict:
        """Fetch basic performance stats for a VM."""
        conn = self._ensure_connected()

        def _metrics() -> dict:
            dom = self._find_domain(conn, vm_id)
            stats: dict[str, float] = {}
            try:
                cpu_stats = dom.getCPUStats(True)
                if cpu_stats:
                    stats["cpu_time_ns"] = float(cpu_stats.get("cpu_time", 0))
                mem_stats = dom.memoryStats()
                if mem_stats:
                    stats["memory_total_mb"] = mem_stats.get("actual", 0) / 1024
                    stats["memory_unused_mb"] = mem_stats.get("unused", 0) / 1024
            except libvirt.libvirtError as exc:
                logger.warning("metrics_failed", vm_id=vm_id, error=str(exc))
            return stats

        return await asyncio.to_thread(_metrics)
