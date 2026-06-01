"""
SQLAlchemy 2.0 async engine and session factory.

Uses lazy initialization so tests can override DATABASE_URL before
the engine is created.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

# Lazy-initialized globals
_engine = None
_session_factory = None


def _get_engine():
    """Get or create the async engine (lazy initialization).

    For PostgreSQL, passes pool configuration from settings:
    - pool_size: persistent connections (default 20)
    - max_overflow: extra connections beyond pool_size (default 10)
    - pool_timeout: seconds to wait for a connection (default 30)
    - pool_recycle: seconds before recycling a connection (default 1800)

    For SQLite (testing), uses NullPool with no pool configuration.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.DATABASE_URL
        if not url:
            # For testing, use SQLite in-memory
            url = "sqlite+aiosqlite:///:memory:"
            _engine = create_async_engine(
                url,
                echo=settings.DB_ECHO,
            )
        else:
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            _engine = create_async_engine(
                url,
                echo=settings.DB_ECHO,
                pool_pre_ping=True,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=30,
                pool_recycle=1800,
            )
    return _engine


def _get_session_factory():
    """Get or create the session factory (lazy initialization)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    The session is automatically committed on success and rolled back
    on exception.  Always closed on exit.
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def reset_engine():
    """Reset the engine and session factory (for testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
