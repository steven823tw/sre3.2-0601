"""Tests for the FusionSphere platform adapter."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.platforms.base import (
    AdapterError, AuthenticationError, AdapterConnectionError,
    ConnectionTestResult, DeviceInfo, NotFoundError, OperationFailedError,
    PlatformConfig, PlatformType,
)


@pytest.fixture
def config() -> PlatformConfig:
    return PlatformConfig(
        platform_type=PlatformType.FUSIONSPHERE,
        host="fusion.example.com",
        port=7443,
        username="admin",
        password="secret",
        verify_ssl=False,
    )


@pytest.fixture
def mock_client():
    """Create a mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.headers = {}
    return client


class TestFusionSphereAdapter:
    """Test suite for FusionSphereAdapter."""

    @pytest.mark.asyncio
    async def test_connect_success(self, config):
        """Should authenticate and get token."""
        from app.platforms.fusionsphere.adapter import FusionSphereAdapter
        adapter = FusionSphereAdapter()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"token": "test-token-123"}
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.headers = {}
            mock_instance.post.return_value = mock_resp
            mock_cls.return_value = mock_instance
            result = await adapter.connect(config)
            assert result is True
            assert adapter._token == "test-token-123"

    @pytest.mark.asyncio
    async def test_connect_auth_failure(self, config):
        """Should raise AuthenticationError for invalid credentials."""
        from app.platforms.fusionsphere.adapter import FusionSphereAdapter
        adapter = FusionSphereAdapter()
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.headers = {}
            mock_instance.post.return_value = mock_resp
            mock_cls.return_value = mock_instance
            with pytest.raises(AuthenticationError):
                await adapter.connect(config)

    @pytest.mark.asyncio
    async def test_list_vms(self):
        """Should list all VMs."""
        from app.platforms.fusionsphere.adapter import FusionSphereAdapter
        adapter = FusionSphereAdapter()
        adapter._connected = True
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "vms": [
                {"vmId": "vm-1", "name": "test-vm", "status": 1, "cpuNum": 4, "memory": 4 * 1024 * 1024 * 1024},
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        adapter._client = mock_client
        vms = await adapter.list_vms()
        assert len(vms) == 1
        assert vms[0].name == "test-vm"
        assert vms[0].status == "running"

    @pytest.mark.asyncio
    async def test_power_on(self):
        """Should power on a VM."""
        from app.platforms.fusionsphere.adapter import FusionSphereAdapter
        adapter = FusionSphereAdapter()
        adapter._connected = True
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        adapter._client = mock_client
        result = await adapter.power_on("vm-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_not_found(self):
        """Should raise NotFoundError for non-existent VM."""
        from app.platforms.fusionsphere.adapter import FusionSphereAdapter
        adapter = FusionSphereAdapter()
        adapter._connected = True
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        adapter._client = mock_client
        with pytest.raises(NotFoundError):
            await adapter.get_vm_status("nonexistent")
