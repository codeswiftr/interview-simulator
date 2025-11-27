"""Interview session management endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies import get_current_user
from app.db import get_session
from app.models.interview import (
    InterviewQuestion,
    InterviewResponse,
    InterviewResponseCreate,
    InterviewResponseRead,
    InterviewSession,
    InterviewSessionCreate,
    InterviewSessionRead,
    InterviewStatus,
    InterviewType,
)
from app.models.question import Question
from app.models.user import User

router = APIRouter()


def _get_time() -> datetime:
    return datetime.now(timezone.utc)


async def _get_interview_for_user(
    session: AsyncSession, interview_id: UUID, user_id: UUID
) -> InterviewSession:
    result = await session.exec(
        select(InterviewSession).where(
            InterviewSession.id == interview_id, InterviewSession.user_id == user_id
        )
    )
    interview = result.first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return interview


@router.post("/", response_model=InterviewSessionRead, status_code=status.HTTP_201_CREATED)
async def create_interview(
    payload: InterviewSessionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewSession:
    """Create a new interview session."""
    interview = InterviewSession(
        user_id=current_user.id,
        interview_type=payload.interview_type,
        company_style=payload.company_style,
        question_count=payload.question_count,
        status=InterviewStatus.SCHEDULED,
        scheduled_at=payload.scheduled_at,
    )
    session.add(interview)
    await session.commit()
    await session.refresh(interview)
    return interview


@router.get("/", response_model=list[InterviewSessionRead])
async def list_interviews(
    status_filter: InterviewStatus | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[InterviewSession]:
    """List user's interview sessions."""
    stmt = select(InterviewSession).where(InterviewSession.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(InterviewSession.status == status_filter)

    stmt = stmt.order_by(InterviewSession.created_at.desc()).limit(limit).offset(offset)
    result = await session.exec(stmt)
    return result.all()


@router.get("/{interview_id}", response_model=InterviewSessionRead)
async def get_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewSession:
    """Get interview session details."""
    return await _get_interview_for_user(session, interview_id, current_user.id)


@router.post("/{interview_id}/start", response_model=InterviewSessionRead)
async def start_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewSession:
    """Start an interview session."""
    interview = await _get_interview_for_user(session, interview_id, current_user.id)
    if interview.status not in {InterviewStatus.SCHEDULED, InterviewStatus.IN_PROGRESS}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start interview")

    interview.status = InterviewStatus.IN_PROGRESS
    interview.started_at = interview.started_at or _get_time()
    await session.commit()
    await session.refresh(interview)
    return interview


@router.post("/{interview_id}/end", response_model=InterviewSessionRead)
async def end_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewSession:
    """End an interview session."""
    interview = await _get_interview_for_user(session, interview_id, current_user.id)
    if interview.status not in {InterviewStatus.IN_PROGRESS, InterviewStatus.SCHEDULED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot end interview")

    now = _get_time()
    interview.status = InterviewStatus.COMPLETED
    interview.ended_at = now
    interview.started_at = interview.started_at or now
    interview.duration_seconds = int((interview.ended_at - interview.started_at).total_seconds())
    await session.commit()
    await session.refresh(interview)
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Cancel a scheduled interview."""
    interview = await _get_interview_for_user(session, interview_id, current_user.id)
    if interview.status != InterviewStatus.SCHEDULED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only scheduled interviews can be cancelled")
    interview.status = InterviewStatus.CANCELLED
    await session.commit()


@router.post("/{interview_id}/responses", response_model=InterviewResponseRead, status_code=status.HTTP_201_CREATED)
async def submit_response(
    interview_id: UUID,
    payload: InterviewResponseCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewResponse:
    """Submit a response to an interview question."""
    # Verify interview exists and belongs to user
    interview = await _get_interview_for_user(session, interview_id, current_user.id)

    # Validate interview is in progress
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only submit responses to interviews in progress"
        )

    # Verify question belongs to this interview session
    question_link_result = await session.exec(
        select(InterviewQuestion).where(
            InterviewQuestion.session_id == interview_id,
            InterviewQuestion.question_id == payload.question_id
        )
    )
    question_link = question_link_result.first()
    if not question_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question does not belong to this interview session"
        )

    # Create the response
    response = InterviewResponse(
        session_id=interview_id,
        question_id=payload.question_id,
        audio_url=payload.audio_url,
        video_url=payload.video_url,
        transcript=payload.transcript,
        duration_seconds=payload.duration_seconds,
    )

    # Calculate word count if transcript is provided
    if payload.transcript:
        response.word_count = len(payload.transcript.split())

    session.add(response)
    await session.commit()
    await session.refresh(response)
    return response


@router.get("/{interview_id}/responses", response_model=list[InterviewResponseRead])
async def get_responses(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[InterviewResponse]:
    """Get all responses for an interview session."""
    # Verify interview exists and belongs to user
    await _get_interview_for_user(session, interview_id, current_user.id)

    # Fetch all responses for this interview
    result = await session.exec(
        select(InterviewResponse)
        .where(InterviewResponse.session_id == interview_id)
        .order_by(InterviewResponse.created_at)
    )
    return result.all()


@router.get("/{interview_id}/feedback")
async def get_interview_feedback(interview_id: UUID) -> dict[str, str]:
    """Placeholder for feedback retrieval."""
    return {"message": f"Get feedback for interview {interview_id} - not yet implemented"}
