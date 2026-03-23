"""Rate limiting for Stripe webhook endpoint.

Protects the webhook endpoint from abuse — Stripe sends at most a few events
per second in normal operation. Limit to 60 requests/minute per source IP.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class WebhookRateLimiter:
    """In-memory sliding window rate limiter for webhook endpoint."""

    def __init__(self, requests_per_minute: int = 60, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, trusting Cloudflare headers if present."""
        cf_ray = request.headers.get("CF-RAY")
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ray and cf_ip:
            return cf_ip
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[-1].strip()
        return request.client.host if request.client else "unknown"

    async def __call__(self, request: Request) -> None:
        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - self.window_seconds

        # Purge timestamps outside the window
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]

        if len(self._requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many webhook requests",
            )

        self._requests[client_ip].append(now)


webhook_rate_limit = WebhookRateLimiter(requests_per_minute=60)
