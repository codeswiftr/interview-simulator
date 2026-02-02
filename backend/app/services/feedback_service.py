"""Feedback orchestration service."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.content_analyzer import ContentAnalyzer
from app.models.feedback import AudioFeedback, ContentFeedback, SessionFeedback, SkillsGapResponse, VideoFeedback
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus
from app.models.question import Question
from app.models.user import User
from app.services.aggregation_service import AggregationService
from app.services.feedback_persistence_service import FeedbackPersistenceService
from app.services.question_recommender import recommend_next_questions
from app.services.scoring_service import ScoringService
from app.services.video_service import VideoService


class FeedbackService:
    """Orchestrates feedback generation using specialized services."""

    def __init__(
        self,
        scoring_service: ScoringService | None = None,
        persistence_service: FeedbackPersistenceService | None = None,
        aggregation_service: AggregationService | None = None,
    ) -> None:
        self.content_analyzer = ContentAnalyzer()
        self.video_service = VideoService()
        self.scoring_service = scoring_service or ScoringService()
        self.persistence_service = persistence_service or FeedbackPersistenceService()
        self.aggregation_service = aggregation_service or AggregationService(self.scoring_service)

    async def generate_feedback(self, session: AsyncSession, response_id: UUID) -> ContentFeedback:
        result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.id == response_id)
        )
        response = result.first()
        if not response:
            raise ValueError(f"Response {response_id} not found")

        if await self.persistence_service.exists_for_response(session, response_id):
            raise ValueError(f"Feedback already exists for response {response_id}")

        if not response.transcript:
            raise ValueError(f"Response {response_id} has no transcript to analyze")

        question_result = await session.exec(
            select(Question).where(Question.id == response.question_id)
        )
        question = question_result.first()
        if not question:
            raise ValueError(f"Question {response.question_id} not found")

        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == response.session_id)
        )
        interview = interview_result.first()

        experience_level = "mid"
        if interview:
            user_result = await session.exec(select(User).where(User.id == interview.user_id))
            user = user_result.first()
            if user and user.experience_level:
                experience_level = str(user.experience_level)

        question_type = str(question.category) if question.category else "behavioral"
        metrics = await self.content_analyzer.analyze(
            question=question.content,
            transcript=response.transcript,
            question_type=question_type,
            experience_level=experience_level,
        )

        overall_score = self.content_analyzer.calculate_overall_score(metrics, question_type)

        feedback = await self.persistence_service.create_content_feedback(
            session,
            response_id,
            {
                "technical_accuracy": metrics.technical_accuracy,
                "star_adherence": metrics.star_adherence,
                "answer_structure": metrics.answer_structure,
                "completeness": metrics.completeness,
                "relevance": metrics.relevance,
                "overall_content_score": overall_score,
                "strengths": metrics.strengths,
                "improvements": metrics.improvements,
                "detailed_feedback": metrics.detailed_feedback,
            },
        )

        await session.commit()
        await session.refresh(feedback)
        return feedback

    async def generate_session_feedback(
        self, session: AsyncSession, session_id: UUID
    ) -> SessionFeedback:
        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        interview = interview_result.first()
        if not interview:
            raise ValueError(f"Interview session {session_id} not found")

        if await self.persistence_service.exists_for_session(session, session_id):
            raise ValueError(f"Session feedback already exists for session {session_id}")

        responses_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.session_id == session_id)
        )
        responses = list(responses_result.all())
        if not responses:
            raise ValueError(f"No responses found for session {session_id}")

        existing_feedbacks = await self.persistence_service.get_all_by_session_id(session, session_id)
        existing_map = {cf.response_id: cf for cf in existing_feedbacks}

        for response in responses:
            if response.id not in existing_map and response.transcript:
                try:
                    await self.generate_feedback(session, response.id)
                except ValueError:
                    continue

        all_feedback = await self.persistence_service.get_all_by_session_id(session, session_id)
        if not all_feedback:
            raise ValueError(f"No feedback could be generated for session {session_id}")

        audio_feedbacks = await self.persistence_service.get_audio_by_session_id(session, session_id)

        aggregated = await self.aggregation_service.aggregate_session_feedback(
            session, interview, all_feedback, audio_feedbacks
        )

        next_question_ids: list[str] = []
        if responses:
            last_response = responses[-1]
            try:
                next_question_ids = await recommend_next_questions(
                    session=session,
                    user_id=interview.user_id,
                    question_id=last_response.question_id,
                    feedback_score=aggregated.overall_score,
                )
            except Exception:
                next_question_ids = []

        session_feedback = await self.persistence_service.create_session_feedback(
            session,
            session_id=session_id,
            overall_score=aggregated.overall_score,
            audio_score=aggregated.audio_score,
            content_score=aggregated.content_score,
            top_strengths=aggregated.top_strengths,
            top_improvements=aggregated.top_improvements,
            recommended_practice_areas=aggregated.recommended_practice_areas,
            next_question_ids=next_question_ids,
        )

        interview.overall_score = aggregated.overall_score
        interview.audio_score = aggregated.audio_score
        interview.content_score = aggregated.content_score
        interview.status = InterviewStatus.ANALYZED

        await session.commit()
        await session.refresh(session_feedback)
        return session_feedback

    async def get_response_feedback(
        self, session: AsyncSession, response_id: UUID
    ) -> ContentFeedback | None:
        return await self.persistence_service.get_by_response_id(session, response_id)

    async def get_video_feedback(
        self, session: AsyncSession, response_id: UUID
    ) -> VideoFeedback | None:
        return await self.persistence_service.get_video_by_response_id(session, response_id)

    async def generate_video_feedback(
        self, session: AsyncSession, response_id: UUID
    ) -> VideoFeedback:
        response_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.id == response_id)
        )
        response = response_result.first()
        if not response:
            raise ValueError(f"Response {response_id} not found")
        if not response.video_url:
            raise ValueError("Response has no video attached")

        existing = await self.persistence_service.get_video_by_response_id(session, response_id)
        if existing:
            raise ValueError(f"Video feedback already exists for response {response_id}")

        video_path = Path(response.video_url.lstrip("/"))
        if not video_path.exists():
            backend_relative = Path("backend") / video_path
            if backend_relative.exists():
                video_path = backend_relative
            else:
                raise ValueError(f"Video file not found at {response.video_url}")

        return await self.video_service.process_response_video(
            session, response_id, str(video_path)
        )

    async def get_session_feedback(
        self, session: AsyncSession, session_id: UUID
    ) -> SessionFeedback | None:
        return await self.persistence_service.get_by_session_id(session, session_id)

    async def get_all_session_feedbacks(
        self, session: AsyncSession, session_id: UUID
    ) -> list[ContentFeedback]:
        return await self.persistence_service.get_all_by_session_id(session, session_id)

    async def get_processing_summary(self, session: AsyncSession, session_id: UUID) -> dict:
        return await self.aggregation_service.aggregate_processing_status(session, session_id)

    async def get_user_progress(self, session: AsyncSession, user_id: UUID) -> dict:
        return await self.aggregation_service.aggregate_user_progress(session, user_id)

    async def get_user_improvements(self, session: AsyncSession, user_id: UUID) -> dict:
        return await self.aggregation_service.aggregate_user_improvements(session, user_id)

    async def get_user_skills_gap(self, session: AsyncSession, user_id: UUID) -> SkillsGapResponse:
        return await self.aggregation_service.aggregate_skills_gap(session, user_id)

    # Backward-compatible helpers (delegated)
    def _get_trend(self, current: float, previous: float) -> str:
        return self.scoring_service.calculate_trend(current, previous)

    def _aggregate_delivery(self, responses, audio_feedbacks, recent, previous):
        return self.aggregation_service._aggregate_delivery(responses, audio_feedbacks, recent, previous)

    def _aggregate_behavioral(self, responses, content_feedbacks, recent, previous):
        return self.aggregation_service._aggregate_behavioral(
            responses, content_feedbacks, recent, previous
        )

    def _aggregate_technical(self, responses, content_feedbacks, recent, previous):
        return self.aggregation_service._aggregate_technical(
            responses, content_feedbacks, recent, previous
        )

    def _compute_content_dimension(self, responses, content_feedbacks, recent, previous):
        return self.aggregation_service._compute_content_dimension(
            responses, content_feedbacks, recent, previous
        )

    def _compute_delivery_dimension(self, responses, audio_feedbacks, recent, previous):
        return self.aggregation_service._compute_delivery_dimension(
            responses, audio_feedbacks, recent, previous
        )

    def _compute_behavioral_dimension(self, responses, content_feedbacks, recent, previous):
        return self.aggregation_service._compute_behavioral_dimension(
            responses, content_feedbacks, recent, previous
        )

    def _compute_technical_dimension(self, responses, content_feedbacks, recent, previous):
        return self.aggregation_service._compute_technical_dimension(
            responses, content_feedbacks, recent, previous
        )

    def _compute_system_design_dimension(self, responses, content_feedbacks, recent, previous):
        return self.aggregation_service._compute_system_design_dimension(
            responses, content_feedbacks, recent, previous
        )

    def _compute_communication_dimension(self, responses, content_feedbacks, recent, previous):
        return self.aggregation_service._compute_communication_dimension(
            responses, content_feedbacks, recent, previous
        )
