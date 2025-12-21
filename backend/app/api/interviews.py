"""Interview session management endpoints."""

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.dependencies import check_interview_quota, get_current_user
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
from app.models.question import Question, QuestionRead
from app.models.user import User
from app.services.analytics import Events, get_analytics
from app.services.background_tasks import background_tasks
from app.services.interview_service import InterviewService

logger = logging.getLogger(__name__)

router = APIRouter()
interview_service = InterviewService()


def _get_time() -> datetime:
    return datetime.now(UTC)


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


@router.post(
    "",
    response_model=InterviewSessionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_interview_quota)],
)
async def create_interview(
    payload: InterviewSessionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewSession:
    """Create a new interview session.

    Enforces subscription quota limits (Free: 3/month, Pro: unlimited).
    """
    interview = InterviewSession(
        user_id=current_user.id,
        interview_type=payload.interview_type,
        company_style=payload.company_style,
        target_company=payload.target_company,
        question_count=payload.question_count,
        difficulty=payload.difficulty,
        status=InterviewStatus.SCHEDULED,
        scheduled_at=payload.scheduled_at,
    )
    session.add(interview)

    # Increment interview counter
    current_user.interviews_this_month += 1
    current_user.total_interviews += 1

    await session.commit()
    await session.refresh(interview)

    # Track interview created event
    get_analytics().capture(
        user_id=str(current_user.id),
        event=Events.INTERVIEW_CREATED,
        properties={
            "interview_id": str(interview.id),
            "interview_type": str(interview.interview_type),
            "question_count": interview.question_count,
            "difficulty": interview.difficulty,
            "company_style": interview.company_style,
        },
    )

    return interview


@router.get("", response_model=list[InterviewSessionRead])
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
    """Start an interview session.

    When starting an interview, random questions are assigned based on
    the interview type. Questions are linked via InterviewQuestion records.
    """
    interview = await _get_interview_for_user(session, interview_id, current_user.id)
    if interview.status not in {InterviewStatus.SCHEDULED, InterviewStatus.IN_PROGRESS}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start interview"
        )

    # Assign questions if not already assigned (idempotent for re-starting)
    has_questions = await interview_service.has_assigned_questions(session, interview_id)
    if not has_questions:
        try:
            await interview_service.assign_questions(session, interview)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from None

    interview.status = InterviewStatus.IN_PROGRESS
    interview.started_at = interview.started_at or _get_time()
    await session.commit()
    await session.refresh(interview)
    return interview


@router.get("/{interview_id}/questions", response_model=list[QuestionRead])
async def get_interview_questions(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Question]:
    """Get all questions assigned to an interview session.

    Returns questions in the order they should be asked.
    Must be called after the interview has been started.
    """
    # Verify interview exists and belongs to user
    interview = await _get_interview_for_user(session, interview_id, current_user.id)

    # Check if interview has been started (questions are assigned on start)
    if interview.status == InterviewStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview has not been started. Call POST /start first.",
        )

    questions = await interview_service.get_interview_questions(session, interview_id)

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions found for this interview.",
        )

    return questions


@router.post("/{interview_id}/end", response_model=InterviewSessionRead)
async def end_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewSession:
    """End an interview session.

    After ending, automatically triggers background generation of session feedback.
    """
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

    # Trigger background session feedback generation
    asyncio.create_task(background_tasks.generate_session_feedback_async(interview_id))

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only scheduled interviews can be cancelled",
        )
    interview.status = InterviewStatus.CANCELLED
    await session.commit()


@router.post(
    "/{interview_id}/responses",
    response_model=InterviewResponseRead,
    status_code=status.HTTP_201_CREATED,
)
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
            detail="Can only submit responses to interviews in progress",
        )

    # Verify question belongs to this interview session
    question_link_result = await session.exec(
        select(InterviewQuestion).where(
            InterviewQuestion.session_id == interview_id,
            InterviewQuestion.question_id == payload.question_id,
        )
    )
    question_link = question_link_result.first()
    if not question_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question does not belong to this interview session",
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

    # Process audio in background if audio_url is provided
    if payload.audio_url and not payload.transcript:
        # Start background task for audio processing
        asyncio.create_task(
            background_tasks.process_response_audio_async(response.id, payload.audio_url)
        )

    return response


@router.get("/{interview_id}/responses", response_model=list[InterviewResponseRead])
async def get_responses(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get all responses for an interview session with question data."""
    # Verify interview exists and belongs to user
    await _get_interview_for_user(session, interview_id, current_user.id)

    # Fetch all responses for this interview
    result = await session.exec(
        select(InterviewResponse)
        .where(InterviewResponse.session_id == interview_id)
        .order_by(InterviewResponse.created_at)
    )
    responses = result.all()

    # Fetch questions for all responses
    question_ids = [r.question_id for r in responses]
    if question_ids:
        question_result = await session.exec(select(Question).where(Question.id.in_(question_ids)))
        questions_map = {q.id: q for q in question_result.all()}
    else:
        questions_map = {}

    # Build response with embedded question data
    response_data = []
    for r in responses:
        question = questions_map.get(r.question_id)
        response_dict = {
            "id": r.id,
            "session_id": r.session_id,
            "question_id": r.question_id,
            "audio_url": r.audio_url,
            "video_url": r.video_url,
            "transcript": r.transcript,
            "duration_seconds": r.duration_seconds,
            "word_count": r.word_count,
            "filler_word_count": r.filler_word_count,
            "processing_status": r.processing_status,
            "processing_error": r.processing_error,
            "created_at": r.created_at,
            "question": {
                "id": question.id,
                "content": question.content,
                "category": question.category,
                "difficulty": question.difficulty,
            }
            if question
            else None,
        }
        response_data.append(response_dict)

    return response_data


@router.get("/{interview_id}/feedback")
async def get_interview_feedback(interview_id: UUID) -> dict[str, str]:
    """Placeholder for feedback retrieval."""
    return {"message": f"Get feedback for interview {interview_id} - not yet implemented"}


@router.post(
    "/quick-practice",
    response_model=InterviewSessionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_interview_quota)],
)
async def create_quick_practice(
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InterviewSession:
    """Create a 1-question practice session with a specific question.

    Allows users to practice individual questions from the question bank.
    Enforces subscription quota limits (Free: 3/month, Pro: unlimited).
    """
    # First, verify the question exists and get its details
    result = await session.exec(
        select(Question).where(
            Question.id == question_id,
            Question.is_active == True,  # noqa: E712
        )
    )
    question = result.first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or is inactive",
        )

    # Map question category to interview type
    category_to_type = {
        "behavioral": InterviewType.BEHAVIORAL,
        "technical": InterviewType.TECHNICAL,
        "system_design": InterviewType.SYSTEM_DESIGN,
    }
    interview_type = category_to_type.get(question.category, InterviewType.BEHAVIORAL)

    # Create interview session
    interview = InterviewSession(
        user_id=current_user.id,
        interview_type=interview_type,
        company_style=question.company_tags[0] if question.company_tags else None,
        question_count=1,
        status=InterviewStatus.SCHEDULED,
    )
    session.add(interview)
    await session.flush()

    # Assign the specific question
    try:
        await interview_service.assign_specific_question(session, interview, question_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    # Increment interview counter
    current_user.interviews_this_month += 1
    current_user.total_interviews += 1

    await session.commit()
    await session.refresh(interview)
    return interview
