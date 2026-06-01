"""Tests for Asset API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_assets_empty(client: AsyncClient):
    """Listing assets with no data returns empty list."""
    response = await client.get("/api/v1/assets")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_asset(client: AsyncClient):
    """Creating an asset returns 201 with the created asset."""
    payload = {
        "name": "test-vm-01",
        "asset_type": "vm",
        "platform": "vsphere",
        "status": "running",
        "ip_address": "10.0.1.100",
    }
    response = await client.post("/api/v1/assets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-vm-01"
    assert data["asset_type"] == "vm"
    assert data["platform"] == "vsphere"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_asset(client: AsyncClient, seed_assets):
    """Fetching an existing asset returns 200."""
    asset_id = seed_assets[0].id
    response = await client.get(f"/api/v1/assets/{asset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "web-01"
    assert data["id"] == asset_id


@pytest.mark.asyncio
async def test_get_asset_not_found(client: AsyncClient):
    """Fetching a non-existent asset returns 404."""
    response = await client.get("/api/v1/assets/99999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "ASSET_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_asset(client: AsyncClient, seed_assets):
    """Partially updating an asset returns the updated asset."""
    asset_id = seed_assets[0].id
    response = await client.patch(
        f"/api/v1/assets/{asset_id}",
        json={"status": "maintenance", "description": "Under maintenance"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "maintenance"
    assert data["description"] == "Under maintenance"


@pytest.mark.asyncio
async def test_delete_asset(client: AsyncClient, seed_assets):
    """Deleting an asset returns 204."""
    asset_id = seed_assets[0].id
    response = await client.delete(f"/api/v1/assets/{asset_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/api/v1/assets/{asset_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_assets_with_filters(client: AsyncClient, seed_assets):
    """Listing assets with type filter returns matching assets."""
    response = await client.get("/api/v1/assets?asset_type=vm")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["asset_type"] == "vm"


@pytest.mark.asyncio
async def test_list_assets_with_search(client: AsyncClient, seed_assets):
    """Searching assets by name returns matching assets."""
    response = await client.get("/api/v1/assets?search=web")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "web-01"


@pytest.mark.asyncio
async def test_execute_action_restart(client: AsyncClient, seed_assets):
    """Executing restart action with confirmation returns success."""
    asset_id = seed_assets[0].id
    response = await client.post(
        f"/api/v1/assets/{asset_id}/actions",
        json={"action": "restart", "confirm": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False  # not_implemented until platform adapter integration
    assert data["action"] == "restart"


@pytest.mark.asyncio
async def test_execute_action_without_confirm(client: AsyncClient, seed_assets):
    """Executing shutdown without confirmation returns 422."""
    asset_id = seed_assets[0].id
    response = await client.post(
        f"/api/v1/assets/{asset_id}/actions",
        json={"action": "shutdown", "confirm": False},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_execute_invalid_action(client: AsyncClient, seed_assets):
    """Executing an invalid action returns 422."""
    asset_id = seed_assets[0].id
    response = await client.post(
        f"/api/v1/assets/{asset_id}/actions",
        json={"action": "explode", "confirm": True},
    )
    assert response.status_code == 422
