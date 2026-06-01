"""Main API router.

Registers all v1 sub-routers under the configured API prefix.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import alerts, atomics, assets, chat, dashboard, health, migration, operations, platforms

api_router = APIRouter()

api_router.include_router(assets.router, prefix="/v1")
api_router.include_router(alerts.router, prefix="/v1")
api_router.include_router(operations.router, prefix="/v1")
api_router.include_router(chat.router, prefix="/v1")
api_router.include_router(dashboard.router, prefix="/v1")
api_router.include_router(atomics.router, prefix="/v1")
api_router.include_router(platforms.router, prefix="/v1")
api_router.include_router(migration.router, prefix="/v1")

health_router = health.router
