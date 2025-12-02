"""Authentication endpoints for password reset."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import get_session
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.security import hash_password
from app.services.email_service import EmailService
from pydantic import BaseModel

router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password."""

    email: str


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset."""

    token: str
    new_password: str


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
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

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

    # Send email
    email_service = EmailService()
    await email_service.send_password_reset(user.email, reset_url)

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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token is already used
    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used"
        )

    # Check if token is expired
    now = datetime.now(timezone.utc)
    if reset_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Get the user
    user_result = await session.exec(
        select(User).where(User.id == reset_token.user_id)
    )
    user = user_result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    # Update user's password
    user.hashed_password = hash_password(payload.new_password)

    # Mark token as used
    reset_token.used = True

    await session.commit()

    return {"message": "Password successfully reset"}
