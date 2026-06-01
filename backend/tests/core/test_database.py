"""Tests for app.core.database — engine creation, session management, reset."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import _create_engine, get_db, reset_engine


@pytest.fixture(autouse=True)
def _clean_engine():
    """Reset global engine state before each test."""
    reset_engine()
    yield
    reset_engine()


def _make_mock_settings(**overrides):
    """Create a mock settings object with sensible defaults."""
    defaults = {
        "DATABASE_URL": "",
        "DB_ECHO": False,
        "DB_POOL_SIZE": 5,
        "DB_MAX_OVERFLOW": 2,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def test_create_engine_sqlite_fallback():
    """_create_engine with empty DATABASE_URL falls back to in-memory SQLite."""
    with patch("app.core.database.get_settings", return_value=_make_mock_settings()):
        engine = _create_engine()
        assert "sqlite" in str(engine.url).lower()


def test_create_engine_postgresql_url_conversion():
    """_create_engine converts postgresql:// to postgresql+asyncpg://."""
    with patch(
        "app.core.database.get_settings",
        return_value=_make_mock_settings(
            DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
        ),
    ):
        engine = _create_engine()
        url_str = str(engine.url)
        assert "asyncpg" in url_str
        assert "postgresql+asyncpg://" in url_str


def test_create_engine_asyncpg_url_unchanged():
    """_create_engine does not modify an already-correct asyncpg URL."""
    with patch(
        "app.core.database.get_settings",
        return_value=_make_mock_settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/mydb"
        ),
    ):
        engine = _create_engine()
        url_str = str(engine.url)
        assert url_str.count("asyncpg") == 1  # no double conversion


@pytest.mark.asyncio
async def test_get_db_yields_session():
    """get_db yields an AsyncSession that can execute queries."""
    gen = get_db()
    session = await gen.__anext__()
    try:
        assert isinstance(session, AsyncSession)
        from sqlalchemy import text

        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    finally:
        await gen.aclose()


def test_reset_engine_clears_state():
    """reset_engine sets the internal engine and factory to None."""
    import app.core.database as db_module

    reset_engine()
    assert db_module._engine is None
    assert db_module._session_factory is None


def test_reset_engine_idempotent():
    """Calling reset_engine multiple times does not raise."""
    reset_engine()
    reset_engine()
    reset_engine()
    import app.core.database as db_module

    assert db_module._engine is None
