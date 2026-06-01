"""Tests for the Platform API endpoints.

Uses the async test client and database fixtures from conftest.py.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.fixture
def platform_payload():
    """Sample platform creation payload."""
    return {
        "name": "Test vSphere",
        "platform_type": "vsphere",
        "host": "vcenter.example.com",
        "port": 443,
        "username": "admin",
        "password": "secret",
    }


class TestPlatformAPI:
    """Test suite for Platform API endpoints."""

    @pytest.mark.asyncio
    async def test_list_platforms_empty(self, client: AsyncClient):
        """Should return empty list when no platforms configured."""
        resp = await client.get("/api/v1/platforms/")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_create_platform(self, client: AsyncClient, platform_payload):
        """Should create a new platform."""
        resp = await client.post("/api/v1/platforms/", json=platform_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test vSphere"
        assert data["platform_type"] == "vsphere"
        assert data["host"] == "vcenter.example.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_and_get(self, client: AsyncClient, platform_payload):
        """Should create and retrieve a platform."""
        create_resp = await client.post("/api/v1/platforms/", json=platform_payload)
        assert create_resp.status_code == 201
        p_id = create_resp.json()["id"]
        get_resp = await client.get(f"/api/v1/platforms/{p_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == p_id

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent platform."""
        resp = await client.get("/api/v1/platforms/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_platform(self, client: AsyncClient, platform_payload):
        """Should update a platform."""
        create_resp = await client.post("/api/v1/platforms/", json=platform_payload)
        assert create_resp.status_code == 201
        p_id = create_resp.json()["id"]
        update_resp = await client.put(f"/api/v1/platforms/{p_id}", json={"name": "Updated"})
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_platform(self, client: AsyncClient, platform_payload):
        """Should delete a platform."""
        create_resp = await client.post("/api/v1/platforms/", json=platform_payload)
        assert create_resp.status_code == 201
        p_id = create_resp.json()["id"]
        del_resp = await client.delete(f"/api/v1/platforms/{p_id}")
        assert del_resp.status_code == 204
        get_resp = await client.get(f"/api/v1/platforms/{p_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client: AsyncClient):
        """Should return 404 when deleting non-existent platform."""
        resp = await client.delete("/api/v1/platforms/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_devices_empty(self, client: AsyncClient, platform_payload):
        """Should return empty device list before sync."""
        create_resp = await client.post("/api/v1/platforms/", json=platform_payload)
        assert create_resp.status_code == 201
        p_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/platforms/{p_id}/devices")
        assert resp.status_code == 200
        assert resp.json() == []
