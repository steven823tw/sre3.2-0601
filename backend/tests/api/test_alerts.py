"""Tests for Alert API endpoints.

Covers the full alert lifecycle: active -> acknowledged -> resolved.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_alerts_empty(client: AsyncClient):
    """Listing alerts with no data returns empty list."""
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_alerts_with_data(client: AsyncClient, seed_alerts):
    """Listing alerts returns seeded data."""
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_alerts_filter_by_severity(client: AsyncClient, seed_alerts):
    """Filtering by severity returns matching alerts."""
    response = await client.get("/api/v1/alerts?severity=P1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["severity"] == "P1"


@pytest.mark.asyncio
async def test_list_alerts_filter_by_status(client: AsyncClient, seed_alerts):
    """Filtering by status returns matching alerts."""
    response = await client.get("/api/v1/alerts?status=active")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_alert(client: AsyncClient, seed_alerts):
    """Fetching an existing alert returns 200."""
    alert_id = seed_alerts[0].id
    response = await client.get(f"/api/v1/alerts/{alert_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == alert_id
    assert data["title"] == "CPU usage > 90% on web-01"


@pytest.mark.asyncio
async def test_get_alert_not_found(client: AsyncClient):
    """Fetching a non-existent alert returns 404."""
    response = await client.get("/api/v1/alerts/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_acknowledge_alert(client: AsyncClient, seed_alerts):
    """Acknowledging an active alert changes its status."""
    alert_id = seed_alerts[0].id
    response = await client.put(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"notes": "Investigating"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_by"] == "test-user"
    assert data["acknowledged_at"] is not None


@pytest.mark.asyncio
async def test_acknowledge_already_acknowledged(client: AsyncClient, seed_alerts):
    """Acknowledging an already acknowledged alert returns 409."""
    alert_id = seed_alerts[0].id

    # First acknowledge
    await client.put(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"notes": "First ack"},
    )

    # Second acknowledge should fail
    response = await client.put(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"notes": "Second ack"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_resolve_alert(client: AsyncClient, seed_alerts):
    """Resolving an active alert changes its status and records notes."""
    alert_id = seed_alerts[0].id
    response = await client.put(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolution_notes": "Fixed by restarting the service"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_by"] == "test-user"
    assert data["resolved_at"] is not None
    assert data["resolution_notes"] == "Fixed by restarting the service"


@pytest.mark.asyncio
async def test_resolve_without_notes(client: AsyncClient, seed_alerts):
    """Resolving without notes returns 422."""
    alert_id = seed_alerts[0].id
    response = await client.put(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolution_notes": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_resolve_already_resolved(client: AsyncClient, seed_alerts):
    """Resolving an already resolved alert returns 409."""
    alert_id = seed_alerts[0].id

    # First resolve
    await client.put(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolution_notes": "Fixed"},
    )

    # Second resolve should fail
    response = await client.put(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolution_notes": "Fixed again"},
    )
    assert response.status_code == 409
