"""Audit logging middleware.

Records ALL incoming requests (GET, POST, PUT, PATCH, DELETE) to the
structured logger. Mutating requests (POST/PUT/PATCH/DELETE) are
additionally persisted to the audit_logs database table for an
immutable compliance trail.

Read-only (GET/HEAD/OPTIONS) requests are logged to the structured
logger for observability but are not persisted to the database to
avoid excessive write volume.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id import request_id_ctx

logger = structlog.get_logger(__name__)

# HTTP methods that trigger database audit persistence (mutable operations).
AUDIT_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# All HTTP methods are logged to structured logger for observability.
ALL_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"})

# Paths excluded from audit logging entirely (health probes, metrics).
_SKIP_PATHS = frozenset({"/health", "/ready", "/health/db", "/health/redis", "/metrics"})

# Path-to-action mapping for structured audit metadata.
_PATH_ACTION_MAP: list[tuple[str, str, str]] = [
    (r"/api/v1/assets", "asset", "assets"),
    (r"/api/v1/operations", "operation", "operations"),
    (r"/api/v1/alerts", "alert", "alerts"),
    (r"/api/v1/chat", "chat", "conversations"),
    (r"/api/v1/conversations", "conversation", "conversations"),
    (r"/api/v1/dashboard", "dashboard", "dashboard"),
    (r"/api/v1/atomics", "atomic", "atomics"),
]

# Extract resource ID from URL path like /api/v1/operations/42.
_RESOURCE_ID_RE = re.compile(r"/api/v1/\w+/(\d+)")


def _extract_action_and_resource(path: str, method: str) -> tuple[str, str | None, str | None]:
    """Derive structured action, resource_type, and resource_id from the request path.

    Args:
        path: The request URL path.
        method: The HTTP method.

    Returns:
        Tuple of (action, resource_type, resource_id).
    """
    resource_type: str | None = None
    resource_id: str | None = None

    for pattern, rtype, _ in _PATH_ACTION_MAP:
        if re.match(pattern, path):
            resource_type = rtype
            break

    id_match = _RESOURCE_ID_RE.search(path)
    if id_match:
        resource_id = id_match.group(1)

    # Build action string like "create_asset", "update_operation", "read_alerts".
    verb_map = {
        "GET": "read",
        "HEAD": "read",
        "OPTIONS": "read",
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }
    verb = verb_map.get(method, method.lower())
    action = f"{verb}_{resource_type}" if resource_type else method.lower()

    return action, resource_type, resource_id



# Sensitive field names to redact from audit logs
_SENSITIVE_FIELDS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "authorization", "credential", "encrypted_password", "private_key",
    "access_token", "refresh_token", "connection_string", "dsn",
})


def _redact_sensitive(body):
    """Redact sensitive fields from a JSON request body string.

    Recursively walks nested dicts and lists to find and redact
    any key whose lowercase name matches _SENSITIVE_FIELDS.
    """
    if not body:
        return body
    try:
        data = json.loads(body)
        _redact_recursive(data)
        return json.dumps(data, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return body


def _redact_recursive(obj):
    """Recursively redact sensitive keys in nested structures."""
    if isinstance(obj, dict):
        for key in obj:
            if key.lower() in _SENSITIVE_FIELDS:
                obj[key] = "[REDACTED]"
            else:
                _redact_recursive(obj[key])
    elif isinstance(obj, list):
        for item in obj:
            _redact_recursive(item)


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs ALL requests to structured logger; persists mutating requests to database.

    Every request gets a structured log entry with method, path, status,
    duration, and user context. Mutable operations (POST/PUT/PATCH/DELETE)
    are additionally written to the audit_logs table for compliance.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip health probes and metrics endpoints entirely.
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.monotonic()
        request_id = request_id_ctx.get("")

        # Read request body for audit on mutating methods (limit to 10KB).
        body_bytes = b""
        if request.method in AUDIT_METHODS:
            try:
                body_bytes = await request.body()
                if len(body_bytes) > 10240:
                    body_bytes = body_bytes[:10240] + b"...[truncated]"
            except Exception as exc:
                logger.warning("audit_body_read_failed", error=str(exc))

        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        # Extract user from request state (set by auth dependency).
        user = getattr(request.state, "user", None)

        # Derive structured metadata.
        action, resource_type, resource_id = _extract_action_and_resource(
            request.url.path, request.method
        )

        # Structured log for ALL requests (read + write).
        logger.info(
            "request_completed",
            request_id=request_id,
            user=user,
            method=request.method,
            path=request.url.path,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status_code=response.status_code,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            duration_ms=duration_ms,
        )

        # Persist mutating requests to database (fire-and-forget).
        if request.method in AUDIT_METHODS:
            try:
                await self._persist_audit_log(
                    request_id=request_id,
                    user=user,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    request_body=_redact_sensitive(body_bytes.decode("utf-8", errors="replace")) if body_bytes else None,
                    duration_ms=duration_ms,
                )
            except Exception:
                # Never let audit persistence break the actual request.
                logger.warning("audit_persist_failed", path=request.url.path)

        return response

    async def _persist_audit_log(
        self,
        *,
        request_id: str,
        user: Any,
        action: str,
        resource_type: str | None,
        resource_id: str | None,
        method: str,
        path: str,
        status_code: int,
        ip_address: str | None,
        user_agent: str | None,
        request_body: str | None,
        duration_ms: int,
    ) -> None:
        """Write an audit log entry to the database.

        Uses a fresh session from the database module to avoid
        interfering with the request's own session.

        Args:
            request_id: Unique request identifier.
            user: Authenticated user identifier.
            action: Structured action name (e.g. "create_asset").
            resource_type: The resource type being acted upon.
            resource_id: The specific resource ID, if applicable.
            method: HTTP method.
            path: Request URL path.
            status_code: HTTP response status code.
            ip_address: Client IP address.
            user_agent: Client user-agent string.
            request_body: Truncated request body.
            duration_ms: Request duration in milliseconds.
        """
        from app.core.database import _get_session_factory
        from app.models.audit_log import AuditLog

        factory = await _get_session_factory()
        async with factory() as session:
            try:
                audit_entry = AuditLog(
                    request_id=request_id,
                    user=str(user) if user else None,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    method=method,
                    path=path,
                    status_code=status_code,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_body=request_body,
                    duration_ms=duration_ms,
                )
                session.add(audit_entry)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
