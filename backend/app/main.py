"""FastAPI application factory.

Creates and configures the FastAPI application with all middleware,
error handlers, and route registrations.

Uses lifespan context manager (FastAPI 0.115+) instead of deprecated
on_event decorators.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.audit import AuditMiddleware
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware


def configure_logging() -> None:
    """Configure structlog for structured JSON logging."""
    settings = get_settings()

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler — startup and shutdown.

    Startup: configure logging, seed operation registry, log application start.
    Shutdown: dispose database engine, log application stop.
    """
    configure_logging()
    logger = structlog.get_logger(__name__)
    settings = get_settings()

    # Store the operation registry on app.state for DI access
    from app.core.registry import registry as _registry
    app.state.registry = _registry

    logger.info(
        "application_starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    yield

    from app.core.database import _engine
    if _engine is not None:
        await _engine.dispose()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    application = FastAPI(
        title=settings.APP_NAME,
        description="SRE Intelligent Operations Platform - Engineer Assist",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Import routers here to avoid circular imports at module level
    from app.api.router import api_router, health_router

    # --- Middleware (order matters: last added = first executed) ---
    application.add_middleware(AuditMiddleware)
    application.add_middleware(RateLimitMiddleware, max_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Error handlers ---
    register_error_handlers(application)

    # --- Routes ---
    # Health probes at root level (/health, /ready)
    application.include_router(health_router)
    # API endpoints under /api prefix
    application.include_router(api_router, prefix="/api")

    return application


# Module-level app instance for uvicorn (created lazily on first import)
app = create_app()
