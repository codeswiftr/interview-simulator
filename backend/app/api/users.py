"""User management endpoints."""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.db import get_session
from app.dependencies import get_current_user
from app.models.email_verification import EmailVerificationToken
from app.models.user import (
    ExperienceLevel,
    PasswordChange,
    Token,
    User,
    UserCreate,
    UserLogin,
    UserRead,
    UserUpdate,
)
from app.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.services.email_service import EmailService
from app.services.feedback_service import FeedbackService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    """Register a new user."""
    existing = await session.exec(select(User).where(User.email == payload.email))
    if existing.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        experience_level=payload.experience_level or ExperienceLevel.MID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, session: AsyncSession = Depends(get_session)) -> Token:
    """Authenticate user and return access and refresh tokens."""
    result = await session.exec(select(User).where(User.email == payload.email.lower()))
    user = result.first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Generate access token
    access_token = create_access_token({"sub": str(user.id)})

    # Generate and store refresh token
    refresh_token, refresh_expires = create_refresh_token()
    user.refresh_token = refresh_token
    user.refresh_token_expires_at = refresh_expires
    await session.commit()

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user."""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Update user profile (name, email).

    Email changes require the new email to be unique.
    """
    # Update full_name if provided
    if updates.full_name is not None:
        current_user.full_name = updates.full_name

    # Update experience_level if provided
    if updates.experience_level is not None:
        current_user.experience_level = updates.experience_level

    # Update email if provided and different
    if updates.email is not None and updates.email.lower() != current_user.email:
        # Check if email is already taken
        existing = await session.exec(select(User).where(User.email == updates.email.lower()))
        if existing.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )
        
        # Email changes require verification - send verification email instead of updating directly
        # Generate verification token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=24)  # 24 hour expiry
        
        # Create verification token record
        verification_token = EmailVerificationToken(
            user_id=current_user.id,
            new_email=updates.email.lower(),
            token=token,
            expires_at=expires_at,
        )
        session.add(verification_token)
        await session.commit()
        
        # Send verification email
        email_service = EmailService()
        verification_url = f"{settings.frontend_url}/verify-email?token={token}"
        await email_service.send_email_verification(updates.email.lower(), verification_url)
        
        # Don't update email yet - return success message
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Verification email sent to new address. Please verify before email is changed."
        )

    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.post("/verify-email")
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Verify email address using verification token.

    Updates user email to the verified new email address.

    Args:
        token: Email verification token from email link
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """

    # Look up verification token
    result = await session.exec(
        select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    )
    verification_token = result.first()

    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Check if token is already used
    if verification_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has already been used"
        )

    # Check if token is expired
    now = datetime.now(UTC)
    if verification_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )

    # Get the user
    user_result = await session.exec(select(User).where(User.id == verification_token.user_id))
    user = user_result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    # Check if new email is already taken
    existing = await session.exec(select(User).where(User.email == verification_token.new_email))
    if existing.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )

    # Update user's email
    user.email = verification_token.new_email

    # Mark token as used
    verification_token.used = True

    await session.commit()

    return {"message": "Email address successfully verified and updated"}


@router.post("/me/change-password")
async def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Change user password.

    Requires current password for verification.
    """
    # Verify current password
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )

    # Hash and set new password
    current_user.hashed_password = hash_password(payload.new_password)
    await session.commit()

    return {"message": "Password updated successfully"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete user account (soft delete).

    Sets is_active to False and anonymizes personal data.
    """
    import uuid

    # Anonymize user data
    current_user.email = f"deleted_{uuid.uuid4().hex[:8]}@deleted.user"
    current_user.full_name = "Deleted User"
    current_user.is_active = False

    # Clear Stripe info if any
    current_user.stripe_customer_id = None
    current_user.stripe_subscription_id = None
    current_user.subscription_status = None

    await session.commit()


@router.get("/me/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get user statistics: total sessions, completed sessions, average score, practice time.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        Dictionary with user statistics
    """
    from app.models.interview import InterviewSession, InterviewStatus

    # Get all sessions for user
    sessions_result = await session.exec(
        select(InterviewSession).where(InterviewSession.user_id == current_user.id)
    )
    all_sessions = list(sessions_result.all())

    total_sessions = len(all_sessions)
    completed_sessions = [
        s
        for s in all_sessions
        if s.status == InterviewStatus.COMPLETED or s.status == InterviewStatus.ANALYZED
    ]
    completed_count = len(completed_sessions)

    # Calculate average score from completed sessions
    scores = [s.overall_score for s in completed_sessions if s.overall_score is not None]
    average_score = sum(scores) / len(scores) if scores else None

    # Calculate total practice time (sum of duration_seconds)
    total_practice_time = sum(s.duration_seconds or 0 for s in completed_sessions)

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_count,
        "average_score": round(average_score, 1) if average_score else None,
        "total_practice_time_seconds": total_practice_time,
    }


@router.get("/me/progress")
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get user progress: time-series of session scores and practice recommendations.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        Dictionary with progress data and recommendations
    """
    from app.models.feedback import SessionFeedback
    from app.models.interview import InterviewSession, InterviewStatus

    # Get completed sessions with feedback
    sessions_result = await session.exec(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
        )
        .order_by(InterviewSession.created_at.desc())
        .limit(20)  # Last 20 sessions
    )
    sessions = list(sessions_result.all())

    # Get session feedbacks
    session_ids = [s.id for s in sessions]
    feedbacks_result = await session.exec(
        select(SessionFeedback).where(SessionFeedback.session_id.in_(session_ids))
    )
    feedbacks = {f.session_id: f for f in feedbacks_result.all()}

    # Build time-series data
    score_trend = []
    for s in reversed(sessions):  # Oldest first for trend
        feedback = feedbacks.get(s.id)
        if feedback:
            score_trend.append(
                {
                    "date": s.created_at.isoformat(),
                    "score": feedback.overall_score,
                    "content_score": feedback.content_score,
                    "audio_score": feedback.audio_score,
                }
            )

    # Get practice recommendations from FeedbackService
    feedback_service = FeedbackService()
    progress_data = await feedback_service.get_user_progress(session, current_user.id)

    return {
        "score_trend": score_trend,
        "recommended_practice_areas": progress_data.get("recommended_practice_areas", []),
        "average_audio_score": progress_data.get("average_audio_score"),
        "average_content_score": progress_data.get("average_content_score"),
    }


@router.get("/me/readiness-score")
async def get_readiness_score(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get interview readiness score based on last 5 completed sessions.

    The readiness score is a percentage (0-100) representing how prepared
    the user is for interviews based on recent practice performance.

    Scoring logic:
    - Based on average score of last 5 completed sessions
    - Requires at least 1 session to calculate
    - Returns null if no completed sessions with scores

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        Dictionary with readiness_score, sessions_used, and improvement_trend
    """
    from app.models.interview import InterviewSession, InterviewStatus

    # Get last 5 completed sessions with scores
    sessions_result = await session.exec(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
            InterviewSession.overall_score.isnot(None),
        )
        .order_by(InterviewSession.created_at.desc())
        .limit(5)
    )
    recent_sessions = list(sessions_result.all())

    if not recent_sessions:
        return {
            "readiness_score": None,
            "sessions_used": 0,
            "improvement_trend": None,
            "message": "Complete at least one interview to get your readiness score",
        }

    # Calculate readiness score (average of last 5 sessions)
    scores = [s.overall_score for s in recent_sessions if s.overall_score is not None]
    readiness_score = sum(scores) / len(scores) if scores else None

    # Calculate improvement trend (compare first half vs second half of sessions)
    improvement_trend = None
    if len(scores) >= 2:
        mid = len(scores) // 2
        older_avg = sum(scores[mid:]) / len(scores[mid:]) if scores[mid:] else 0
        newer_avg = sum(scores[:mid]) / len(scores[:mid]) if scores[:mid] else 0
        improvement_trend = round(newer_avg - older_avg, 1)

    return {
        "readiness_score": round(readiness_score, 1) if readiness_score else None,
        "sessions_used": len(scores),
        "improvement_trend": improvement_trend,
    }
