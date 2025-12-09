"""Answer preparation endpoints for AI Ghostwriter feature."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.services.delivery_rating_service import DeliveryRatingService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_stage_value(stage: PreparationStage | str) -> str:
    """Get string value from stage (handles both enum and string from DB)."""
    return stage.value if hasattr(stage, "value") else stage

# Initialize OpenRouter client for Gemini 2.0 Flash (detective) and Claude Haiku 4.5 (ghostwriter)
_preparation_client: AsyncOpenAI | None = None

# Simple in-memory cache for detective questions (question_id + exp_level + qna_count -> question)
# Cache size limit: 100 entries (LRU eviction)
_detective_question_cache: dict[str, str] = {}
_cache_access_order: list[str] = []
_MAX_CACHE_SIZE = 100


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


class DraftUpdateRequest(BaseModel):
    draft_answer: str = Field(..., min_length=1, description="Updated draft answer")


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
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    created_at: datetime


class AttemptsResponse(BaseModel):
    attempts: list[DeliveryAttemptRead]


class RateDeliveryRequest(BaseModel):
    attempt_id: UUID


class RateDeliveryResponse(BaseModel):
    delivery_score: float
    content_coverage: float
    key_points: float
    flow_structure: float
    comparison_feedback: str
    strengths: list[str]
    improvements: list[str]
    stage: str


class ComparisonResponse(BaseModel):
    draft: str
    delivery: str
    delivery_score: float | None
    comparison_feedback: str | None
    strengths: list[str]
    improvements: list[str]


class QuestionContext(BaseModel):
    id: UUID
    content: str
    category: str | None = None
    difficulty: str | None = None
    company_tags: list[str] | None = None


class PreparationStateResponse(BaseModel):
    preparation_id: UUID
    stage: str
    question: QuestionContext
    qna: list[PreparationQnA]
    current_question: str | None
    draft_answer: str | None
    attempts: list[DeliveryAttemptRead]


@router.get("/{preparation_id}/state", response_model=PreparationStateResponse)
async def get_preparation_state(
    preparation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PreparationStateResponse:
    """Get complete preparation state for resume flows."""
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

    # Fetch question context
    question_result = await session.exec(
        select(Question).where(Question.id == preparation.question_id)
    )
    question = question_result.first()

    # Fetch Q&A history
    qna_result = await session.exec(
        select(PreparationQnA)
        .where(PreparationQnA.preparation_id == preparation_id)
        .order_by(PreparationQnA.order)
    )
    qna_list = list(qna_result.all())

    # Determine the current (unanswered) question if any
    current_question = None
    for qna in qna_list:
        if qna.answer == "":
            current_question = qna.question
            break

    # Fetch attempts
    attempts_result = await session.exec(
        select(DeliveryAttempt)
        .where(DeliveryAttempt.preparation_id == preparation_id)
        .order_by(DeliveryAttempt.created_at.desc())
    )
    attempts = list(attempts_result.all())

    return PreparationStateResponse(
        preparation_id=preparation.id,
        stage=get_stage_value(preparation.stage),
        question=QuestionContext(
            id=question.id if question else preparation.question_id,
            content=question.content if question else "",
            category=getattr(question, "category", None),
            difficulty=getattr(question, "difficulty", None),
            company_tags=getattr(question, "company_tags", None),
        ),
        qna=qna_list,
        current_question=current_question,
        draft_answer=preparation.draft_answer,
        attempts=[
            DeliveryAttemptRead(
                id=attempt.id,
                preparation_id=attempt.preparation_id,
                audio_url=attempt.audio_url,
                transcript=attempt.transcript,
                delivery_score=attempt.delivery_score,
                comparison_feedback=attempt.comparison_feedback,
                strengths=(attempt.comparison_details or {}).get("strengths", []),
                improvements=(attempt.comparison_details or {}).get("improvements", []),
                created_at=attempt.created_at,
            )
            for attempt in attempts
        ],
    )


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
    existing_prep = existing_result.first()
    if existing_prep:
        # Return the existing preparation instead of error
        return PreparationStartResponse(
            preparation_id=existing_prep.id,
            stage=get_stage_value(existing_prep.stage),
            message="Existing preparation found. Resuming from current stage.",
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
        stage=get_stage_value(preparation.stage),
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
            detail=f"Preparation is in {get_stage_value(preparation.stage)} stage, not detective stage",
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

    # Check cache for similar question patterns
    exp_level = (
        current_user.experience_level.value
        if hasattr(current_user, "experience_level") and hasattr(current_user.experience_level, "value")
        else (current_user.experience_level if hasattr(current_user, "experience_level") else "mid")
    )
    cache_key = f"{preparation.question_id}:{exp_level}:{len(existing_qna)}"

    # Try cache first (only for similar question counts)
    if len(existing_qna) <= 2 and cache_key in _detective_question_cache:
        # Update LRU order
        if cache_key in _cache_access_order:
            _cache_access_order.remove(cache_key)
        _cache_access_order.append(cache_key)
        cached_question = _detective_question_cache[cache_key]

        # Save cached question
        next_order = len(existing_qna) + 1
        qna = PreparationQnA(
            preparation_id=preparation_id,
            question=cached_question,
            answer="",
            order=next_order,
        )
        session.add(qna)
        await session.commit()

        logger.debug(f"Using cached detective question for {cache_key}")
        return DetectiveQuestionResponse(
            question=cached_question,
            order=next_order,
            is_complete=False,
        )

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

        # Build prompt (optimized for token efficiency)
        q_type = question.category if question else "behavioral"
        exp_level = (
            current_user.experience_level.value
            if hasattr(current_user, "experience_level") and hasattr(current_user.experience_level, "value")
            else (current_user.experience_level if hasattr(current_user, "experience_level") else "mid")
        )

        prompt = f"""Interview coach: Ask ONE clarifying question.

Q: {question.content if question else "Unknown"}
Type: {q_type} | Level: {exp_level}
{qna_context}

Ask ONE concise question. If enough info (3-5 Q&A), respond "ENOUGH_INFO" only."""

        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            max_tokens=80,  # Reduced from 100 - questions should be shorter
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

        # Cache the question if it's an early question (more likely to be reusable)
        if len(existing_qna) <= 2:
            # LRU eviction if cache is full
            if len(_detective_question_cache) >= _MAX_CACHE_SIZE:
                oldest_key = _cache_access_order.pop(0)
                del _detective_question_cache[oldest_key]

            _detective_question_cache[cache_key] = content
            _cache_access_order.append(cache_key)

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
            detail=f"Preparation is in {get_stage_value(preparation.stage)} stage, not detective stage",
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
            detail=f"Preparation is in {get_stage_value(preparation.stage)} stage. Complete detective stage first.",
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

    # Build Q&A context (optimized format)
    qna_context = "\n".join([f"Q{i+1}: {qna.question}\nA{i+1}: {qna.answer}" for i, qna in enumerate(qna_list)])

    # Generate draft using Claude Haiku 4.5
    if not settings.openrouter_api_key:
        # Fallback draft
        draft = """**Situation**: Based on the context provided
**Task**: Your responsibility
**Action**: Specific steps you took
**Result**: Measurable outcome"""
    else:
        try:
            client = get_preparation_client()

            q_type = question.category if question else "behavioral"
            exp_level = (
                current_user.experience_level.value
                if hasattr(current_user, "experience_level") and hasattr(current_user.experience_level, "value")
                else (current_user.experience_level if hasattr(current_user, "experience_level") else "mid")
            )

            # Optimized prompt for token efficiency
            prompt = f"""Draft STAR answer.

Question: {question.content if question else "Unknown"}
Type: {q_type} | Level: {exp_level}

{qna_context}

Requirements:
- STAR format (Situation, Task, Action, Result)
- Use Q&A details
- 2-3 min when spoken
- Quantify results
- Personal contribution focus

Draft:"""

            response = await client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",  # Claude Haiku 4.5 via OpenRouter
                max_tokens=700,  # Reduced from 800 - drafts should be concise
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
            draft = """**Situation**: Based on your experience
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
        stage=get_stage_value(preparation.stage),
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
        stage=get_stage_value(preparation.stage),
    )


@router.patch(
    "/{preparation_id}/draft",
    response_model=DraftResponse,
)
async def update_draft(
    preparation_id: UUID,
    request: DraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftResponse:
    """Update the draft answer.

    Allows users to edit their AI-generated draft before practicing.

    Args:
        preparation_id: UUID of the preparation session
        request: DraftUpdateRequest with updated draft
        current_user: Authenticated user
        session: Database session

    Returns:
        DraftResponse with updated draft answer

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

    # Verify draft exists (must have been generated first)
    if not preparation.draft_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft not yet generated. Generate draft first before editing.",
        )

    # Update draft
    preparation.draft_answer = request.draft_answer
    preparation.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(preparation)

    return DraftResponse(
        draft_answer=preparation.draft_answer,
        stage=get_stage_value(preparation.stage),
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

    # Convert URL path to file path (local storage)
    # audio_url format: /uploads/audio/filename.webm
    audio_path = Path(".") / request.audio_url.lstrip("/")
    if not audio_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found at specified URL",
        )

    # Transcribe audio
    try:
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
        stage=get_stage_value(preparation.stage),
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
                strengths=(attempt.comparison_details or {}).get("strengths", []),
                improvements=(attempt.comparison_details or {}).get("improvements", []),
                created_at=attempt.created_at,
            )
            for attempt in attempts
        ]
    )


@router.post(
    "/{preparation_id}/rate-delivery",
    response_model=RateDeliveryResponse,
    status_code=status.HTTP_200_OK,
)
async def rate_delivery(
    preparation_id: UUID,
    request: RateDeliveryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RateDeliveryResponse:
    """Rate a delivery attempt against the prepared draft.

    Compares the transcribed delivery to the draft answer using AI
    and provides scores and feedback.

    Args:
        preparation_id: UUID of the preparation session
        request: RateDeliveryRequest with attempt_id
        current_user: Authenticated user
        session: Database session

    Returns:
        RateDeliveryResponse with scores and feedback

    Raises:
        HTTPException: If preparation, attempt, or draft not found
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
            detail="Draft not yet generated. Generate draft first.",
        )

    # Get the attempt
    attempt_result = await session.exec(
        select(DeliveryAttempt).where(
            DeliveryAttempt.id == request.attempt_id,
            DeliveryAttempt.preparation_id == preparation_id,
        )
    )
    attempt = attempt_result.first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery attempt not found or access denied",
        )

    # Verify attempt has transcript
    if not attempt.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt has no transcript. Submit practice attempt first.",
        )

    # Rate the delivery
    rating_service = DeliveryRatingService()
    try:
        rating = await rating_service.rate_delivery(
            draft=preparation.draft_answer,
            delivery_transcript=attempt.transcript,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rating failed: {str(e)}",
        ) from None

    # Save rating to attempt
    attempt.delivery_score = rating.delivery_score
    attempt.comparison_feedback = rating.comparison_feedback
    attempt.comparison_details = {
        "strengths": rating.strengths,
        "improvements": rating.improvements,
        "content_coverage": rating.content_coverage,
        "key_points": rating.key_points,
        "flow_structure": rating.flow_structure,
    }
    await session.commit()

    # Update preparation stage to COMPLETE if first successful rating
    if preparation.stage != PreparationStage.COMPLETE:
        preparation.stage = PreparationStage.COMPLETE
        await session.commit()

    return RateDeliveryResponse(
        delivery_score=rating.delivery_score,
        content_coverage=rating.content_coverage,
        key_points=rating.key_points,
        flow_structure=rating.flow_structure,
        comparison_feedback=rating.comparison_feedback,
        strengths=rating.strengths,
        improvements=rating.improvements,
        stage=get_stage_value(preparation.stage),
    )


@router.get(
    "/{preparation_id}/comparison",
    response_model=ComparisonResponse,
)
async def get_comparison(
    preparation_id: UUID,
    attempt_id: UUID = Query(..., description="UUID of the delivery attempt"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ComparisonResponse:
    """Get side-by-side comparison of draft and delivery.

    Args:
        preparation_id: UUID of the preparation session
        attempt_id: UUID of the delivery attempt (query parameter)
        current_user: Authenticated user
        session: Database session

    Returns:
        ComparisonResponse with draft, delivery, scores, and feedback

    Raises:
        HTTPException: If preparation or attempt not found
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

    # Get the attempt
    attempt_result = await session.exec(
        select(DeliveryAttempt).where(
            DeliveryAttempt.id == attempt_id,
            DeliveryAttempt.preparation_id == preparation_id,
        )
    )
    attempt = attempt_result.first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery attempt not found or access denied",
        )

    details = attempt.comparison_details or {}
    strengths: list[str] = details.get("strengths", [])
    improvements: list[str] = details.get("improvements", [])

    return ComparisonResponse(
        draft=preparation.draft_answer or "",
        delivery=attempt.transcript or "",
        delivery_score=attempt.delivery_score,
        comparison_feedback=attempt.comparison_feedback,
        strengths=strengths,
        improvements=improvements,
    )
