"""Unit tests for SecurityHeadersMiddleware without DB dependencies."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.security_headers import SecurityHeadersMiddleware


def make_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_security_headers_production_mode():
    app = FastAPI()
    middleware = SecurityHeadersMiddleware(app)

    async def call_next(request: Request) -> Response:
        return Response("ok")

    with patch("app.config.settings.debug", False):
        response = await middleware.dispatch(make_request(), call_next)

    assert "Content-Security-Policy" in response.headers
    assert (
        response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
    )
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers


@pytest.mark.asyncio
async def test_security_headers_debug_mode():
    app = FastAPI()
    middleware = SecurityHeadersMiddleware(app)

    async def call_next(request: Request) -> Response:
        return Response("ok")

    with patch("app.config.settings.debug", True):
        response = await middleware.dispatch(make_request(), call_next)

    assert "Content-Security-Policy" not in response.headers
    assert "Strict-Transport-Security" not in response.headers
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers
