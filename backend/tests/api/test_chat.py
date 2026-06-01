"""Tests for Chat API endpoint."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_diagnose_intent(client: AsyncClient):
    """Chinese diagnostic message returns diagnose intent with recommendations."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "web-01 连接超时了"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["intent"] == "diagnose"
    assert len(data["recommendations"]) >= 1
    assert data["recommendations"][0]["action"] == "infra.ping"


@pytest.mark.asyncio
async def test_chat_restart_intent(client: AsyncClient):
    """Restart message returns restart intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "重启 web-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "restart"
    assert any(r["action"] == "compute.vm_restart" for r in data["recommendations"])


@pytest.mark.asyncio
async def test_chat_shutdown_intent(client: AsyncClient):
    """Shutdown message returns shutdown intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "关机 db-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "shutdown"


@pytest.mark.asyncio
async def test_chat_power_on_intent(client: AsyncClient):
    """Power on message returns power_on intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "启动 web-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "power_on"


@pytest.mark.asyncio
async def test_chat_snapshot_intent(client: AsyncClient):
    """Snapshot message returns snapshot intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "创建 web-01 快照"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "snapshot"


@pytest.mark.asyncio
async def test_chat_check_alerts_intent(client: AsyncClient):
    """Check alerts message returns check_alerts intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "查看告警"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "check_alerts"


@pytest.mark.asyncio
async def test_chat_check_resources_intent(client: AsyncClient):
    """Check resources message returns check_resources intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "看看集群"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "check_resources"


@pytest.mark.asyncio
async def test_chat_help_intent(client: AsyncClient):
    """Help message returns help intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "帮助"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "help"
    assert "Engineer Assist" in data["message"]


@pytest.mark.asyncio
async def test_chat_general_fallback(client: AsyncClient):
    """Unrecognized message returns general intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "hello world"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "general"


@pytest.mark.asyncio
async def test_chat_empty_message_rejected(client: AsyncClient):
    """Empty message is rejected by validation."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_network_check_intent(client: AsyncClient):
    """Network check message returns network_check intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "web-01 ping不通"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "diagnose"


@pytest.mark.asyncio
async def test_chat_disk_usage_intent(client: AsyncClient):
    """Disk usage message returns disk_usage intent."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "db-01 磁盘空间不足"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "disk_usage"
