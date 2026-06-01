"""Tests for health, readiness, and dependency probe endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Liveness probe returns 200 with healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Readiness probe returns a response with dependency checks.

    With an in-memory SQLite database the database check should pass.
    Redis may be unavailable in CI, so we accept both ready and degraded.
    """
    response = await client.get("/ready")
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ready", "degraded")
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]


@pytest.mark.asyncio
async def test_database_health(client: AsyncClient):
    """Database health endpoint returns 200 with latency measurement.

    Uses the in-memory SQLite test database which should be healthy.
    """
    response = await client.get("/health/db")
    data = response.json()
    assert data["status"] == "healthy"
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], (int, float))


@pytest.mark.asyncio
async def test_redis_health(client: AsyncClient):
    """Redis health endpoint returns a status.

    Redis may not be available in the test environment, so we accept
    any valid status: healthy, unhealthy, or not_configured.
    """
    response = await client.get("/health/redis")
    data = response.json()
    assert data["status"] in ("healthy", "unhealthy", "not_configured")
    assert "latency_ms" in data
