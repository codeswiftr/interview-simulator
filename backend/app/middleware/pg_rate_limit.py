"""PostgreSQL-backed rate limiting middleware.

Replaces the Redis-based ``forge_shared.middleware.RateLimitMiddleware``.
Uses a sliding-window algorithm implemented with a ``rate_limit_events`` table
so no external cache service is required.

Design notes
------------
* Atomic increment via ``INSERT ... ON CONFLICT DO UPDATE SET count = count + 1``
  guarantees correctness under concurrent requests without advisory locks.
* Window key is ``<prefix>:<client_id>:<rounded_window_start_unix>``.  Each row
  represents one minute-window for one client.
* A lightweight background cleanup runs every ``cleanup_interval_seconds``
  inside the middleware to prune rows older than the window.  This keeps the
  table small without a dedicated cron job.
* Falls back to an in-memory limiter if the database insert fails so a DB
  hiccup does not take down the API.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import Request, Response
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory fallback (identical algorithm, no persistence)
# ---------------------------------------------------------------------------


class _MemoryFallback:
    """Sliding-window in-memory fallback used when the DB is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, list[float]] = defaultdict(list)

    def check_and_increment(
        self, key: str, limit: int, window_seconds: int
    ) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds
        bucket = self._store[key]
        # Prune old timestamps
        self._store[key] = [t for t in bucket if t > cutoff]
        count = len(self._store[key])
        if count >= limit:
            return False, 0
        self._store[key].append(now)
        return True, limit - count - 1


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class PgRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware backed by PostgreSQL.

    Parameters
    ----------
    app:
        ASGI application.
    requests_per_minute:
        Maximum requests allowed per minute per client.  Defaults to 60.
    requests_per_hour:
        Maximum requests allowed per hour per client.  Defaults to 1 000.
    exclude_paths:
        URL path prefixes that skip rate limiting entirely.
    cleanup_interval_seconds:
        How often (in seconds) old rows are deleted from ``rate_limit_events``.
        Defaults to 300 (5 minutes).
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        exclude_paths: list[str] | None = None,
        cleanup_interval_seconds: int = 300,
    ) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.exclude_paths: list[str] = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/",
            "/favicon.ico",
            "/static",
        ]
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._fallback = _MemoryFallback()
        self._last_cleanup: float = 0.0

    # ------------------------------------------------------------------
    # Main dispatch
    # ------------------------------------------------------------------

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        client_key = self._client_key(request)

        # Minute-window check
        allowed, remaining = await self._check(client_key, self.requests_per_minute, 60)
        if not allowed:
            return self._too_many(self.requests_per_minute, 60)

        # Hour-window check (only if minute passed)
        allowed_h, remaining_h = await self._check(client_key, self.requests_per_hour, 3600)
        if not allowed_h:
            return self._too_many(self.requests_per_hour, 3600)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        # Periodic cleanup (fire-and-forget, does not block response)
        now = time.time()
        if now - self._last_cleanup > self.cleanup_interval_seconds:
            self._last_cleanup = now
            asyncio.create_task(self._cleanup_old_rows())  # noqa: RUF006

        return response

    # ------------------------------------------------------------------
    # Rate limit check
    # ------------------------------------------------------------------

    async def _check(self, client_key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Atomically increment and check the counter for this window.

        Returns (allowed, remaining).
        """
        # Round down to window boundary for bucketing
        window_start = int(time.time()) // window_seconds * window_seconds
        db_key = f"{client_key}:{window_seconds}:{window_start}"

        try:
            from app.db import engine  # local import to avoid circular deps

            async with engine.begin() as conn:
                # Upsert: insert new row or increment existing one atomically
                await conn.execute(
                    text(
                        """
                        INSERT INTO rate_limit_events (key, window_start, count)
                        VALUES (:key, :window_start, 1)
                        ON CONFLICT (key, window_start)
                        DO UPDATE SET count = rate_limit_events.count + 1
                        """
                    ),
                    {
                        "key": db_key,
                        "window_start": datetime.fromtimestamp(window_start, tz=UTC),
                    },
                )

                result = await conn.execute(
                    text(
                        "SELECT count FROM rate_limit_events "
                        "WHERE key = :key AND window_start = :window_start"
                    ),
                    {
                        "key": db_key,
                        "window_start": datetime.fromtimestamp(window_start, tz=UTC),
                    },
                )
                row = result.fetchone()
                count: int = row[0] if row else 1

            if count > limit:
                return False, 0
            return True, max(0, limit - count)

        except Exception as exc:
            logger.warning("PgRateLimitMiddleware DB error, using in-memory fallback: %s", exc)
            return self._fallback.check_and_increment(db_key, limit, window_seconds)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _client_key(self, request: Request) -> str:
        """Derive a stable, privacy-safe key for this client."""
        # Prefer API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            raw = f"apikey:{api_key}"
            return hashlib.sha256(raw.encode()).hexdigest()[:24]

        # Authenticated user
        user = getattr(request.state, "user", None)
        if user:
            uid = getattr(user, "id", None) or getattr(user, "user_id", None)
            if uid:
                return hashlib.sha256(f"user:{uid}".encode()).hexdigest()[:24]

        # IP address
        ip = self._client_ip(request)
        return hashlib.sha256(f"ip:{ip}".encode()).hexdigest()[:24]

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    @staticmethod
    def _too_many(limit: int, window_seconds: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please try again later.",
                "retry_after": window_seconds,
            },
            headers={
                "Retry-After": str(window_seconds),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + window_seconds),
            },
        )

    async def _cleanup_old_rows(self) -> None:
        """Delete rate_limit_events rows older than one hour."""
        try:
            from app.db import engine

            cutoff = datetime.fromtimestamp(time.time() - 3600, tz=UTC)
            async with engine.begin() as conn:
                await conn.execute(
                    text("DELETE FROM rate_limit_events WHERE window_start < :cutoff"),
                    {"cutoff": cutoff},
                )
        except Exception as exc:
            logger.debug("Rate limit cleanup failed (non-critical): %s", exc)
