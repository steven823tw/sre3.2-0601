"""Shared FastAPI dependencies.

Provides dependency-injected services, repositories, and auth.
"""
from __future__ import annotations

import structlog
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.core.registry import OperationRegistry
from app.core.security import decode_token
from app.services.alert_service import AlertService
from app.services.asset_service import AssetService
from app.services.chat_service import ChatService
from app.services.operation_executor import OperationExecutor
from app.services.operation_service import OperationService
from app.services.platform_service import PlatformService

logger = structlog.get_logger(__name__)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract and validate the current user from the Authorization header.

    Returns the username/subject from the JWT token.

    Security behavior:
    - Production (APP_ENV=production): Always requires valid JWT token
    - Development (APP_ENV=development): Allows dev-user fallback ONLY if
      DEV_DEFAULT_USER is explicitly configured

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    settings = get_settings()

    # No Authorization header provided
    if authorization is None:
        if settings.APP_ENV == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required in production",
            )
        # Development mode: allow dev-user only if explicitly configured
        if settings.DEV_DEFAULT_USER:
            logger.warning("auth_dev_fallback", user=settings.DEV_DEFAULT_USER)
            return settings.DEV_DEFAULT_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
        )

    token = authorization[7:]  # Strip "Bearer " prefix
    try:
        payload = decode_token(token, expected_type="access")
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain a subject claim",
            )
        return str(username)
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {exc}",
        )


def get_chat_service() -> ChatService:
    """Dependency that provides the ChatService singleton.

    The singleton maintains conversation context state across requests.
    """
    from app.services.chat_service import chat_service
    return chat_service


def get_operation_executor() -> OperationExecutor:
    """Dependency that provides the OperationExecutor singleton.

    The singleton tracks running operations across requests.
    """
    from app.services.operation_executor import operation_executor
    return operation_executor


def get_registry(request: Request) -> OperationRegistry:
    """Dependency that provides the OperationRegistry from app state.

    The registry is created and seeded during application lifespan
    and stored on ``app.state.registry``.
    """
    return request.app.state.registry


async def get_asset_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[AssetService, None]:
    """Dependency that provides an AssetService instance."""
    yield AssetService(db)


async def get_alert_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[AlertService, None]:
    """Dependency that provides an AlertService instance."""
    yield AlertService(db)


async def get_operation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    executor: Annotated[OperationExecutor, Depends(get_operation_executor)],
) -> AsyncGenerator[OperationService, None]:
    """Dependency that provides an OperationService instance."""
    yield OperationService(db, executor)


async def get_platform_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[PlatformService, None]:
    """Dependency that provides a PlatformService instance."""
    yield PlatformService(db)


# Type aliases for dependency injection in route handlers
CurrentUser = Annotated[str, Depends(get_current_user)]
AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
OperationServiceDep = Annotated[OperationService, Depends(get_operation_service)]
PlatformServiceDep = Annotated[PlatformService, Depends(get_platform_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
OperationExecutorDep = Annotated[OperationExecutor, Depends(get_operation_executor)]
RegistryDep = Annotated[OperationRegistry, Depends(get_registry)]
