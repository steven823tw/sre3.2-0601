"""Rate limiting middleware.

Enforces per-client request rate limits using a sliding window counter.
Client identity is derived from the authenticated user or, as a fallback,
the client IP address.

Configuration:
    RATE_LIMIT_PER_MINUTE (int): Max requests per minute per client.
        Set to 0 to disable rate limiting.  Default: 60.
"""
from __future__ import annotations

import time
from collections import defaultdict

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

logger = structlog.get_logger(__name__)

# Paths exempt from rate limiting (health probes, metrics, docs).
_EXEMPT_PATHS = frozenset({
    "/health", "/ready", "/health/db", "/health/redis",
    "/metrics", "/docs", "/redoc", "/openapi.json",
})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter keyed on user or IP."""

    def __init__(self, app, max_per_minute: int = 0) -> None:  # noqa: ANN001
        super().__init__(app)
        self._max = max_per_minute
        # {client_key: [timestamp, ...]}
        self._windows: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._max <= 0 or request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        client_key = self._identify(request)
        now = time.monotonic()
        window = self._windows[client_key]

        # Prune entries older than 60 seconds.
        cutoff = now - 60.0
        while window and window[0] < cutoff:
            window.pop(0)

        if len(window) >= self._max:
            logger.warning("rate_limit_exceeded", client=client_key, count=len(window))
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Rate limit exceeded. Max {self._max} requests per minute.",
                    },
                },
            )

        window.append(now)
        return await call_next(request)

    @staticmethod
    def _identify(request: Request) -> str:
        """Derive a client key from user or IP."""
        user = getattr(request.state, "user", None)
        if user:
            return f"user:{user}"
        client = request.client
        return f"ip:{client.host if client else 'unknown'}"
