"""Interview question management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies import get_current_user
from app.db import get_session
from app.models.question import Difficulty, Question, QuestionCategory, QuestionCreate, QuestionRead
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[QuestionRead])
async def list_questions(
    category: QuestionCategory | None = None,
    difficulty: Difficulty | None = None,
    company: str | None = Query(None, description="Filter by company tag"),
    topic: str | None = Query(None, description="Filter by topic tag"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[Question]:
    """List interview questions with optional filters."""
    stmt = select(Question)
    if category:
        stmt = stmt.where(Question.category == category)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if company:
        stmt = stmt.where(Question.company_tags.contains([company]))
    if topic:
        stmt = stmt.where(Question.topic_tags.contains([topic]))

    stmt = stmt.where(Question.is_active.is_(True)).limit(limit).offset(offset)
    result = await session.exec(stmt)
    return result.all()


@router.get("/random", response_model=QuestionRead)
async def get_random_question(
    category: QuestionCategory | None = None,
    difficulty: Difficulty | None = None,
    exclude_ids: list[UUID] | None = Query(None, description="Question IDs to exclude"),
    session: AsyncSession = Depends(get_session),
) -> Question:
    """Get a random question matching criteria."""
    stmt = select(Question).where(Question.is_active.is_(True))
    if category:
        stmt = stmt.where(Question.category == category)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if exclude_ids:
        stmt = stmt.where(Question.id.not_in(exclude_ids))

    stmt = stmt.order_by(func.random()).limit(1)
    result = await session.exec(stmt)
    question = result.first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching question found")
    return question


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question(question_id: UUID, session: AsyncSession = Depends(get_session)) -> Question:
    """Get a specific question by ID."""
    result = await session.exec(select(Question).where(Question.id == question_id, Question.is_active.is_(True)))
    question = result.first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


@router.post("/", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Question:
    """Create a new question (requires authentication)."""
    question = Question(**payload.model_dump())
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return question
