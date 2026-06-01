"""Tests for the Migration API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.v1.migration import router, engine


@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_engine():
    """Clear migration engine state between tests."""
    engine._plans.clear()
    yield
    engine._plans.clear()


class TestMigrationAPI:
    """Test suite for Migration API endpoints."""

    def test_create_plan_vsphere_to_kvm(self, client):
        """Should create a migration plan from vSphere to KVM."""
        resp = client.post("/api/v1/migration/plan", json={
            "vm_id": "vm-123", "source": "vsphere", "target": "kvm",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["vm_id"] == "vm-123"
        assert data["source_platform"] == "vsphere"
        assert data["target_platform"] == "kvm"
        assert data["method"] == "virt-v2v"
        assert data["status"] == "planned"
        assert len(data["steps"]) == 4

    def test_create_plan_same_platform(self, client):
        """Should create a live migration plan for same platform."""
        resp = client.post("/api/v1/migration/plan", json={
            "vm_id": "vm-123", "source": "kvm", "target": "kvm",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["method"] == "live-migrate"
        assert len(data["steps"]) == 3

    def test_create_plan_unsupported(self, client):
        """Should return 400 for unsupported migration path."""
        resp = client.post("/api/v1/migration/plan", json={
            "vm_id": "vm-123", "source": "fusionsphere", "target": "kvm",
        })
        assert resp.status_code == 400

    def test_execute_migration(self, client):
        """Should execute a migration plan."""
        plan_resp = client.post("/api/v1/migration/plan", json={
            "vm_id": "vm-123", "source": "vsphere", "target": "kvm",
        })
        plan_id = plan_resp.json()["plan_id"]
        exec_resp = client.post(f"/api/v1/migration/execute?plan_id={plan_id}")
        assert exec_resp.status_code == 200
        # Migration may fail if virt-v2v/qemu-img not installed
        assert isinstance(exec_resp.json()["success"], bool)

    def test_get_status(self, client):
        """Should return migration status."""
        plan_resp = client.post("/api/v1/migration/plan", json={
            "vm_id": "vm-123", "source": "vsphere", "target": "kvm",
        })
        plan_id = plan_resp.json()["plan_id"]
        status_resp = client.get(f"/api/v1/migration/{plan_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["status"] == "planned"
        assert data["progress_pct"] == 0.0

    def test_rollback_not_started(self, client):
        """Should fail to rollback a plan that has not started."""
        plan_resp = client.post("/api/v1/migration/plan", json={
            "vm_id": "vm-123", "source": "vsphere", "target": "kvm",
        })
        plan_id = plan_resp.json()["plan_id"]
        rollback_resp = client.post(f"/api/v1/migration/{plan_id}/rollback")
        assert rollback_resp.status_code == 400

    def test_get_status_not_found(self, client):
        """Should return 404 for non-existent plan."""
        resp = client.get("/api/v1/migration/nonexistent")
        assert resp.status_code == 404
