"""Tests for AlertRepository — count_active and count_by_severity."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.repositories.alert_repo import AlertRepository


@pytest.mark.asyncio
async def test_count_active(db_session: AsyncSession, seed_alerts):
    """count_active returns the number of alerts with ACTIVE status."""
    repo = AlertRepository(db_session)
    count = await repo.count_active()
    assert count == 2


@pytest.mark.asyncio
async def test_count_active_none(db_session: AsyncSession):
    """count_active returns 0 when there are no alerts."""
    repo = AlertRepository(db_session)
    count = await repo.count_active()
    assert count == 0


@pytest.mark.asyncio
async def test_count_active_excludes_resolved(db_session: AsyncSession, seed_assets):
    """count_active excludes resolved alerts."""
    from app.models.asset import Asset

    alerts = [
        Alert(
            title="Active alert",
            severity=AlertSeverity.P1,
            status=AlertStatus.ACTIVE,
            source="prometheus",
            asset_id=seed_assets[0].id,
        ),
        Alert(
            title="Resolved alert",
            severity=AlertSeverity.P2,
            status=AlertStatus.RESOLVED,
            source="prometheus",
            asset_id=seed_assets[0].id,
        ),
        Alert(
            title="Acknowledged alert",
            severity=AlertSeverity.P3,
            status=AlertStatus.ACKNOWLEDGED,
            source="prometheus",
            asset_id=seed_assets[0].id,
        ),
    ]
    for a in alerts:
        db_session.add(a)
    await db_session.flush()

    repo = AlertRepository(db_session)
    assert await repo.count_active() == 1


@pytest.mark.asyncio
async def test_count_by_severity(db_session: AsyncSession, seed_alerts):
    """count_by_severity returns active alert counts grouped by severity."""
    repo = AlertRepository(db_session)
    result = await repo.count_by_severity()
    result_dict = {r["severity"]: r["count"] for r in result}
    assert result_dict["P1"] == 1
    assert result_dict["P2"] == 1


@pytest.mark.asyncio
async def test_count_by_severity_empty(db_session: AsyncSession):
    """count_by_severity returns empty list when no active alerts exist."""
    repo = AlertRepository(db_session)
    result = await repo.count_by_severity()
    assert result == []


@pytest.mark.asyncio
async def test_count_by_severity_excludes_non_active(db_session: AsyncSession, seed_assets):
    """count_by_severity only counts ACTIVE alerts, not acknowledged/resolved."""
    alerts = [
        Alert(
            title="Active P1",
            severity=AlertSeverity.P1,
            status=AlertStatus.ACTIVE,
            source="prometheus",
            asset_id=seed_assets[0].id,
        ),
        Alert(
            title="Resolved P1",
            severity=AlertSeverity.P1,
            status=AlertStatus.RESOLVED,
            source="prometheus",
            asset_id=seed_assets[0].id,
        ),
    ]
    for a in alerts:
        db_session.add(a)
    await db_session.flush()

    repo = AlertRepository(db_session)
    result = await repo.count_by_severity()
    result_dict = {r["severity"]: r["count"] for r in result}
    assert result_dict["P1"] == 1
