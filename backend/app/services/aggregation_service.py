"""Aggregation service for feedback data."""

from __future__ import annotations

from collections import Counter
from datetime import UTC
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.feedback import (
    AudioFeedback,
    ContentFeedback,
    SessionFeedback,
    SkillDimension,
    SkillsGapResponse,
)
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    ProcessingStatus,
)
from app.models.question import Question
from app.services.scoring_service import ScoringService


class AggregationService:
    """Service for aggregating feedback across responses and sessions."""

    def __init__(self, scoring_service: ScoringService) -> None:
        self.scoring_service = scoring_service

    async def aggregate_session_feedback(
        self,
        session: AsyncSession,
        interview_session: InterviewSession,
        content_feedbacks: list[ContentFeedback],
        audio_feedbacks: list[AudioFeedback],
    ) -> SessionFeedback:
        content_scores = [f.overall_content_score for f in content_feedbacks]
        avg_content_score = sum(content_scores) / len(content_scores) if content_scores else 0.0

        audio_scores = [f.overall_audio_score for f in audio_feedbacks]
        avg_audio_score = sum(audio_scores) / len(audio_scores) if audio_scores else 0.0

        overall_score = self.scoring_service.calculate_overall_score(
            avg_content_score, avg_audio_score, content_weight=0.8, audio_weight=0.2
        )

        top_strengths, top_improvements = self.aggregate_strengths_and_improvements(content_feedbacks)
        practice_areas = self.determine_practice_areas(content_feedbacks)

        feedback = SessionFeedback(
            session_id=interview_session.id,
            overall_score=overall_score,
            audio_score=avg_audio_score,
            content_score=avg_content_score,
            top_strengths=top_strengths,
            top_improvements=top_improvements,
            recommended_practice_areas=practice_areas,
            next_question_ids=[],
        )
        return feedback

    async def aggregate_user_progress(
        self, session: AsyncSession, user_id: UUID, limit: int = 10
    ) -> dict:
        sessions_result = await session.exec(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
            )
            .order_by(InterviewSession.created_at.desc())
            .limit(limit)
        )
        sessions = list(sessions_result.all())

        if not sessions:
            return {
                "recommended_practice_areas": [],
                "average_audio_score": None,
                "average_content_score": None,
            }

        session_ids = [s.id for s in sessions]
        feedbacks_result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id.in_(session_ids))
        )
        feedbacks = list(feedbacks_result.all())

        if not feedbacks:
            return {
                "recommended_practice_areas": [],
                "average_audio_score": None,
                "average_content_score": None,
            }

        audio_scores = [f.audio_score for f in feedbacks if f.audio_score is not None]
        content_scores = [f.content_score for f in feedbacks if f.content_score is not None]

        avg_audio = sum(audio_scores) / len(audio_scores) if audio_scores else None
        avg_content = sum(content_scores) / len(content_scores) if content_scores else None

        all_practice_areas: list[str] = []
        for f in feedbacks:
            all_practice_areas.extend(f.recommended_practice_areas)

        practice_area_counter = Counter(all_practice_areas)
        top_practice_areas = [area for area, _ in practice_area_counter.most_common(3)]

        return {
            "recommended_practice_areas": top_practice_areas,
            "average_audio_score": round(avg_audio, 1) if avg_audio is not None else None,
            "average_content_score": round(avg_content, 1) if avg_content is not None else None,
        }

    async def aggregate_user_improvements(
        self, session: AsyncSession, user_id: UUID, limit: int = 10
    ) -> dict:
        sessions_result = await session.exec(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
            )
            .order_by(InterviewSession.created_at.desc())
            .limit(limit)
        )
        sessions = list(sessions_result.all())

        if len(sessions) < 2:
            return {
                "delivery": None,
                "behavioral": None,
                "technical": None,
                "sessions_analyzed": len(sessions),
                "data_available": False,
            }

        recent_sessions, previous_sessions = _split_sessions(sessions)
        session_ids = [s.id for s in sessions]

        responses_result = await session.exec(
            select(InterviewResponse, Question)
            .join(Question, InterviewResponse.question_id == Question.id)
            .where(InterviewResponse.session_id.in_(session_ids))
        )
        responses_with_questions = list(responses_result.all())

        response_ids = [r.id for r, _ in responses_with_questions]

        content_feedbacks_result = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id.in_(response_ids))
        )
        content_feedbacks = {cf.response_id: cf for cf in content_feedbacks_result.all()}

        audio_feedbacks_result = await session.exec(
            select(AudioFeedback).where(AudioFeedback.response_id.in_(response_ids))
        )
        audio_feedbacks = {af.response_id: af for af in audio_feedbacks_result.all()}

        delivery = self._aggregate_delivery(
            responses_with_questions, audio_feedbacks, recent_sessions, previous_sessions
        )
        behavioral = self._aggregate_behavioral(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        technical = self._aggregate_technical(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )

        return {
            "delivery": delivery,
            "behavioral": behavioral,
            "technical": technical,
            "sessions_analyzed": len(sessions),
            "data_available": True,
        }

    async def aggregate_skills_gap(
        self, session: AsyncSession, user_id: UUID, limit: int = 20
    ) -> SkillsGapResponse:
        sessions_result = await session.exec(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
            )
            .order_by(InterviewSession.created_at.desc())
            .limit(limit)
        )
        all_sessions = list(sessions_result.all())

        if len(all_sessions) < 2:
            return SkillsGapResponse(
                dimensions=[],
                sessions_analyzed=len(all_sessions),
                data_available=False,
                last_updated=None,
            )

        recent_sessions, previous_sessions = _split_sessions(all_sessions, recent_count=5)
        session_ids = [s.id for s in all_sessions]

        responses_result = await session.exec(
            select(InterviewResponse, Question)
            .join(Question, InterviewResponse.question_id == Question.id)
            .where(InterviewResponse.session_id.in_(session_ids))
        )
        responses_with_questions = list(responses_result.all())

        response_ids = [r.id for r, _ in responses_with_questions]

        content_feedbacks_result = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id.in_(response_ids))
        )
        content_feedbacks = {cf.response_id: cf for cf in content_feedbacks_result.all()}

        audio_feedbacks_result = await session.exec(
            select(AudioFeedback).where(AudioFeedback.response_id.in_(response_ids))
        )
        audio_feedbacks = {af.response_id: af for af in audio_feedbacks_result.all()}

        dimensions: list[SkillDimension] = []

        content_dim = self._compute_content_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if content_dim:
            dimensions.append(content_dim)

        delivery_dim = self._compute_delivery_dimension(
            responses_with_questions, audio_feedbacks, recent_sessions, previous_sessions
        )
        if delivery_dim:
            dimensions.append(delivery_dim)

        behavioral_dim = self._compute_behavioral_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if behavioral_dim:
            dimensions.append(behavioral_dim)

        technical_dim = self._compute_technical_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if technical_dim:
            dimensions.append(technical_dim)

        system_design_dim = self._compute_system_design_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if system_design_dim:
            dimensions.append(system_design_dim)

        communication_dim = self._compute_communication_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if communication_dim:
            dimensions.append(communication_dim)

        last_updated = all_sessions[0].created_at if all_sessions else None
        if last_updated and last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=UTC)

        return SkillsGapResponse(
            dimensions=dimensions,
            sessions_analyzed=len(all_sessions),
            data_available=len(dimensions) > 0,
            last_updated=last_updated,
        )

    async def aggregate_processing_status(self, session: AsyncSession, session_id: UUID) -> dict:
        responses_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.session_id == session_id)
        )
        responses = list(responses_result.all())

        status_counts = {
            ProcessingStatus.PENDING: 0,
            ProcessingStatus.TRANSCRIBING: 0,
            ProcessingStatus.ANALYZING: 0,
            ProcessingStatus.COMPLETED: 0,
            ProcessingStatus.FAILED: 0,
        }

        for response in responses:
            status = response.processing_status
            if status in status_counts:
                status_counts[status] += 1

        session_feedback_result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == session_id)
        )
        has_session_feedback = session_feedback_result.first() is not None

        total_responses = len(responses)
        completed_or_failed = (
            status_counts[ProcessingStatus.COMPLETED] + status_counts[ProcessingStatus.FAILED]
        )
        all_processed = total_responses > 0 and completed_or_failed == total_responses

        current_step = "idle"
        if status_counts[ProcessingStatus.TRANSCRIBING] > 0:
            current_step = "transcribing"
        elif status_counts[ProcessingStatus.ANALYZING] > 0:
            current_step = "analyzing"
        elif status_counts[ProcessingStatus.COMPLETED] > 0 and not has_session_feedback:
            current_step = "generating_feedback"
        elif has_session_feedback:
            current_step = "complete"
        elif status_counts[ProcessingStatus.FAILED] > 0 and completed_or_failed == total_responses:
            current_step = "failed"

        return {
            "status_counts": {
                "pending": status_counts[ProcessingStatus.PENDING],
                "transcribing": status_counts[ProcessingStatus.TRANSCRIBING],
                "analyzing": status_counts[ProcessingStatus.ANALYZING],
                "completed": status_counts[ProcessingStatus.COMPLETED],
                "failed": status_counts[ProcessingStatus.FAILED],
            },
            "total_responses": total_responses,
            "has_session_feedback": has_session_feedback,
            "all_processed": all_processed,
            "current_step": current_step,
        }

    def aggregate_strengths_and_improvements(
        self, feedbacks: list[ContentFeedback], top_n: int = 3
    ) -> tuple[list[str], list[str]]:
        all_strengths = [strength for f in feedbacks for strength in f.strengths]
        all_improvements = [improvement for f in feedbacks for improvement in f.improvements]

        strength_counter = Counter(all_strengths)
        improvement_counter = Counter(all_improvements)

        top_strengths = [item for item, _ in strength_counter.most_common(top_n)]
        top_improvements = [item for item, _ in improvement_counter.most_common(top_n)]

        return top_strengths, top_improvements

    def determine_practice_areas(
        self, feedbacks: list[ContentFeedback], threshold: float = 70.0
    ) -> list[str]:
        if not feedbacks:
            return []

        avg_technical = sum(f.technical_accuracy for f in feedbacks) / len(feedbacks)
        avg_structure = sum(f.answer_structure for f in feedbacks) / len(feedbacks)
        avg_completeness = sum(f.completeness for f in feedbacks) / len(feedbacks)

        star_scores = [f.star_adherence for f in feedbacks if f.star_adherence > 0]
        avg_star = sum(star_scores) / len(star_scores) if star_scores else 0

        practice_areas: list[str] = []

        if avg_technical < threshold:
            practice_areas.append("Technical accuracy and depth")
        if avg_structure < threshold:
            practice_areas.append("Answer structure and organization")
        if avg_completeness < threshold:
            practice_areas.append("Completeness and thoroughness")
        if avg_star < threshold and avg_star > 0:
            practice_areas.append("STAR method application")

        return practice_areas

    def _aggregate_delivery(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        audio_feedbacks: dict[UUID, AudioFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> dict | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        all_improvements: list[str] = []
        all_areas: list[str] = []

        for response, _question in responses:
            af = audio_feedbacks.get(response.id)
            if not af:
                continue

            score = self.scoring_service.calculate_delivery_score(
                af.speech_rate_score,
                af.filler_word_score,
                af.confidence_score,
                af.volume_consistency,
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

            if af.filler_word_score and af.filler_word_score >= 80:
                all_improvements.append("Low filler word usage")
            elif af.filler_word_score and af.filler_word_score < 60:
                total_fillers = sum(af.filler_words.values()) if af.filler_words else 0
                all_areas.append(f"Reduce filler words - {total_fillers} detected")

            if af.speech_rate_score and af.speech_rate_score >= 80:
                wpm = af.speech_rate_wpm or 130
                all_improvements.append(f"Optimal pacing at {wpm:.0f} WPM")
            elif af.speech_rate_wpm and af.speech_rate_wpm > 160:
                all_areas.append("Slow down speech pace")
            elif af.speech_rate_wpm and af.speech_rate_wpm < 110:
                all_areas.append("Speed up delivery slightly")

            if af.confidence_score and af.confidence_score >= 80:
                all_improvements.append("Strong vocal confidence")
            elif af.confidence_score and af.confidence_score < 60:
                all_areas.append("Improve vocal confidence")

            if af.volume_consistency and af.volume_consistency >= 80:
                all_improvements.append("Consistent volume levels")
            elif af.volume_consistency and af.volume_consistency < 60:
                all_areas.append("Maintain more consistent volume")

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self.scoring_service.calculate_trend(current, prev)

        return {
            "current_score": round(current, 1),
            "previous_score": round(prev, 1),
            "trend": trend,
            "improvements": list(dict.fromkeys(all_improvements))[:3],
            "areas_to_work_on": list(dict.fromkeys(all_areas))[:3],
        }

    def _aggregate_behavioral(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> dict | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        all_improvements: list[str] = []
        all_areas: list[str] = []

        for response, question in responses:
            if str(question.category) != "behavioral":
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            score = self.scoring_service.calculate_behavioral_score(
                cf.star_adherence, cf.answer_structure, cf.completeness
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

            if cf.star_adherence and cf.star_adherence >= 80:
                all_improvements.append("STAR method structure detected in most answers")
            elif cf.star_adherence and cf.star_adherence < 60:
                all_areas.append("Improve STAR method usage")

            if cf.answer_structure and cf.answer_structure >= 80:
                all_improvements.append("Clear and logical answer structure")
            elif cf.answer_structure and cf.answer_structure < 60:
                all_areas.append("Improve answer organization")

            if cf.completeness and cf.completeness >= 80:
                all_improvements.append("Comprehensive answers with good detail")
            elif cf.completeness and cf.completeness < 60:
                all_areas.append("Include more specific examples and metrics")

            if cf.strengths:
                for s in cf.strengths[:2]:
                    if "star" in s.lower() or "structure" in s.lower():
                        all_improvements.append(s)
            if cf.improvements:
                for i in cf.improvements[:2]:
                    if "star" in i.lower() or "structure" in i.lower():
                        all_areas.append(i)

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self.scoring_service.calculate_trend(current, prev)

        return {
            "current_score": round(current, 1),
            "previous_score": round(prev, 1),
            "trend": trend,
            "improvements": list(dict.fromkeys(all_improvements))[:3],
            "areas_to_work_on": list(dict.fromkeys(all_areas))[:3],
        }

    def _aggregate_technical(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> dict | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        all_improvements: list[str] = []
        all_areas: list[str] = []

        for response, question in responses:
            category = str(question.category)
            if category not in ("technical", "system_design"):
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            score = self.scoring_service.calculate_technical_score(
                cf.technical_accuracy, cf.completeness, cf.relevance
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

            if cf.technical_accuracy and cf.technical_accuracy >= 80:
                all_improvements.append("Key terminology used correctly")
            elif cf.technical_accuracy and cf.technical_accuracy < 60:
                all_areas.append("Deepen technical explanations")

            if cf.completeness and cf.completeness >= 80:
                all_improvements.append("Good problem breakdown approach")
            elif cf.completeness and cf.completeness < 60:
                all_areas.append("Provide more trade-off analysis")

            if cf.relevance and cf.relevance >= 80:
                all_improvements.append("Answers directly address the question")
            elif cf.relevance and cf.relevance < 60:
                all_areas.append("Focus more on core requirements")

            if cf.strengths:
                for s in cf.strengths[:2]:
                    if "technical" in s.lower() or "system" in s.lower() or "design" in s.lower():
                        all_improvements.append(s)
            if cf.improvements:
                for i in cf.improvements[:2]:
                    if "technical" in i.lower() or "system" in i.lower() or "design" in i.lower():
                        all_areas.append(i)

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self.scoring_service.calculate_trend(current, prev)

        return {
            "current_score": round(current, 1),
            "previous_score": round(prev, 1),
            "trend": trend,
            "improvements": list(dict.fromkeys(all_improvements))[:3],
            "areas_to_work_on": list(dict.fromkeys(all_areas))[:3],
        }

    def _compute_content_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, _question in responses:
            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            score = cf.overall_content_score

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        return self.scoring_service.evaluate_skill_dimension(
            name="Content",
            recent_scores=recent_scores,
            previous_scores=previous_scores,
            sessions_with_data=len(sessions_with_data),
            target_score=90,
        )

    def _compute_delivery_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        audio_feedbacks: dict[UUID, AudioFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, _question in responses:
            af = audio_feedbacks.get(response.id)
            if not af:
                continue

            sessions_with_data.add(response.session_id)
            score = af.overall_audio_score

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        return self.scoring_service.evaluate_skill_dimension(
            name="Delivery",
            recent_scores=recent_scores,
            previous_scores=previous_scores,
            sessions_with_data=len(sessions_with_data),
            target_score=85,
        )

    def _compute_behavioral_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, question in responses:
            if str(question.category) != "behavioral":
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            score = self.scoring_service.calculate_behavioral_score(
                cf.star_adherence, cf.answer_structure, cf.completeness
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        return self.scoring_service.evaluate_skill_dimension(
            name="Behavioral",
            recent_scores=recent_scores,
            previous_scores=previous_scores,
            sessions_with_data=len(sessions_with_data),
            target_score=90,
        )

    def _compute_technical_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, question in responses:
            category = str(question.category)
            if category not in ("technical", "system_design"):
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            score = self.scoring_service.calculate_technical_score(
                cf.technical_accuracy, cf.completeness, cf.relevance
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        return self.scoring_service.evaluate_skill_dimension(
            name="Technical",
            recent_scores=recent_scores,
            previous_scores=previous_scores,
            sessions_with_data=len(sessions_with_data),
            target_score=85,
        )

    def _compute_system_design_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, question in responses:
            if str(question.category) != "system_design":
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            score = self.scoring_service.calculate_technical_score(
                cf.technical_accuracy, cf.completeness, cf.relevance
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        return self.scoring_service.evaluate_skill_dimension(
            name="System Design",
            recent_scores=recent_scores,
            previous_scores=previous_scores,
            sessions_with_data=len(sessions_with_data),
            target_score=80,
        )

    def _compute_communication_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, _question in responses:
            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            score = (cf.relevance or 0) * 0.5 + (cf.answer_structure or 0) * 0.5

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        return self.scoring_service.evaluate_skill_dimension(
            name="Communication",
            recent_scores=recent_scores,
            previous_scores=previous_scores,
            sessions_with_data=len(sessions_with_data),
            target_score=90,
        )


def _split_sessions(
    sessions: list[InterviewSession], recent_count: int = 5
) -> tuple[list[InterviewSession], list[InterviewSession]]:
    recent_sessions = sessions[:recent_count]
    if len(sessions) > recent_count:
        previous_sessions = sessions[recent_count:]
    else:
        previous_sessions = sessions[len(sessions) // 2 :]
    return recent_sessions, previous_sessions
