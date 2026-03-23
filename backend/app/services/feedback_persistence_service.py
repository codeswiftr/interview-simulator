"""Persistence helpers for feedback entities."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.feedback import AudioFeedback, ContentFeedback, SessionFeedback, VideoFeedback
from app.models.interview import InterviewResponse


class FeedbackPersistenceService:
    """Service for database operations for feedback entities."""

    async def get_by_response_id(
        self, session: AsyncSession, response_id: UUID
    ) -> ContentFeedback | None:
        result = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id == response_id)
        )
        return result.first()

    async def get_all_by_session_id(
        self, session: AsyncSession, session_id: UUID
    ) -> list[ContentFeedback]:
        result = await session.exec(
            select(ContentFeedback)
            .join(InterviewResponse, ContentFeedback.response_id == InterviewResponse.id)
            .where(InterviewResponse.session_id == session_id)
            .order_by(InterviewResponse.created_at)
        )
        return list(result.all())

    async def create_content_feedback(
        self, session: AsyncSession, response_id: UUID, metrics: Any
    ) -> ContentFeedback:
        feedback = ContentFeedback(
            response_id=response_id,
            technical_accuracy=_get_metric(metrics, "technical_accuracy"),
            star_adherence=_get_metric(metrics, "star_adherence"),
            answer_structure=_get_metric(metrics, "answer_structure"),
            completeness=_get_metric(metrics, "completeness"),
            relevance=_get_metric(metrics, "relevance"),
            overall_content_score=_get_metric(metrics, "overall_content_score"),
            strengths=_get_metric(metrics, "strengths", []),
            improvements=_get_metric(metrics, "improvements", []),
            detailed_feedback=_get_metric(metrics, "detailed_feedback", ""),
        )
        session.add(feedback)
        await session.flush()
        return feedback

    async def exists_for_response(self, session: AsyncSession, response_id: UUID) -> bool:
        result = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id == response_id)
        )
        return result.first() is not None

    async def get_by_session_id(
        self, session: AsyncSession, session_id: UUID
    ) -> SessionFeedback | None:
        result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == session_id)
        )
        return result.first()

    async def create_session_feedback(
        self,
        session: AsyncSession,
        session_id: UUID,
        overall_score: float,
        audio_score: float,
        content_score: float,
        top_strengths: list[str],
        top_improvements: list[str],
        recommended_practice_areas: list[str],
        next_question_ids: list[str] | None = None,
    ) -> SessionFeedback:
        feedback = SessionFeedback(
            session_id=session_id,
            overall_score=overall_score,
            audio_score=audio_score,
            content_score=content_score,
            top_strengths=top_strengths,
            top_improvements=top_improvements,
            recommended_practice_areas=recommended_practice_areas,
            next_question_ids=next_question_ids or [],
        )
        session.add(feedback)
        await session.flush()
        return feedback

    async def exists_for_session(self, session: AsyncSession, session_id: UUID) -> bool:
        result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == session_id)
        )
        return result.first() is not None

    async def get_video_by_response_id(
        self, session: AsyncSession, response_id: UUID
    ) -> VideoFeedback | None:
        result = await session.exec(
            select(VideoFeedback).where(VideoFeedback.response_id == response_id)
        )
        return result.first()

    async def get_audio_by_response_id(
        self, session: AsyncSession, response_id: UUID
    ) -> AudioFeedback | None:
        result = await session.exec(
            select(AudioFeedback).where(AudioFeedback.response_id == response_id)
        )
        return result.first()

    async def get_audio_by_session_id(
        self, session: AsyncSession, session_id: UUID
    ) -> list[AudioFeedback]:
        result = await session.exec(
            select(AudioFeedback)
            .join(InterviewResponse, AudioFeedback.response_id == InterviewResponse.id)
            .where(InterviewResponse.session_id == session_id)
            .order_by(InterviewResponse.created_at)
        )
        return list(result.all())


def _get_metric(metrics: Any, name: str, default: Any = 0) -> Any:
    if isinstance(metrics, dict):
        return metrics.get(name, default)
    return getattr(metrics, name, default)
