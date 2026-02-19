"""Per-endpoint rate limiting for authentication endpoints.

Provides FastAPI dependencies for rate limiting login (10/min) and
register (5/min) endpoints using in-memory sliding window counters.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class AuthRateLimiter:
    """In-memory sliding window rate limiter for auth endpoints."""

    def __init__(self, requests_per_minute: int, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Trust CF-Connecting-IP if CF-RAY present (Cloudflare)
        cf_ray = request.headers.get("CF-RAY")
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ray and cf_ip:
            return cf_ip

        # Fall back to X-Forwarded-For rightmost or direct IP
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            ips = [ip.strip() for ip in xff.split(",")]
            if len(ips) <= 5:
                return ips[-1]

        return request.client.host if request.client else "0.0.0.0"

    def check(self, request: Request) -> None:
        """Check if request is within rate limit. Raises HTTPException if exceeded."""
        now = time.time()
        client_ip = self._get_client_ip(request)
        cutoff = now - self.window_seconds

        # Clean old entries
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > cutoff
        ]

        if len(self._requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._requests[client_ip].append(now)


# Singleton instances for auth endpoints
_login_limiter = AuthRateLimiter(requests_per_minute=10)
_register_limiter = AuthRateLimiter(requests_per_minute=5)
_forgot_password_limiter = AuthRateLimiter(requests_per_minute=5)


async def login_rate_limit(request: Request) -> None:
    """Rate limit dependency for login: 10 requests/minute per IP."""
    _login_limiter.check(request)


async def register_rate_limit(request: Request) -> None:
    """Rate limit dependency for register: 5 requests/minute per IP."""
    _register_limiter.check(request)


async def forgot_password_rate_limit(request: Request) -> None:
    """Rate limit dependency for forgot-password: 5 requests/minute per IP."""
    _forgot_password_limiter.check(request)
