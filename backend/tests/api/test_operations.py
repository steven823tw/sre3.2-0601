"""Tests for Operation API endpoints.

Covers the operation workflow: create -> approve -> reject.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_operations_empty(client: AsyncClient):
    """Listing operations with no data returns empty list."""
    response = await client.get("/api/v1/operations")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_operation(client: AsyncClient):
    """Creating an operation returns 201 with the created operation."""
    payload = {
        "title": "Diagnose web-01 connectivity",
        "description": "Check why web-01 is unreachable",
        "intent": "diagnose",
        "steps": [
            {
                "step_number": 1,
                "action": "infra.ping",
                "description": "Ping web-01",
                "risk_level": "low",
                "estimated_time_ms": 5000,
            },
            {
                "step_number": 2,
                "action": "compute.vm_status",
                "description": "Check VM status",
                "risk_level": "low",
                "estimated_time_ms": 10000,
            },
        ],
    }
    response = await client.post("/api/v1/operations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Diagnose web-01 connectivity"
    assert data["status"] == "pending"
    assert len(data["steps"]) == 2
    assert data["created_by"] == "test-user"


@pytest.mark.asyncio
async def test_get_operation(client: AsyncClient):
    """Fetching an operation by ID returns the operation with steps."""
    # Create first
    create_resp = await client.post(
        "/api/v1/operations",
        json={"title": "Test operation"},
    )
    op_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/operations/{op_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == op_id
    assert data["title"] == "Test operation"


@pytest.mark.asyncio
async def test_get_operation_not_found(client: AsyncClient):
    """Fetching a non-existent operation returns 404."""
    response = await client.get("/api/v1/operations/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_operation(client: AsyncClient):
    """Approving a pending operation changes its status."""
    create_resp = await client.post(
        "/api/v1/operations",
        json={"title": "Needs approval"},
    )
    op_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/operations/{op_id}/approve",
        json={"notes": "Approved for testing"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == "test-user"
    assert data["approved_at"] is not None


@pytest.mark.asyncio
async def test_reject_operation(client: AsyncClient):
    """Rejecting a pending operation changes its status and records reason."""
    create_resp = await client.post(
        "/api/v1/operations",
        json={"title": "Will be rejected"},
    )
    op_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/operations/{op_id}/reject",
        json={"reason": "Not needed at this time"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert "Not needed" in data["result_summary"]


@pytest.mark.asyncio
async def test_approve_already_approved(client: AsyncClient):
    """Approving an already approved operation returns 409."""
    create_resp = await client.post(
        "/api/v1/operations",
        json={"title": "Double approve test"},
    )
    op_id = create_resp.json()["id"]

    # First approve
    await client.put(f"/api/v1/operations/{op_id}/approve", json={})

    # Second approve should fail
    response = await client.put(f"/api/v1/operations/{op_id}/approve", json={})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_operations_filter_by_status(client: AsyncClient):
    """Filtering operations by status returns matching operations."""
    # Create one pending
    await client.post(
        "/api/v1/operations",
        json={"title": "Pending op"},
    )

    response = await client.get("/api/v1/operations?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["status"] == "pending" for item in data["items"])
