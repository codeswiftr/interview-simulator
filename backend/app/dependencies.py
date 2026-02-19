"""Common FastAPI dependencies.

Migrated to forge-shared auth (2026-02).
"""

import time
from collections import defaultdict
from datetime import UTC

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from forge_shared.auth.dependencies import get_jwt_auth
from forge_shared.auth.jwt import JWTAuth
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models.user import SubscriptionTier, User

# Use HTTPBearer instead of OAuth2PasswordBearer for better spec compliance
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_session),
    auth: JWTAuth = Depends(get_jwt_auth),
) -> User:
    """Retrieve current user from JWT token using forge-shared auth.

    Migrated from custom JWT implementation to forge-shared for consistency.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        payload = auth.decode_token(token)
        user_id: str = payload.sub
    except Exception:
        raise credentials_exception

    # Fetch user from database
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    if user is None:
        raise credentials_exception

    return user


async def check_interview_quota(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Check if user can create a new interview based on subscription tier.

    Free tier: 3 interviews per month
    Pro/Team tier: Unlimited

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        User if quota allows

    Raises:
        HTTPException: 402 Payment Required if quota exceeded with upgrade URL
    """
    from datetime import datetime

    from app.config import settings

    now = datetime.now(UTC)

    # Reset monthly counter if we're in a new month
    # Compare year and month to handle month boundaries correctly
    created_year_month = (current_user.created_at.year, current_user.created_at.month)
    current_year_month = (now.year, now.month)

    # More robust reset logic: reset if we've crossed into a new calendar month
    if created_year_month != current_year_month and current_user.interviews_this_month > 0:
        current_user.interviews_this_month = 0
        await session.commit()

    # Free tier limit: 3 interviews per month
    FREE_TIER_LIMIT = 3

    # Check quota based on tier
    if (
        current_user.subscription_tier == SubscriptionTier.FREE
        and current_user.interviews_this_month >= FREE_TIER_LIMIT
    ):
        # Build upgrade details with Stripe checkout URL
        upgrade_url = None
        price_id = settings.stripe_price_id_pro_monthly

        if price_id and settings.stripe_secret_key:
            # Include price_id in error detail so frontend can trigger checkout
            upgrade_url = f"{settings.frontend_url}/upgrade?price_id={price_id}"

        detail_message = {
            "message": f"Free tier limit reached ({FREE_TIER_LIMIT} interviews per month). Upgrade to Pro for unlimited interviews.",
            "interviews_used": current_user.interviews_this_month,
            "interviews_limit": FREE_TIER_LIMIT,
            "upgrade_url": upgrade_url,
            "price_id": price_id,
        }

        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail_message,
        )

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
