"""Tests for rate limiting middleware."""
from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


async def _ok(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True})


async def _health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def _make_app(max_per_minute: int = 3) -> Starlette:
    """Create a minimal app with rate limiting."""
    return Starlette(
        routes=[
            Route("/test", _ok),
            Route("/health", _health),
        ],
        middleware=[Middleware(RateLimitMiddleware, max_per_minute=max_per_minute)],
    )


class TestRateLimitMiddleware:
    """Rate limiting enforcement."""

    def test_allows_requests_under_limit(self):
        app = _make_app(max_per_minute=5)
        client = TestClient(app)
        for _ in range(5):
            resp = client.get("/test")
            assert resp.status_code == 200

    def test_blocks_requests_over_limit(self):
        app = _make_app(max_per_minute=3)
        client = TestClient(app)
        for _ in range(3):
            assert client.get("/test").status_code == 200
        resp = client.get("/test")
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "RATE_LIMITED"

    def test_disabled_when_max_is_zero(self):
        app = _make_app(max_per_minute=0)
        client = TestClient(app)
        for _ in range(100):
            assert client.get("/test").status_code == 200

    def test_exempt_paths_not_limited(self):
        """Health probes should bypass rate limiting."""
        app = _make_app(max_per_minute=1)
        client = TestClient(app)
        # Exhaust the limit on /test
        assert client.get("/test").status_code == 200
        assert client.get("/test").status_code == 429
        # /health should still work
        assert client.get("/health").status_code == 200
