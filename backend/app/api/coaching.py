"""Coaching hint generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


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
    """Generate a coaching hint using AI.

    Args:
        question: The interview question
        question_type: Type of question (behavioral, technical, system_design)
        transcript: Current transcript of the answer

    Returns:
        A contextual coaching hint
    """
    # TODO: Implement AI hint generation with Gemini 2.0 Flash
    # For now, return a placeholder
    if question_type == "behavioral":
        return "Try using the STAR framework: Situation, Task, Action, Result"
    elif question_type == "technical":
        return "Clarify the problem requirements before jumping into a solution"
    elif question_type == "system_design":
        return "Start with functional and non-functional requirements"
    else:
        return "Speak clearly and provide specific examples"


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
        HTTPException: If question_type is invalid
    """
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

    return CoachingHintResponse(hint=hint)
