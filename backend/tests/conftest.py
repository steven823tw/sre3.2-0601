"""Shared test fixtures.

Provides an in-memory SQLite database for testing and a FastAPI test client.
"""
from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base

# Set test environment BEFORE importing app
os.environ["APP_ENV"] = "development"
os.environ["DEV_DEFAULT_USER"] = "test-user"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"  # Disable rate limiting in tests

# Use aiosqlite for in-memory async SQLite testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing API endpoints.

    Overrides the database dependency to use the test database.
    """
    from app.core.database import get_db
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_assets(db_session: AsyncSession):
    """Seed the test database with sample assets."""
    from app.models.asset import Asset, AssetStatus, AssetType, Platform

    assets = [
        Asset(
            name="web-01",
            asset_type=AssetType.VM,
            platform=Platform.VSPHERE,
            status=AssetStatus.RUNNING,
            ip_address="10.0.1.51",
            hostname="web-01",
            environment="production",
        ),
        Asset(
            name="db-01",
            asset_type=AssetType.DATABASE,
            platform=Platform.VSPHERE,
            status=AssetStatus.RUNNING,
            ip_address="10.0.1.52",
            hostname="db-01",
            environment="production",
        ),
        Asset(
            name="esxi-01",
            asset_type=AssetType.HOST,
            platform=Platform.VSPHERE,
            status=AssetStatus.RUNNING,
            ip_address="10.0.1.10",
            hostname="esxi-01",
        ),
    ]
    for asset in assets:
        db_session.add(asset)
    await db_session.flush()
    return assets


@pytest_asyncio.fixture
async def seed_alerts(db_session: AsyncSession, seed_assets):
    """Seed the test database with sample alerts."""
    from app.models.alert import Alert, AlertSeverity, AlertStatus

    alerts = [
        Alert(
            title="CPU usage > 90% on web-01",
            severity=AlertSeverity.P1,
            status=AlertStatus.ACTIVE,
            source="prometheus",
            asset_id=seed_assets[0].id,
            metric_name="cpu_usage",
            metric_value="92%",
            threshold="90%",
        ),
        Alert(
            title="Disk space low on db-01",
            severity=AlertSeverity.P2,
            status=AlertStatus.ACTIVE,
            source="prometheus",
            asset_id=seed_assets[1].id,
            metric_name="disk_free",
            metric_value="5%",
            threshold="10%",
        ),
    ]
    for alert in alerts:
        db_session.add(alert)
    await db_session.flush()
    return alerts
