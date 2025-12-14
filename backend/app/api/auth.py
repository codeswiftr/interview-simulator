"""Authentication endpoints for password reset and token refresh."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import get_session
from app.models.password_reset import PasswordResetToken
from app.models.user import RefreshTokenRequest, Token, User
from app.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_refresh_token,
)
from app.services.email_service import EmailService

router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password."""

    email: str


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset."""

    token: str
    new_password: str

    def model_post_init(self, __context: Any) -> None:
        """Validate new password after model initialization."""
        from app.utils.password_validation import validate_password

        errors = validate_password(self.new_password)
        if errors:
            from pydantic import ValidationError
            raise ValidationError.from_exception_data(
                "ResetPasswordRequest",
                [{"type": "value_error", "loc": ("new_password",), "msg": "\n".join(errors)}]
            )


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Request a password reset email.

    Always returns success for security (don't reveal if email exists).
    Generates a secure token and sends reset link via email.

    Args:
        payload: Email address for password reset
        session: Database session

    Returns:
        Success message (always, regardless of email existence)
    """
    # Always return success to avoid revealing if email exists (security best practice)
    response = {
        "message": "If an account with that email exists, a password reset link has been sent."
    }

    # Look up user by email
    result = await session.exec(select(User).where(User.email == payload.email.lower()))
    user = result.first()

    if not user:
        # Don't reveal that user doesn't exist - just return success
        return response

    # Generate secure token
    token = secrets.token_urlsafe(32)

    # Token expires in 1 hour
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    # Create password reset token
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    session.add(reset_token)
    await session.commit()

    # Build reset URL
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    # Send email (errors are logged but don't affect response for security)
    email_service = EmailService()
    try:
        await email_service.send_password_reset(user.email, reset_url)
    except Exception as e:
        # Log error but don't expose to user (security best practice)
        import logging
        logging.getLogger(__name__).error(f"Failed to send password reset email: {e}")

    return response


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Reset password using a valid token.

    Validates token exists, is not used, and is not expired.
    Updates user's password and marks token as used.

    Args:
        payload: Token and new password
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    # Look up token
    result = await session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token == payload.token)
    )
    reset_token = result.first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
        )

    # Check if token is already used
    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has already been used"
        )

    # Check if token is expired
    now = datetime.now(UTC)
    if reset_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has expired"
        )

    # Get the user
    user_result = await session.exec(select(User).where(User.id == reset_token.user_id))
    user = user_result.first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

    # Update user's password
    user.hashed_password = hash_password(payload.new_password)

    # Mark token as used
    reset_token.used = True

    await session.commit()

    return {"message": "Password successfully reset"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Refresh access token using a valid refresh token.

    Implements token rotation: invalidates old refresh token and issues new pair.

    Args:
        payload: Refresh token from client
        session: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Find user with this refresh token
    result = await session.exec(select(User).where(User.refresh_token == payload.refresh_token))
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Verify token is not expired
    if not verify_refresh_token(
        user.refresh_token, payload.refresh_token, user.refresh_token_expires_at
    ):
        # Clear invalid token
        user.refresh_token = None
        user.refresh_token_expires_at = None
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )

    # Generate new tokens (token rotation)
    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token, new_expires = create_refresh_token()

    # Store new refresh token (invalidates old one)
    user.refresh_token = new_refresh_token
    user.refresh_token_expires_at = new_expires
    await session.commit()

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)
