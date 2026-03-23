"""Common FastAPI dependencies.

Migrated to forge-auth (ForgeAuth facade) for S152 Week 2.
"""

import time
from collections import defaultdict
from datetime import UTC

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from forge_shared.auth.forge_auth import AuthError, ForgeAuth
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models.user import SubscriptionTier, User

# Use HTTPBearer instead of OAuth2PasswordBearer for better spec compliance
security = HTTPBearer(auto_error=False)


def _get_forge_auth() -> ForgeAuth:
    """Get the ForgeAuth instance from app.security (lazy singleton)."""
    from app.security import get_forge_auth_instance

    return get_forge_auth_instance()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Retrieve current user from JWT token using forge-auth.

    Migrated from JWTAuth (forge-shared low-level) to ForgeAuth facade
    (forge-shared high-level) for S152 Week 2.

    The get_current_user signature is kept backward-compatible:
    routes that Depend on this still receive the SQLModel User object
    fetched from the database — not a ForgeUser or TokenPayload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        auth = _get_forge_auth()
        token = credentials.credentials
        payload = auth.decode_token(token)
        user_id: str = payload.sub
    except AuthError:
        raise credentials_exception from None
    except Exception:
        raise credentials_exception from None

    # Fetch user from database — IS still uses its own SQLModel User model
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    if user is None:
        raise credentials_exception

    return user


async def check_interview_quota(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Check quota and atomically increment the monthly interview counter.

    Free tier: 3 interviews per month
    Pro/Team tier: Unlimited

    The quota check and counter increment are performed as a single atomic
    UPDATE statement (``interviews_this_month = interviews_this_month + 1
    WHERE interviews_this_month < limit``).  This prevents the TOCTOU race
    condition where concurrent requests could both pass a separate SELECT
    check before either had incremented the counter.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        User if quota allows (counter has already been incremented)

    Raises:
        HTTPException: 402 Payment Required if quota exceeded with upgrade URL
    """
    from datetime import datetime

    from sqlalchemy import text

    from app.config import settings

    now = datetime.now(UTC)

    # Reset monthly counter if we've crossed into a new calendar month.
    # This non-atomic reset is safe because it only runs once per month and
    # the subsequent atomic increment enforces the limit regardless.
    last_reset = current_user.interviews_reset_at or current_user.created_at
    last_reset_month = (last_reset.year, last_reset.month)
    current_month = (now.year, now.month)

    if last_reset_month != current_month:
        current_user.interviews_this_month = 0
        current_user.interviews_reset_at = now
        await session.commit()

    # Free tier limit: 3 interviews per month
    free_tier_limit = 3

    # Team members with an active org subscription bypass the free-tier quota
    team_id = getattr(current_user, "team_id", None)
    if team_id is not None:
        from app.models.organization import Organization

        org_result = await session.exec(select(Organization).where(Organization.id == team_id))
        team_org = org_result.first()
        if (
            team_org
            and team_org.is_active
            and team_org.subscription_status in ("active", "trialing")
        ):
            return current_user

    # Non-free tiers have unlimited quota — skip atomic check.
    if current_user.subscription_tier != SubscriptionTier.FREE:
        return current_user

    # Atomic quota check + increment in a single UPDATE statement.
    #
    # Only increments when interviews_this_month < limit, so concurrent
    # requests cannot both read "under limit" and both succeed — the DB
    # serialises the updates and at most `limit` of them will match.
    #
    # Works on both SQLite (tests) and PostgreSQL (production) because it
    # uses standard SQL with no dialect-specific locking hints.
    result = await session.execute(
        text(
            "UPDATE users "
            "SET interviews_this_month = interviews_this_month + 1, "
            "    total_interviews = total_interviews + 1 "
            "WHERE id = :user_id "
            "  AND subscription_tier = 'free' "
            "  AND interviews_this_month < :limit "
            "RETURNING interviews_this_month"
        ).bindparams(user_id=str(current_user.id), limit=free_tier_limit)
    )
    updated_row = result.fetchone()

    if updated_row is None:
        # Zero rows matched — quota already at or above the limit.
        upgrade_url = None
        price_id = settings.stripe_price_id_pro_monthly

        if price_id and settings.stripe_secret_key:
            upgrade_url = f"{settings.frontend_url}/upgrade?price_id={price_id}"

        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": f"Free tier limit reached ({free_tier_limit} interviews per month). Upgrade to Pro for unlimited interviews.",
                "interviews_used": current_user.interviews_this_month,
                "interviews_limit": free_tier_limit,
                "upgrade_url": upgrade_url,
                "price_id": price_id,
            },
        )

    await session.commit()

    # Reflect the new counter value on the in-memory object so callers that
    # read current_user.interviews_this_month see the post-increment value.
    current_user.interviews_this_month = updated_row[0]

    return current_user


# ===== Per-Endpoint Rate Limiting =====


class EndpointRateLimiter:
    """Simple in-memory per-endpoint rate limiter using sliding window."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP for rate limiting."""
        # Trust Cloudflare CF-Connecting-IP if CF-RAY present
        cf_ray = request.headers.get("CF-RAY")
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ray and cf_ip:
            return cf_ip

        # X-Forwarded-For (rightmost = closest proxy)
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            ips = [ip.strip() for ip in xff.split(",")]
            if len(ips) <= 5:
                return ips[-1]

        # Direct connection
        if request.client:
            return request.client.host
        return "unknown"

    def _clean_old(self, key: str) -> None:
        cutoff = time.time() - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, request: Request) -> None:
        """Check rate limit. Raises HTTPException if exceeded."""
        ip = self._get_client_ip(request)
        key = f"{request.url.path}:{ip}"

        self._clean_old(key)

        if len(self._requests[key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {self.window_seconds} seconds.",
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[key].append(time.time())


# Pre-configured rate limiters for auth endpoints
_login_limiter = EndpointRateLimiter(max_requests=10, window_seconds=60)
_register_limiter = EndpointRateLimiter(max_requests=5, window_seconds=60)
_password_reset_limiter = EndpointRateLimiter(max_requests=5, window_seconds=60)


def rate_limit_login(request: Request) -> None:
    """Rate limit login: 10 requests per minute per IP."""
    _login_limiter.check(request)


def rate_limit_register(request: Request) -> None:
    """Rate limit registration: 5 requests per minute per IP."""
    _register_limiter.check(request)


def rate_limit_password_reset(request: Request) -> None:
    """Rate limit password reset: 5 requests per minute per IP."""
    _password_reset_limiter.check(request)
