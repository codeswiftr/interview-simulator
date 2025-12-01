"""Feedback retrieval and generation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user
from app.models.feedback import (
    ContentFeedback,
    ContentFeedbackRead,
    SessionFeedback,
    SessionFeedbackRead,
)
from app.models.interview import InterviewResponse, InterviewSession
from app.models.user import User
from app.services.feedback_service import FeedbackService

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


async def _verify_response_ownership(
    session: AsyncSession, response_id: UUID, user_id: UUID
) -> InterviewResponse:
    """Verify that the response belongs to the user.

    Args:
        session: Database session
        response_id: UUID of the response
        user_id: UUID of the current user

    Returns:
        InterviewResponse if found and belongs to user

    Raises:
        HTTPException: If response not found or unauthorized
    """
    result = await session.exec(
        select(InterviewResponse)
        .join(InterviewSession, InterviewResponse.session_id == InterviewSession.id)
        .where(InterviewResponse.id == response_id, InterviewSession.user_id == user_id)
    )
    response = result.first()
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found or access denied",
        )
    return response


@router.get("/session/{session_id}", response_model=SessionFeedbackRead)
async def get_session_feedback(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SessionFeedback:
    """Get aggregated feedback for an entire interview session.

    Returns overall scores, top strengths/improvements, and practice recommendations.

    Args:
        session_id: UUID of the interview session
        current_user: Authenticated user
        session: Database session

    Returns:
        SessionFeedback with aggregated analysis

    Raises:
        HTTPException: If session not found, unauthorized, or no feedback available
    """
    # Verify ownership
    await _verify_session_ownership(session, session_id, current_user.id)

    # Retrieve session feedback
    feedback_service = FeedbackService()
    feedback = await feedback_service.get_session_feedback(session, session_id)

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not yet generated for this session. Use POST /api/v1/feedback/generate/{session_id} to generate it.",
        )

    return feedback


@router.get("/session/{session_id}/all", response_model=list[ContentFeedbackRead])
async def get_all_session_feedbacks(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ContentFeedback]:
    """Get feedback for all responses in a session.

    Returns individual feedback for each response in the interview.

    Args:
        session_id: UUID of the interview session
        current_user: Authenticated user
        session: Database session

    Returns:
        List of ContentFeedback records

    Raises:
        HTTPException: If session not found or unauthorized
    """
    # Verify ownership
    await _verify_session_ownership(session, session_id, current_user.id)

    # Retrieve all feedbacks
    feedback_service = FeedbackService()
    feedbacks = await feedback_service.get_all_session_feedbacks(session, session_id)

    return feedbacks


@router.get("/response/{response_id}", response_model=ContentFeedbackRead)
async def get_response_feedback(
    response_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContentFeedback:
    """Get feedback for a single interview response.

    Returns detailed content analysis including scores, strengths, and improvements.

    Args:
        response_id: UUID of the response
        current_user: Authenticated user
        session: Database session

    Returns:
        ContentFeedback with detailed analysis

    Raises:
        HTTPException: If response not found, unauthorized, or no feedback available
    """
    # Verify ownership
    await _verify_response_ownership(session, response_id, current_user.id)

    # Retrieve feedback
    feedback_service = FeedbackService()
    feedback = await feedback_service.get_response_feedback(session, response_id)

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not yet generated for this response.",
        )

    return feedback


@router.post(
    "/generate/response/{response_id}",
    response_model=ContentFeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_response_feedback(
    response_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContentFeedback:
    """Generate feedback for a single interview response.

    Analyzes the response content using AI and creates a ContentFeedback record.

    Args:
        response_id: UUID of the response to analyze
        current_user: Authenticated user
        session: Database session

    Returns:
        Newly created ContentFeedback

    Raises:
        HTTPException: If response not found, unauthorized, or analysis fails
    """
    # Verify ownership
    await _verify_response_ownership(session, response_id, current_user.id)

    # Generate feedback
    feedback_service = FeedbackService()
    try:
        feedback = await feedback_service.generate_feedback(session, response_id)
        return feedback
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post(
    "/generate/session/{session_id}",
    response_model=SessionFeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_session_feedback(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SessionFeedback:
    """Generate aggregated feedback for entire interview session.

    Analyzes all responses and creates aggregated scores and recommendations.
    Will automatically generate individual response feedback if not already done.

    Args:
        session_id: UUID of the interview session
        current_user: Authenticated user
        session: Database session

    Returns:
        Newly created SessionFeedback

    Raises:
        HTTPException: If session not found, unauthorized, or analysis fails
    """
    # Verify ownership
    await _verify_session_ownership(session, session_id, current_user.id)

    # Generate session feedback
    feedback_service = FeedbackService()
    try:
        feedback = await feedback_service.generate_session_feedback(session, session_id)
        return feedback
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/session/{session_id}/status")
async def get_session_processing_status(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get processing status summary for an interview session.

    Returns counts of responses by processing_status, whether session feedback exists,
    and whether all responses are fully processed.

    Args:
        session_id: UUID of the interview session
        current_user: Authenticated user
        session: Database session

    Returns:
        Dictionary with processing status summary

    Raises:
        HTTPException: If session not found or unauthorized
    """
    # Verify ownership
    await _verify_session_ownership(session, session_id, current_user.id)

    # Get processing summary
    feedback_service = FeedbackService()
    summary = await feedback_service.get_processing_summary(session, session_id)

    return summary
