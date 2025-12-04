"""Rate limiting middleware using in-memory storage.

For production with multiple instances, use Redis-based rate limiting.
"""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests older than the window."""
        now = time.time()
        cutoff = now - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]

    def is_allowed(self, key: str) -> tuple[bool, dict[str, int]]:
        """Check if request is allowed and return remaining limits.

        Args:
            key: Identifier for the client (IP or user ID)

        Returns:
            Tuple of (is_allowed, headers_dict)
        """
        now = time.time()

        # Clean old requests
        self._clean_old_requests(key, 3600)  # Keep last hour

        requests = self._requests[key]

        # Count requests in last minute
        minute_ago = now - 60
        requests_last_minute = sum(1 for ts in requests if ts > minute_ago)

        # Count requests in last hour
        requests_last_hour = len(requests)

        # Check limits
        if requests_last_minute >= self.config.requests_per_minute:
            return False, {
                "X-RateLimit-Limit": str(self.config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(minute_ago + 60)),
            }

        if requests_last_hour >= self.config.requests_per_hour:
            return False, {
                "X-RateLimit-Limit": str(self.config.requests_per_hour),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now - 3600 + 3600)),
            }

        # Record this request
        self._requests[key].append(now)

        return True, {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(
                self.config.requests_per_minute - requests_last_minute - 1
            ),
            "X-RateLimit-Reset": str(int(minute_ago + 60)),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        config: RateLimitConfig | None = None,
        key_func: Callable[[Request], str] | None = None,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(config)
        self.key_func = key_func or self._default_key_func
        self.exclude_paths = exclude_paths or ["/api/v1/health", "/docs", "/openapi.json"]

    def _default_key_func(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get real IP from forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and apply rate limiting."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get client key
        key = self.key_func(request)

        # Check rate limit
        is_allowed, headers = self.limiter.is_allowed(key)

        if not is_allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60,
                },
            )
            for header_name, header_value in headers.items():
                response.headers[header_name] = header_value
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response
