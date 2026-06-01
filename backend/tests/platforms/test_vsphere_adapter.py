"""Tests for the vSphere platform adapter."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.platforms.base import (
    AdapterError, AuthenticationError, ConnectionError,
    ConnectionTestResult, DeviceInfo, NotFoundError, OperationFailedError,
    PlatformConfig, PlatformType,
)


@pytest.fixture
def config() -> PlatformConfig:
    return PlatformConfig(
        platform_type=PlatformType.VSPHERE,
        host="vcenter.example.com",
        port=443,
        username="admin@vsphere.local",
        password="secret",
        verify_ssl=False,
    )


@pytest.fixture
def mock_si():
    """Create a mock vSphere ServiceInstance."""
    si = MagicMock()
    si.content.about.version = "7.0.3"
    si.content.about.build = "20012146"
    si.content.about.apiType = "VirtualCenter"
    si.content.about.apiVersion = "7.0"
    si.content.about.osType = "linux-x64"
    si.content.about.instanceUuid = "test-uuid"
    si.content.about.licenseProductName = "vCenter Server"
    return si


class TestVSphereAdapter:
    """Test suite for VSphereAdapter."""

    @pytest.mark.asyncio
    async def test_connect_pyvmomi_unavailable(self):
        """Should raise AdapterError when pyVmomi is not installed."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        with patch("app.platforms.vsphere.adapter._PYVMOMI_AVAILABLE", False):
            with pytest.raises(AdapterError, match="pyVmomi is not installed"):
                await adapter.connect(config)

    @pytest.mark.asyncio
    async def test_connect_success(self, config, mock_si):
        """Should connect successfully with valid credentials."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        with patch("app.platforms.vsphere.adapter._PYVMOMI_AVAILABLE", True):
            with patch("app.platforms.vsphere.adapter.SmartConnect", return_value=mock_si):
                result = await adapter.connect(config)
                assert result is True
                assert adapter._connected is True

    @pytest.mark.asyncio
    async def test_connect_invalid_login(self, config):
        """Should raise AuthenticationError for invalid credentials."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        with patch("app.platforms.vsphere.adapter._PYVMOMI_AVAILABLE", True):
            with patch("app.platforms.vsphere.adapter.SmartConnect", side_effect=Exception("Invalid login")):
                with pytest.raises(ConnectionError):
                    await adapter.connect(config)

    @pytest.mark.asyncio
    async def test_disconnect(self, config, mock_si):
        """Should disconnect cleanly."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        adapter._si = mock_si
        adapter._connected = True
        with patch("app.platforms.vsphere.adapter.Disconnect"):
            await adapter.disconnect()
            assert adapter._connected is False
            assert adapter._si is None

    @pytest.mark.asyncio
    async def test_test_connection_success(self, config, mock_si):
        """Should return version info on successful connection test."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        adapter._si = mock_si
        adapter._connected = True
        result = await adapter.test_connection()
        assert result.success is True
        assert result.version == "7.0.3"
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_test_connection_not_connected(self):
        """Should return failure when not connected."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        result = await adapter.test_connection()
        assert result.success is False
        assert result.error == "Not connected"

    @pytest.mark.asyncio
    async def test_list_vms_not_connected(self):
        """Should raise AdapterError when not connected."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        with pytest.raises(AdapterError, match="Not connected"):
            await adapter.list_vms()

    @pytest.mark.asyncio
    async def test_power_on_not_found(self, mock_si):
        """Should raise NotFoundError for non-existent VM."""
        from app.platforms.vsphere.adapter import VSphereAdapter
        adapter = VSphereAdapter()
        adapter._si = mock_si
        adapter._connected = True
        mock_container = MagicMock()
        mock_container.view = []
        mock_si.content.viewManager.CreateContainerView.return_value = mock_container
        with pytest.raises(NotFoundError):
            await adapter.power_on("vm-999")
