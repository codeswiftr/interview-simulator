"""Coaching hint generation endpoints."""

import json
import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize OpenRouter client for Gemini 2.0 Flash
_coaching_client: AsyncOpenAI | None = None

# Static hint fallbacks when AI is unavailable
STATIC_HINTS = {
    "behavioral": "Try using the STAR framework: Situation, Task, Action, Result",
    "technical": "Clarify the problem requirements before jumping into a solution",
    "system_design": "Start with functional and non-functional requirements",
}

# Per-user rate limiting for coaching hints (5 hints per minute)
_coaching_rate_limits: dict[str, list[float]] = defaultdict(list)
COACHING_RATE_LIMIT = 5  # hints per minute
COACHING_RATE_WINDOW = 60  # seconds


def get_coaching_client() -> AsyncOpenAI:
    """Get or create OpenRouter client for coaching hints.

    Returns:
        AsyncOpenAI client configured for OpenRouter
    """
    global _coaching_client
    if _coaching_client is None:
        _coaching_client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _coaching_client


def check_coaching_rate_limit(user_id: str) -> tuple[bool, int]:
    """Check if user has exceeded coaching hint rate limit.

    Args:
        user_id: User ID string

    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    now = time.time()
    cutoff = now - COACHING_RATE_WINDOW

    # Clean old requests
    _coaching_rate_limits[user_id] = [
        ts for ts in _coaching_rate_limits[user_id] if ts > cutoff
    ]

    # Count requests in window
    request_count = len(_coaching_rate_limits[user_id])

    if request_count >= COACHING_RATE_LIMIT:
        return False, 0

    # Record this request
    _coaching_rate_limits[user_id].append(now)

    remaining = COACHING_RATE_LIMIT - request_count - 1
    return True, remaining


class CoachingHintRequest(BaseModel):
    """Request model for coaching hint generation."""

    question: str = Field(..., description="The interview question")
    question_type: str = Field(
        ..., description="Type of question: behavioral, technical, or system_design"
    )
    transcript: str = Field(
        default="", description="Current transcript of the candidate's answer"
    )


class CoachingHintResponse(BaseModel):
    """Response model for coaching hint."""

    hint: str = Field(..., description="Contextual coaching hint")


async def generate_coaching_hint(
    question: str, question_type: str, transcript: str
) -> str:
    """Generate a coaching hint using Gemini 2.0 Flash via OpenRouter.

    Args:
        question: The interview question
        question_type: Type of question (behavioral, technical, system_design)
        transcript: Current transcript of the answer

    Returns:
        A contextual coaching hint

    Raises:
        Exception: If AI service is unavailable or returns an error
    """
    # Build prompt based on question type
    if question_type == "behavioral":
        focus_areas = "STAR structure, quantifying results, personal contribution"
    elif question_type == "technical":
        focus_areas = "Problem clarification, approach explanation, edge cases"
    elif question_type == "system_design":
        focus_areas = "Requirements, scalability, trade-offs"
    else:
        focus_areas = "Clarity, specificity, examples"

    prompt = f"""You are an interview coach. Based on the question and the candidate's current answer transcript, provide a brief, actionable hint (1-2 sentences) to help them improve their answer.

Question: {question}
Question Type: {question_type}
Current Transcript: {transcript}

Provide a specific, contextual hint. Focus on: {focus_areas}

Hint (max 100 words):"""

    # Fallback to static hints if OpenRouter is not configured
    if not settings.openrouter_api_key:
        logger.warning("OpenRouter API key not configured, using static hints")
        return STATIC_HINTS.get(question_type, "Speak clearly and provide specific examples")

    try:
        client = get_coaching_client()
        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",  # Gemini 2.0 Flash via OpenRouter
            max_tokens=150,  # Keep hints concise
            temperature=0.7,  # Slightly creative but focused
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from AI service")
        hint = content.strip()

        return hint

    except Exception as e:
        logger.error(f"Error generating coaching hint: {e}")
        # Fallback to static hints on error
        return STATIC_HINTS.get(question_type, "Speak clearly and provide specific examples")


async def generate_coaching_hint_stream(
    question: str, question_type: str, transcript: str
):
    """Generate a coaching hint with streaming support.

    Args:
        question: The interview question
        question_type: Type of question (behavioral, technical, system_design)
        transcript: Current transcript of the answer

    Yields:
        JSON strings with streaming hint chunks
    """
    # Build prompt based on question type
    if question_type == "behavioral":
        focus_areas = "STAR structure, quantifying results, personal contribution"
    elif question_type == "technical":
        focus_areas = "Problem clarification, approach explanation, edge cases"
    elif question_type == "system_design":
        focus_areas = "Requirements, scalability, trade-offs"
    else:
        focus_areas = "Clarity, specificity, examples"

    prompt = f"""You are an interview coach. Based on the question and the candidate's current answer transcript, provide a brief, actionable hint (1-2 sentences) to help them improve their answer.

Question: {question}
Question Type: {question_type}
Current Transcript: {transcript}

Provide a specific, contextual hint. Focus on: {focus_areas}

Hint (max 100 words):"""

    # Fallback to static hints if OpenRouter is not configured
    if not settings.openrouter_api_key:
        logger.warning("OpenRouter API key not configured, using static hints")
        hint = STATIC_HINTS.get(question_type, "Speak clearly and provide specific examples")
        yield f"data: {json.dumps({'hint': hint, 'done': True})}\n\n"
        return

    try:
        client = get_coaching_client()
        stream = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",  # Gemini 2.0 Flash via OpenRouter
            max_tokens=150,  # Keep hints concise
            temperature=0.7,  # Slightly creative but focused
            messages=[{"role": "user", "content": prompt}],
            stream=True,  # Enable streaming
        )

        accumulated_hint = ""
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                accumulated_hint += content
                # Stream each chunk as it arrives
                yield f"data: {json.dumps({'hint': accumulated_hint, 'done': False})}\n\n"

        # Send final message with done flag
        if accumulated_hint:
            yield f"data: {json.dumps({'hint': accumulated_hint.strip(), 'done': True})}\n\n"
        else:
            # If no content received, fall back to static hint
            hint = STATIC_HINTS.get(question_type, "Speak clearly and provide specific examples")
            yield f"data: {json.dumps({'hint': hint, 'done': True})}\n\n"

    except Exception as e:
        logger.error(f"Error generating streaming coaching hint: {e}")
        # Fallback to static hints on error
        hint = STATIC_HINTS.get(question_type, "Speak clearly and provide specific examples")
        yield f"data: {json.dumps({'hint': hint, 'done': True})}\n\n"


@router.post("/hint", response_model=CoachingHintResponse)
async def get_coaching_hint(
    request: CoachingHintRequest,
    current_user: User = Depends(get_current_user),
) -> CoachingHintResponse:
    """Generate a contextual coaching hint based on question and transcript.

    Args:
        request: Coaching hint request with question, type, and transcript
        current_user: Current authenticated user

    Returns:
        CoachingHintResponse with generated hint

    Raises:
        HTTPException: If question_type is invalid or rate limit exceeded
    """
    # Check rate limit
    is_allowed, remaining = check_coaching_rate_limit(str(current_user.id))
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {COACHING_RATE_LIMIT} hints per minute.",
            headers={"X-RateLimit-Remaining": "0", "Retry-After": "60"},
        )

    # Validate question_type
    valid_types = {"behavioral", "technical", "system_design"}
    if request.question_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"question_type must be one of: {', '.join(valid_types)}",
        )

    # Generate hint
    hint = await generate_coaching_hint(
        question=request.question,
        question_type=request.question_type,
        transcript=request.transcript,
    )

    response = CoachingHintResponse(hint=hint)
    return response


@router.post("/hint/stream")
async def get_coaching_hint_stream(
    request: CoachingHintRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Generate a contextual coaching hint with streaming support.

    Streams hint chunks as they are generated by the AI model for low latency.

    Args:
        request: Coaching hint request with question, type, and transcript
        current_user: Current authenticated user

    Returns:
        StreamingResponse with Server-Sent Events (SSE) format

    Raises:
        HTTPException: If question_type is invalid or rate limit exceeded
    """
    # Check rate limit
    is_allowed, remaining = check_coaching_rate_limit(str(current_user.id))
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {COACHING_RATE_LIMIT} hints per minute.",
            headers={"X-RateLimit-Remaining": "0", "Retry-After": "60"},
        )

    # Validate question_type
    valid_types = {"behavioral", "technical", "system_design"}
    if request.question_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"question_type must be one of: {', '.join(valid_types)}",
        )

    # Create streaming generator
    stream_generator = generate_coaching_hint_stream(
        question=request.question,
        question_type=request.question_type,
        transcript=request.transcript,
    )

    return StreamingResponse(
        stream_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "X-RateLimit-Remaining": str(remaining),
        },
    )
