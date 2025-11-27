"""Common FastAPI dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models.user import SubscriptionTier, User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> User:
    """Retrieve current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

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
        HTTPException: 402 Payment Required if quota exceeded
    """
    # Reset monthly counter if needed (simple check: if created_at is in different month)
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    # Simple reset: if user was created in a different month, reset counter
    # In production, you'd want a last_reset_at field
    if current_user.created_at:
        if (
            current_user.created_at.month != now.month
            or current_user.created_at.year != now.year
        ):
            # Only reset if counter is non-zero (avoid unnecessary updates)
            if current_user.interviews_this_month > 0:
                current_user.interviews_this_month = 0
                await session.commit()

    # Check quota based on tier
    if current_user.subscription_tier == SubscriptionTier.FREE:
        if current_user.interviews_this_month >= 3:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Free tier limit reached. Upgrade to Pro for unlimited interviews.",
            )

    return current_user
