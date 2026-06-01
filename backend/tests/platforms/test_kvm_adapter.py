"""Tests for the KVM platform adapter."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.platforms.base import (
    AdapterError, ConnectionTestResult, DeviceInfo, NotFoundError, OperationFailedError,
    PlatformConfig, PlatformType,
)

# Try to import libvirt, skip tests if not available
try:
    import libvirt
    HAS_LIBVIRT = True
except ImportError:
    HAS_LIBVIRT = False

pytestmark = pytest.mark.skipif(not HAS_LIBVIRT, reason="libvirt-python not installed")


@pytest.fixture
def config() -> PlatformConfig:
    return PlatformConfig(
        platform_type=PlatformType.KVM,
        host="kvm-host.example.com",
        port=22,
        username="root",
        password="secret",
        extra={"transport": "ssh"},
    )


@pytest.fixture
def mock_conn():
    """Create a mock libvirt connection."""
    conn = MagicMock()
    conn.getHostname.return_value = "kvm-host"
    conn.getLibVersion.return_value = 9000000
    conn.getVersion.return_value = 7000000
    conn.getInfo.return_value = ["x86_64", 32768, 16, 2, 1, 1, 4, 2]
    conn.listDomainsID.return_value = [1, 2]
    conn.listDefinedDomains.return_value = []
    return conn


class TestKVMAdapter:
    """Test suite for KVMAdapter."""

    @pytest.mark.asyncio
    async def test_connect_libvirt_unavailable(self, config):
        """Should raise AdapterError when libvirt is not installed."""
        from app.platforms.kvm.adapter import KVMAdapter
        adapter = KVMAdapter()
        with patch("app.platforms.kvm.adapter._LIBVIRT_AVAILABLE", False):
            with pytest.raises(AdapterError, match="libvirt-python is not installed"):
                await adapter.connect(config)

    @pytest.mark.asyncio
    async def test_connect_success(self, config, mock_conn):
        """Should connect successfully."""
        from app.platforms.kvm.adapter import KVMAdapter
        adapter = KVMAdapter()
        with patch("app.platforms.kvm.adapter._LIBVIRT_AVAILABLE", True):
            with patch("app.platforms.kvm.adapter.libvirt.open", return_value=mock_conn):
                result = await adapter.connect(config)
                assert result is True
                assert adapter._connected is True

    @pytest.mark.asyncio
    async def test_test_connection_success(self, config, mock_conn):
        """Should return version info on successful test."""
        from app.platforms.kvm.adapter import KVMAdapter
        adapter = KVMAdapter()
        adapter._conn = mock_conn
        adapter._connected = True
        result = await adapter.test_connection()
        assert result.success is True
        assert "9.0.0" in result.version
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_list_vms(self, config, mock_conn):
        """Should list all VMs."""
        from app.platforms.kvm.adapter import KVMAdapter
        adapter = KVMAdapter()
        adapter._conn = mock_conn
        adapter._connected = True
        mock_dom = MagicMock()
        mock_dom.name.return_value = "test-vm"
        mock_dom.UUIDString.return_value = "test-uuid"
        mock_dom.state.return_value = (1, 1024)  # running
        mock_dom.info.return_value = [1, 1024, 512, 2, 0]
        mock_dom.interfaceAddresses.return_value = {}
        mock_conn.listDomainsID.return_value = [1]
        mock_conn.lookupByID.return_value = mock_dom
        vms = await adapter.list_vms()
        assert len(vms) >= 1
        assert vms[0].name == "test-vm"
        assert vms[0].status == "running"

    @pytest.mark.asyncio
    async def test_power_on(self, config, mock_conn):
        """Should power on a VM."""
        from app.platforms.kvm.adapter import KVMAdapter
        adapter = KVMAdapter()
        adapter._conn = mock_conn
        adapter._connected = True
        mock_dom = MagicMock()
        mock_dom.state.return_value = (5, 1024)  # shutoff
        mock_conn.lookupByUUIDString.return_value = mock_dom
        result = await adapter.power_on("test-uuid")
        assert result is True
        mock_dom.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_power_off_graceful(self, config, mock_conn):
        """Should gracefully power off a VM."""
        from app.platforms.kvm.adapter import KVMAdapter
        adapter = KVMAdapter()
        adapter._conn = mock_conn
        adapter._connected = True
        mock_dom = MagicMock()
        mock_dom.state.return_value = (1, 1024)  # running
        mock_conn.lookupByUUIDString.return_value = mock_dom
        result = await adapter.power_off("test-uuid", graceful=True)
        assert result is True
        mock_dom.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_found(self, config, mock_conn):
        """Should raise NotFoundError for non-existent VM."""
        from app.platforms.kvm.adapter import KVMAdapter
        import libvirt
        adapter = KVMAdapter()
        adapter._conn = mock_conn
        adapter._connected = True
        mock_conn.lookupByUUIDString.side_effect = libvirt.libvirtError("not found")
        mock_conn.lookupByName.side_effect = libvirt.libvirtError("not found")
        with pytest.raises(NotFoundError):
            await adapter.get_vm_status("nonexistent")
