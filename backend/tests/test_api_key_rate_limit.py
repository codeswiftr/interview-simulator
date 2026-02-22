"""Tests for API key rate limiting middleware."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers

from app.middleware.api_key_rate_limit import APIKeyRateLimitMiddleware


class TestAPIKeyRateLimitMiddleware:
    """Tests for APIKeyRateLimitMiddleware."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create middleware instance."""
        return APIKeyRateLimitMiddleware(mock_app)

    def test_initialization(self, middleware, mock_app):
        """Test middleware initializes with empty request tracking."""
        assert middleware.app == mock_app
        assert middleware._requests == {}

    def test_clean_old_requests(self, middleware):
        """Test removing old requests from sliding window."""
        now = time.time()
        middleware._requests["test_key"] = [
            now - 120,  # 2 minutes ago - should be removed
            now - 30,   # 30 seconds ago - should be kept
            now,        # now - should be kept
        ]

        middleware._clean_old_requests("test_key", 60)

        # Only 2 requests should remain (30 seconds ago and now)
        assert len(middleware._requests["test_key"]) == 2

    def test_is_rate_limited_when_under_limit(self, middleware):
        """Test returns False when under rate limit."""
        now = time.time()
        middleware._requests["test_key"] = [
            now - 10,
            now - 5,
        ]

        result = middleware._is_rate_limited("test_key", 5)

        assert result is False

    def test_is_rate_limited_when_at_limit(self, middleware):
        """Test returns True when at rate limit."""
        now = time.time()
        middleware._requests["test_key"] = [
            now - 50,
            now - 40,
            now - 30,
            now - 20,
            now - 10,
        ]

        result = middleware._is_rate_limited("test_key", 5)

        assert result is True

    def test_record_request(self, middleware):
        """Test recording a new request."""
        middleware._record_request("test_key")

        assert len(middleware._requests["test_key"]) == 1
        # Timestamp should be recent
        assert time.time() - middleware._requests["test_key"][0] < 1

    @pytest.mark.asyncio
    async def test_dispatch_allows_request_without_auth_header(self, middleware, mock_app):
        """Test allows request when no Authorization header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"host": "localhost"})
        mock_request.url = MagicMock()
        mock_request.url.path = "/health"
        mock_request.method = "GET"

        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_allows_request_with_non_bearer_auth(self, middleware):
        """Test allows request when Authorization is not Bearer."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"authorization": "Basic dXNlcjpwass"})
        mock_request.url = MagicMock()
        mock_request.url.path = "/health"

        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_dispatch_allows_request_with_non_api_key_token(self, middleware):
        """Test allows request when token doesn't start with 'is_'."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"authorization": "Bearer jwt_token_here"})
        mock_request.url = MagicMock()
        mock_request.url.path = "/health"

        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_call_next.return_value = mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
