"""Custom exception hierarchy for the application.

All application-specific exceptions inherit from AppException.
Each exception carries an HTTP status code, error code, and message.
"""
from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base application exception.

    Attributes:
        status_code: HTTP status code to return.
        error_code: Machine-readable error code (e.g. "ASSET_NOT_FOUND").
        message: Human-readable error message.
        details: Optional additional context.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found (404)."""

    def __init__(self, resource: str, resource_id: str | int) -> None:
        super().__init__(
            status_code=404,
            error_code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} with id '{resource_id}' not found",
        )


class ValidationException(AppException):
    """Request validation failed (422)."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class ConflictException(AppException):
    """Resource conflict (409)."""

    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=409,
            error_code="CONFLICT",
            message=message,
        )


class ForbiddenException(AppException):
    """Insufficient permissions (403)."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            status_code=403,
            error_code="FORBIDDEN",
            message=message,
        )


class UnauthorizedException(AppException):
    """Authentication required (401)."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            status_code=401,
            error_code="UNAUTHORIZED",
            message=message,
        )


class OperationFailedException(AppException):
    """An operation failed during execution (500)."""

    def __init__(self, operation: str, reason: str) -> None:
        super().__init__(
            status_code=500,
            error_code="OPERATION_FAILED",
            message=f"Operation '{operation}' failed: {reason}",
        )
