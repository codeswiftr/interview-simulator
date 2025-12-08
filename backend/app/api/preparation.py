"""Answer preparation endpoints for AI Ghostwriter feature."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.transcriber import Transcriber
from app.config import settings
from app.db import get_session
from app.dependencies import get_current_user
from app.models.preparation import (
    AnswerPreparation,
    DeliveryAttempt,
    PreparationQnA,
    PreparationStage,
)
from app.models.question import Question
from app.models.user import SubscriptionTier, User

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize OpenRouter client for Gemini 2.0 Flash (detective) and Claude Haiku 4.5 (ghostwriter)
_preparation_client: AsyncOpenAI | None = None


def get_preparation_client() -> AsyncOpenAI:
    """Get or create OpenRouter client for preparation AI.

    Returns:
        AsyncOpenAI client configured for OpenRouter
    """
    global _preparation_client
    if _preparation_client is None:
        _preparation_client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _preparation_client


def check_preparation_tier(user: User) -> None:
    """Check if user has access to preparation feature (Pro/Premium only).

    Args:
        user: Current user

    Raises:
        HTTPException: If user is on Free tier
    """
    if user.subscription_tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Answer preparation is available for Pro and Premium subscribers. Upgrade to access this feature.",
        )


# Request/Response Models
class PreparationStartRequest(BaseModel):
    question_id: UUID


class PreparationStartResponse(BaseModel):
    preparation_id: UUID
    stage: str
    message: str


class DetectiveQuestionResponse(BaseModel):
    question: str
    order: int
    is_complete: bool = False


class DetectiveAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, description="User's answer to the clarifying question")


class DetectiveAnswerResponse(BaseModel):
    next_question: str | None = None
    stage: str
    is_complete: bool = False


class DraftResponse(BaseModel):
    draft_answer: str
    stage: str


class PracticeStartResponse(BaseModel):
    attempt_id: UUID
    stage: str


class PracticeSubmitRequest(BaseModel):
    audio_url: str = Field(..., description="URL to the uploaded audio file")


class PracticeSubmitResponse(BaseModel):
    attempt_id: UUID
    transcript: str
    stage: str


class DeliveryAttemptRead(BaseModel):
    id: UUID
    preparation_id: UUID
    audio_url: str | None
    transcript: str | None
    delivery_score: float | None
    comparison_feedback: str | None
    created_at: datetime


class AttemptsResponse(BaseModel):
    attempts: list[DeliveryAttemptRead]


# Endpoints
@router.post("/start", response_model=PreparationStartResponse, status_code=status.HTTP_201_CREATED)
async def start_preparation(
    request: PreparationStartRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PreparationStartResponse:
    """Start answer preparation for a question.

    Args:
        request: Preparation start request with question_id
        current_user: Authenticated user
        session: Database session

    Returns:
        PreparationStartResponse with preparation_id and initial stage

    Raises:
        HTTPException: If question not found, tier check fails, or preparation already exists
    """
    # Check tier
    check_preparation_tier(current_user)

    # Verify question exists
    result = await session.exec(select(Question).where(Question.id == request.question_id))
    question = result.first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    # Check if preparation already exists for this user + question
    existing_result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.user_id == current_user.id,
            AnswerPreparation.question_id == request.question_id,
        )
    )
    if existing_result.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Preparation already exists for this question. Use GET /preparation/{id} to retrieve it.",
        )

    # Create preparation
    preparation = AnswerPreparation(
        user_id=current_user.id,
        question_id=request.question_id,
        stage=PreparationStage.DETECTIVE,
    )
    session.add(preparation)
    await session.commit()
    await session.refresh(preparation)

    return PreparationStartResponse(
        preparation_id=preparation.id,
        stage=preparation.stage.value,
        message="Preparation started. Use POST /preparation/{id}/detective/question to get the first question.",
    )


@router.post("/{preparation_id}/detective/question", response_model=DetectiveQuestionResponse)
async def get_detective_question(
    preparation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DetectiveQuestionResponse:
    """Get the next clarifying question from the detective stage.

    Uses Gemini 2.0 Flash to generate contextual questions based on:
    - The original interview question
    - Previous Q&A in this preparation session
    - User's experience level

    Args:
        preparation_id: UUID of the preparation session
        current_user: Authenticated user
        session: Database session

    Returns:
        DetectiveQuestionResponse with the next question

    Raises:
        HTTPException: If preparation not found, unauthorized, or stage is not detective
    """
    # Verify preparation exists and belongs to user
    result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.id == preparation_id,
            AnswerPreparation.user_id == current_user.id,
        )
    )
    preparation = result.first()
    if not preparation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preparation not found or access denied",
        )

    # Check tier
    check_preparation_tier(current_user)

    # Verify we're in detective stage
    if preparation.stage != PreparationStage.DETECTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preparation is in {preparation.stage.value} stage, not detective stage",
        )

    # Get question
    question_result = await session.exec(
        select(Question).where(Question.id == preparation.question_id)
    )
    question = question_result.first()

    # Get existing Q&A
    qna_result = await session.exec(
        select(PreparationQnA)
        .where(PreparationQnA.preparation_id == preparation_id)
        .order_by(PreparationQnA.order)
    )
    existing_qna = list(qna_result.all())

    # Generate next question using Gemini 2.0 Flash
    if not settings.openrouter_api_key:
        # Fallback: return a generic question
        next_order = len(existing_qna) + 1
        if next_order == 1:
            return DetectiveQuestionResponse(
                question="Can you tell me about a specific project or experience that relates to this question?",
                order=next_order,
                is_complete=False,
            )
        else:
            # Mark as complete if we've asked enough questions
            preparation.stage = PreparationStage.DRAFT
            await session.commit()
            return DetectiveQuestionResponse(
                question="",
                order=next_order,
                is_complete=True,
            )

    try:
        client = get_preparation_client()

        # Build context from existing Q&A
        qna_context = ""
        if existing_qna:
            qna_context = "\n\nPrevious Q&A:\n"
            for qna in existing_qna:
                qna_context += f"Q: {qna.question}\nA: {qna.answer}\n"

        # Build prompt
        prompt = f"""You are an interview coach helping a candidate prepare an answer. Based on the interview question and any previous answers, ask ONE clarifying question to gather more context.

Interview Question: {question.content if question else "Unknown"}
Question Type: {question.category if question else "behavioral"}
User Experience Level: {current_user.experience_level if hasattr(current_user, 'experience_level') else 'mid'}
{qna_context}

Ask ONE specific, helpful question to gather context. Keep it concise (1 sentence). If you have enough information (3-5 questions asked), respond with "ENOUGH_INFO" instead of a question.

Question:"""

        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            max_tokens=100,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from AI service")

        content = content.strip()

        # Check if we have enough info
        if "ENOUGH_INFO" in content.upper() or len(existing_qna) >= 4:
            preparation.stage = PreparationStage.DRAFT
            await session.commit()
            return DetectiveQuestionResponse(
                question="",
                order=len(existing_qna) + 1,
                is_complete=True,
            )

        # Save the question to database
        next_order = len(existing_qna) + 1
        qna = PreparationQnA(
            preparation_id=preparation_id,
            question=content,
            answer="",  # Will be filled when user answers
            order=next_order,
        )
        session.add(qna)
        await session.commit()

        return DetectiveQuestionResponse(
            question=content,
            order=next_order,
            is_complete=False,
        )

    except Exception as e:
        logger.error(f"Error generating detective question: {e}")
        # Fallback to generic question
        next_order = len(existing_qna) + 1
        if next_order <= 3:
            fallback_question = "Can you provide more specific details about your experience?"
            # Save fallback question
            qna = PreparationQnA(
                preparation_id=preparation_id,
                question=fallback_question,
                answer="",
                order=next_order,
            )
            session.add(qna)
            await session.commit()
            return DetectiveQuestionResponse(
                question=fallback_question,
                order=next_order,
                is_complete=False,
            )
        else:
            preparation.stage = PreparationStage.DRAFT
            await session.commit()
            return DetectiveQuestionResponse(
                question="",
                order=next_order,
                is_complete=True,
            )


@router.post("/{preparation_id}/detective/answer", response_model=DetectiveAnswerResponse)
async def submit_detective_answer(
    preparation_id: UUID,
    request: DetectiveAnswerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DetectiveAnswerResponse:
    """Submit answer to a detective question.

    Args:
        preparation_id: UUID of the preparation session
        request: Answer to the question
        current_user: Authenticated user
        session: Database session

    Returns:
        DetectiveAnswerResponse with next question or completion status

    Raises:
        HTTPException: If preparation not found, unauthorized, or stage is not detective
    """
    # Verify preparation exists and belongs to user
    result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.id == preparation_id,
            AnswerPreparation.user_id == current_user.id,
        )
    )
    preparation = result.first()
    if not preparation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preparation not found or access denied",
        )

    # Check tier
    check_preparation_tier(current_user)

    # Verify we're in detective stage
    if preparation.stage != PreparationStage.DETECTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preparation is in {preparation.stage.value} stage, not detective stage",
        )

    # Get the last unanswered question
    qna_result = await session.exec(
        select(PreparationQnA)
        .where(
            PreparationQnA.preparation_id == preparation_id,
            PreparationQnA.answer == "",  # Unanswered
        )
        .order_by(PreparationQnA.order)
    )
    last_qna = qna_result.first()

    if not last_qna:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No unanswered question found. Call POST /preparation/{id}/detective/question first.",
        )

    # Save the answer
    last_qna.answer = request.answer
    await session.commit()

    # Get next question
    next_question_resp = await get_detective_question(preparation_id, current_user, session)
    next_question_data = next_question_resp.model_dump()

    if next_question_data["is_complete"]:
        return DetectiveAnswerResponse(
            next_question=None,
            stage=PreparationStage.DRAFT.value,
            is_complete=True,
        )

    return DetectiveAnswerResponse(
        next_question=next_question_data["question"],
        stage=PreparationStage.DETECTIVE.value,
        is_complete=False,
    )


@router.post("/{preparation_id}/generate-draft", response_model=DraftResponse)
async def generate_draft(
    preparation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftResponse:
    """Generate personalized draft answer using Claude Haiku 4.5.

    Uses all Q&A from detective stage to create a STAR-formatted answer.

    Args:
        preparation_id: UUID of the preparation session
        current_user: Authenticated user
        session: Database session

    Returns:
        DraftResponse with generated draft answer

    Raises:
        HTTPException: If preparation not found, unauthorized, or stage is not draft
    """
    # Verify preparation exists and belongs to user
    result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.id == preparation_id,
            AnswerPreparation.user_id == current_user.id,
        )
    )
    preparation = result.first()
    if not preparation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preparation not found or access denied",
        )

    # Check tier
    check_preparation_tier(current_user)

    # Verify we're in draft stage
    if preparation.stage != PreparationStage.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preparation is in {preparation.stage.value} stage. Complete detective stage first.",
        )

    # Get question
    question_result = await session.exec(
        select(Question).where(Question.id == preparation.question_id)
    )
    question = question_result.first()

    # Get all Q&A
    qna_result = await session.exec(
        select(PreparationQnA)
        .where(PreparationQnA.preparation_id == preparation_id)
        .order_by(PreparationQnA.order)
    )
    qna_list = list(qna_result.all())

    if not qna_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Q&A found. Complete detective stage first.",
        )

    # Build Q&A context
    qna_context = "\n\nContext from Q&A:\n"
    for qna in qna_list:
        qna_context += f"Q: {qna.question}\nA: {qna.answer}\n"

    # Generate draft using Claude Haiku 4.5
    if not settings.openrouter_api_key:
        # Fallback draft
        draft = f"""**Situation**: Based on the context provided
**Task**: Your responsibility
**Action**: Specific steps you took
**Result**: Measurable outcome"""
    else:
        try:
            client = get_preparation_client()

            prompt = f"""You are an interview coach helping a candidate prepare a personalized answer. Based on the interview question and the candidate's responses to clarifying questions, draft a well-structured answer using the STAR method (Situation, Task, Action, Result).

Interview Question: {question.content if question else "Unknown"}
Question Type: {question.category if question else "behavioral"}
User Experience Level: {current_user.experience_level if hasattr(current_user, 'experience_level') else 'mid'}
{qna_context}

Draft a personalized, authentic answer that:
1. Uses the STAR framework (Situation, Task, Action, Result)
2. Incorporates specific details from the Q&A context
3. Is grounded in the candidate's actual experiences
4. Is concise but complete (2-3 minutes when spoken)
5. Quantifies results where possible
6. Emphasizes the candidate's personal contribution

Format the answer clearly with STAR sections labeled. Make it feel authentic and personal, not generic.

Draft Answer:"""

            response = await client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",  # Claude Haiku 4.5 via OpenRouter
                max_tokens=800,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from AI service")
            draft = content.strip()

        except Exception as e:
            logger.error(f"Error generating draft: {e}")
            # Fallback draft
            draft = f"""**Situation**: Based on your experience
**Task**: Your responsibility
**Action**: Specific steps you took
**Result**: Measurable outcome

Use the context from your answers to fill in the details above."""

    # Save draft
    preparation.draft_answer = draft
    preparation.stage = PreparationStage.PRACTICE
    await session.commit()
    await session.refresh(preparation)

    return DraftResponse(
        draft_answer=draft,
        stage=preparation.stage.value,
    )


@router.get("/{preparation_id}/draft", response_model=DraftResponse)
async def get_draft(
    preparation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftResponse:
    """Get the generated draft answer.

    Args:
        preparation_id: UUID of the preparation session
        current_user: Authenticated user
        session: Database session

    Returns:
        DraftResponse with draft answer

    Raises:
        HTTPException: If preparation not found, unauthorized, or draft not generated
    """
    # Verify preparation exists and belongs to user
    result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.id == preparation_id,
            AnswerPreparation.user_id == current_user.id,
        )
    )
    preparation = result.first()
    if not preparation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preparation not found or access denied",
        )

    if not preparation.draft_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not yet generated. Complete detective stage and call POST /preparation/{id}/generate-draft first.",
        )

    return DraftResponse(
        draft_answer=preparation.draft_answer,
        stage=preparation.stage.value,
    )


@router.post(
    "/{preparation_id}/practice/start",
    response_model=PracticeStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_practice(
    preparation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PracticeStartResponse:
    """Start a practice delivery attempt for a prepared answer.

    Creates a new DeliveryAttempt record and transitions preparation to PRACTICE stage.

    Args:
        preparation_id: UUID of the preparation session
        current_user: Authenticated user
        session: Database session

    Returns:
        PracticeStartResponse with attempt_id and stage

    Raises:
        HTTPException: If preparation not found, unauthorized, or draft not generated
    """
    # Verify preparation exists and belongs to user
    result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.id == preparation_id,
            AnswerPreparation.user_id == current_user.id,
        )
    )
    preparation = result.first()
    if not preparation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preparation not found or access denied",
        )

    # Check tier
    check_preparation_tier(current_user)

    # Verify draft exists
    if not preparation.draft_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft not yet generated. Complete detective stage and generate draft first.",
        )

    # Create delivery attempt
    attempt = DeliveryAttempt(
        preparation_id=preparation_id,
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)

    # Update stage to PRACTICE if not already
    if preparation.stage != PreparationStage.PRACTICE:
        preparation.stage = PreparationStage.PRACTICE
        await session.commit()

    return PracticeStartResponse(
        attempt_id=attempt.id,
        stage=PreparationStage.PRACTICE.value,
    )


@router.post(
    "/{preparation_id}/practice/submit",
    response_model=PracticeSubmitResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_practice(
    preparation_id: UUID,
    request: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PracticeSubmitResponse:
    """Submit a practice delivery attempt with audio.

    Transcribes the audio and stores the transcript. The attempt can later be rated
    using the rating endpoint (Epic 3).

    Args:
        preparation_id: UUID of the preparation session
        request: PracticeSubmitRequest with audio_url
        current_user: Authenticated user
        session: Database session

    Returns:
        PracticeSubmitResponse with attempt_id, transcript, and stage

    Raises:
        HTTPException: If preparation not found, unauthorized, or transcription fails
    """
    # Verify preparation exists and belongs to user
    result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.id == preparation_id,
            AnswerPreparation.user_id == current_user.id,
        )
    )
    preparation = result.first()
    if not preparation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preparation not found or access denied",
        )

    # Check tier
    check_preparation_tier(current_user)

    # Get the most recent attempt (or create one if none exists)
    attempts_result = await session.exec(
        select(DeliveryAttempt)
        .where(DeliveryAttempt.preparation_id == preparation_id)
        .order_by(DeliveryAttempt.created_at.desc())
    )
    attempt = attempts_result.first()

    if not attempt:
        # Create attempt if none exists
        attempt = DeliveryAttempt(
            preparation_id=preparation_id,
        )
        session.add(attempt)
        await session.commit()
        await session.refresh(attempt)

    # Store audio URL
    attempt.audio_url = request.audio_url

    # Transcribe audio
    try:
        # Convert URL path to file path (local storage)
        # audio_url format: /uploads/audio/filename.webm
        audio_path = Path(".") / request.audio_url.lstrip("/")
        if not audio_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found at specified URL",
            )

        transcriber = Transcriber()
        transcription_result = await transcriber.transcribe(audio_path, language="en")
        attempt.transcript = transcription_result.text

    except Exception as e:
        logger.error(f"Transcription failed for practice attempt {attempt.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        ) from None

    await session.commit()
    await session.refresh(attempt)

    return PracticeSubmitResponse(
        attempt_id=attempt.id,
        transcript=attempt.transcript or "",
        stage=preparation.stage.value,
    )


@router.get(
    "/{preparation_id}/attempts",
    response_model=AttemptsResponse,
)
async def get_attempts(
    preparation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AttemptsResponse:
    """Get all delivery attempts for a preparation session.

    Returns attempts ordered by creation time (newest first).

    Args:
        preparation_id: UUID of the preparation session
        current_user: Authenticated user
        session: Database session

    Returns:
        AttemptsResponse with list of delivery attempts

    Raises:
        HTTPException: If preparation not found or unauthorized
    """
    # Verify preparation exists and belongs to user
    result = await session.exec(
        select(AnswerPreparation).where(
            AnswerPreparation.id == preparation_id,
            AnswerPreparation.user_id == current_user.id,
        )
    )
    preparation = result.first()
    if not preparation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preparation not found or access denied",
        )

    # Get all attempts
    attempts_result = await session.exec(
        select(DeliveryAttempt)
        .where(DeliveryAttempt.preparation_id == preparation_id)
        .order_by(DeliveryAttempt.created_at.desc())
    )
    attempts = list(attempts_result.all())

    return AttemptsResponse(
        attempts=[
            DeliveryAttemptRead(
                id=attempt.id,
                preparation_id=attempt.preparation_id,
                audio_url=attempt.audio_url,
                transcript=attempt.transcript,
                delivery_score=attempt.delivery_score,
                comparison_feedback=attempt.comparison_feedback,
                created_at=attempt.created_at,
            )
            for attempt in attempts
        ]
    )
