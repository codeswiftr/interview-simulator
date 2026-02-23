"""API Key rate limiting middleware.

Implements per-key rate limiting based on the key's configured rate limit.
"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class APIKeyRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit API requests based on API key configuration.

    Uses a sliding window algorithm to track requests per API key.
    """

    def __init__(self, app):
        super().__init__(app)
        # Track requests per API key: {key_prefix: [timestamps]}
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old_requests(self, key_prefix: str, window_seconds: int) -> None:
        """Remove requests outside the sliding window.

        Args:
            key_prefix: API key prefix
            window_seconds: Window size in seconds (60 for per-minute limiting)
        """
        cutoff = time.time() - window_seconds
        self._requests[key_prefix] = [
            ts for ts in self._requests[key_prefix] if ts > cutoff
        ]

    def _is_rate_limited(self, key_prefix: str, rate_limit: int) -> bool:
        """Check if the API key has exceeded its rate limit.

        Args:
            key_prefix: API key prefix
            rate_limit: Maximum requests per minute

        Returns:
            True if rate limit exceeded, False otherwise
        """
        window_seconds = 60  # Per-minute rate limiting

        # Clean old requests
        self._clean_old_requests(key_prefix, window_seconds)

        # Check if limit exceeded
        return len(self._requests[key_prefix]) >= rate_limit

    def _record_request(self, key_prefix: str) -> None:
        """Record a new request for the API key.

        Args:
            key_prefix: API key prefix
        """
        self._requests[key_prefix].append(time.time())

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply rate limiting for API keys.

        Args:
            request: The incoming request
            call_next: The next middleware/handler

        Returns:
            The response

        Raises:
            HTTPException 429: If rate limit exceeded
        """
        # Check if request uses API key authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # No API key, skip rate limiting (JWT has its own rate limiting)
            return await call_next(request)

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Check if it's an API key (starts with 'is_')
        if not token.startswith("is_"):
            # Not an API key, skip
            return await call_next(request)

        # Extract key prefix
        key_prefix = token[:8]

        # Get the API key from database to check rate limit
        # This is a simple implementation - for production, consider caching
        from sqlmodel import select

        from app.db import SessionLocal
        from app.models.api_key import APIKey

        async with SessionLocal() as session:
            result = await session.exec(
                select(APIKey).where(
                    APIKey.key_prefix == key_prefix,
                    APIKey.is_active == True,
                )
            )
            api_key = result.first()

            if not api_key:
                # Invalid key - let the auth middleware handle it
                return await call_next(request)

            # Check rate limit
            if self._is_rate_limited(key_prefix, api_key.rate_limit):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {api_key.rate_limit} requests per minute.",
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(api_key.rate_limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            # Record the request
            self._record_request(key_prefix)

            # Add rate limit headers to response
            response = await call_next(request)

            # Calculate remaining requests
            window_seconds = 60
            self._clean_old_requests(key_prefix, window_seconds)
            remaining = max(0, api_key.rate_limit - len(self._requests[key_prefix]))

            response.headers["X-RateLimit-Limit"] = str(api_key.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

            return response
