"""Health and readiness probes with dependency checks.

Provides liveness, readiness, database, and Redis health endpoints
used by Kubernetes/load balancers and the frontend status bar to
determine service availability.
"""
from __future__ import annotations

import asyncio
import time

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings

router = APIRouter(tags=["Health"])

settings = get_settings()

logger = structlog.get_logger(__name__)


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 if the application process is alive.",
)
async def health_check() -> dict:
    """Liveness probe -- confirms the process is alive.

    Does not check downstream dependencies; used by Kubernetes
    to decide whether to restart the container.
    """
    return {"status": "healthy", "version": settings.APP_VERSION}


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 if the application and its dependencies are ready.",
)
async def readiness_check() -> JSONResponse:
    """Readiness probe -- checks database and Redis connectivity.

    Returns 200 only when all critical dependencies are reachable.
    Kubernetes uses this to decide whether to route traffic.
    """
    checks: dict[str, dict] = {}
    all_healthy = True

    # Check database connectivity.
    db_result = await _check_database()
    checks["database"] = db_result
    if db_result["status"] != "healthy":
        all_healthy = False

    # Check Redis connectivity.
    redis_result = await _check_redis()
    checks["redis"] = redis_result
    if redis_result["status"] != "healthy":
        all_healthy = False

    status_code = 200 if all_healthy else 503
    overall = "ready" if all_healthy else "degraded"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "version": settings.APP_VERSION,
            "checks": checks,
        },
    )


@router.get(
    "/health/db",
    summary="Database health check",
    description="Returns 200 if the database is reachable and responsive.",
)
async def database_health() -> JSONResponse:
    """Dedicated database health endpoint.

    Executes a simple SELECT 1 query and measures latency.
    """
    result = await _check_database()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=result)


@router.get(
    "/health/redis",
    summary="Redis health check",
    description="Returns 200 if Redis is reachable and responsive.",
)
async def redis_health() -> JSONResponse:
    """Dedicated Redis health endpoint.

    Pings the Redis server and measures latency.
    """
    result = await _check_redis()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=result)


async def _check_database() -> dict:
    """Check database connectivity by executing SELECT 1.

    Returns:
        Dict with 'status', 'latency_ms', and optional 'error' keys.
    """
    start = time.monotonic()
    try:
        from app.core.database import _get_session_factory

        factory = await _get_session_factory()
        async with factory() as session:
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))

        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        logger.warning("health_db_failed", error=str(exc), latency_ms=latency_ms)
        return {"status": "unhealthy", "latency_ms": latency_ms, "error": str(exc)}


async def _check_redis() -> dict:
    """Check Redis connectivity by sending a PING command.

    Returns:
        Dict with 'status', 'latency_ms', and optional 'error' keys.
    """
    start = time.monotonic()
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            pong = await asyncio.wait_for(client.ping(), timeout=5.0)
            latency_ms = round((time.monotonic() - start) * 1000, 2)
            return {"status": "healthy", "latency_ms": latency_ms, "pong": pong}
        finally:
            await client.aclose()
    except ImportError:
        # redis package not installed -- treat as not configured.
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return {"status": "not_configured", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        logger.warning("health_redis_failed", error=str(exc), latency_ms=latency_ms)
        return {"status": "unhealthy", "latency_ms": latency_ms, "error": str(exc)}
