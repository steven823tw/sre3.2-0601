"""Request ID tracking middleware.

Assigns a unique request ID to every incoming request and adds it
to the response headers for distributed tracing.
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable for the current request ID, accessible anywhere in the async context
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns and propagates a unique request ID."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use incoming header if present, otherwise generate a new UUID
        req_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request_id_ctx.set(req_id)

        # Store on request state for access in route handlers
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = req_id
        return response
