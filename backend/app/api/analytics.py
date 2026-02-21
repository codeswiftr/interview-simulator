"""Analytics endpoints for behavioral interview metrics."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user
from app.models.analytics import (
    AnalyticsSummary,
    InterviewAnalyticsRead,
    ProgressResponse,
)
from app.models.interview import InterviewSession
from app.models.user import User
from app.services.behavioral_analytics_service import BehavioralAnalyticsService

router = APIRouter()


async def _verify_session_ownership(
    session: AsyncSession, session_id: UUID, user_id: UUID
) -> InterviewSession:
    """Verify that the interview session belongs to the user.

    Args:
        session: Database session
        session_id: UUID of the interview session
        user_id: UUID of the current user

    Returns:
        InterviewSession if found and belongs to user

    Raises:
        HTTPException: If session not found or unauthorized
    """
    result = await session.exec(
        select(InterviewSession).where(
            InterviewSession.id == session_id, InterviewSession.user_id == user_id
        )
    )
    interview = result.first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found or access denied",
        )
    return interview


@router.get("/sessions/{session_id}", response_model=InterviewAnalyticsRead)
async def get_session_analytics(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewAnalyticsRead:
    """Get behavioral analytics for a specific interview session.

    Returns detailed metrics including filler words, speaking pace, pause analysis,
    STAR compliance, and overall confidence score.

    Args:
        session_id: UUID of the interview session
        current_user: Authenticated user
        session: Database session

    Returns:
        InterviewAnalyticsRead with complete behavioral metrics

    Raises:
        HTTPException: If session not found, unauthorized, or analytics not available
    """
    # Verify ownership
    await _verify_session_ownership(session, session_id, current_user.id)

    # Get analytics
    analytics_service = BehavioralAnalyticsService()
    analytics = await analytics_service.get_session_analytics(session, session_id)

    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Analytics not yet generated for this session. "
                "Analytics are automatically computed after completing an interview."
            ),
        )

    return InterviewAnalyticsRead.model_validate(analytics)


@router.get("/progress", response_model=ProgressResponse)
async def get_user_progress(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProgressResponse:
    """Get user's progress over time across all interview sessions.

    Returns a time-series of key behavioral metrics sorted by date,
    allowing users to visualize improvement trends.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        ProgressResponse with list of data points and total session count
    """
    analytics_service = BehavioralAnalyticsService()
    data_points = await analytics_service.get_user_progress(session, current_user.id)

    return ProgressResponse(
        data_points=data_points,
        total_sessions=len(data_points),
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AnalyticsSummary:
    """Get aggregated analytics summary for the user.

    Returns overall averages across all sessions plus improvement trends
    (comparing first half of sessions to second half).

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        AnalyticsSummary with averages, totals, and improvement percentages
    """
    analytics_service = BehavioralAnalyticsService()
    summary = await analytics_service.get_analytics_summary(session, current_user.id)

    return summary


@router.post(
    "/generate/{session_id}",
    response_model=InterviewAnalyticsRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_session_analytics(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewAnalyticsRead:
    """Generate behavioral analytics for a completed interview session.

    This endpoint is typically called automatically after interview completion,
    but can also be triggered manually if analytics were not generated.

    Args:
        session_id: UUID of the interview session
        current_user: Authenticated user
        session: Database session

    Returns:
        Newly created InterviewAnalyticsRead

    Raises:
        HTTPException: If session not found, unauthorized, or analytics generation fails
    """
    # Verify ownership
    await _verify_session_ownership(session, session_id, current_user.id)

    # Generate analytics
    analytics_service = BehavioralAnalyticsService()
    try:
        analytics = await analytics_service.calculate_session_analytics(
            session, session_id, current_user.id
        )
        return InterviewAnalyticsRead.model_validate(analytics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
