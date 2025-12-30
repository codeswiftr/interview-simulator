"""Feedback generation service for interview responses."""

from collections import Counter
from pathlib import Path
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.content_analyzer import ContentAnalyzer
from app.models.feedback import (
    AudioFeedback,
    ContentFeedback,
    SessionFeedback,
    SkillDimension,
    SkillsGapResponse,
    VideoFeedback,
)
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    ProcessingStatus,
)
from app.models.question import Question
from app.models.user import User
from app.services.question_recommender import recommend_next_questions
from app.services.video_service import VideoService


class FeedbackService:
    """Service for generating and managing interview feedback.

    Handles:
    - Content analysis of individual responses
    - Session-level feedback aggregation
    - Score calculation and storage
    """

    def __init__(self) -> None:
        """Initialize feedback service with content analyzer."""
        self.content_analyzer = ContentAnalyzer()
        self.video_service = VideoService()

    async def generate_feedback(self, session: AsyncSession, response_id: UUID) -> ContentFeedback:
        """Generate feedback for a single interview response.

        Args:
            session: Database session
            response_id: UUID of the response to analyze

        Returns:
            ContentFeedback record with analysis results

        Raises:
            ValueError: If response not found or missing required data
        """
        # Fetch the response
        result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.id == response_id)
        )
        response = result.first()
        if not response:
            raise ValueError(f"Response {response_id} not found")

        # Check if feedback already exists
        existing_feedback = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id == response_id)
        )
        if existing_feedback.first():
            raise ValueError(f"Feedback already exists for response {response_id}")

        # Verify we have transcript
        if not response.transcript:
            raise ValueError(f"Response {response_id} has no transcript to analyze")

        # Fetch the question to get its type
        question_result = await session.exec(
            select(Question).where(Question.id == response.question_id)
        )
        question = question_result.first()
        if not question:
            raise ValueError(f"Question {response.question_id} not found")

        # Fetch the interview session to get user_id
        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == response.session_id)
        )
        interview = interview_result.first()

        # Fetch the user's experience level
        experience_level = "mid"  # Default
        if interview:
            user_result = await session.exec(select(User).where(User.id == interview.user_id))
            user = user_result.first()
            if user and user.experience_level:
                # Handle both enum and string values
                experience_level = str(user.experience_level)

        # Analyze content using Claude
        # Note: question.category comes from DB as string
        question_type = str(question.category) if question.category else "behavioral"
        metrics = await self.content_analyzer.analyze(
            question=question.content,
            transcript=response.transcript,
            question_type=question_type,
            experience_level=experience_level,
        )

        # Calculate overall score
        overall_score = self.content_analyzer.calculate_overall_score(metrics, question_type)

        # Create feedback record
        feedback = ContentFeedback(
            response_id=response_id,
            technical_accuracy=metrics.technical_accuracy,
            star_adherence=metrics.star_adherence,
            answer_structure=metrics.answer_structure,
            completeness=metrics.completeness,
            relevance=metrics.relevance,
            overall_content_score=overall_score,
            strengths=metrics.strengths,
            improvements=metrics.improvements,
            detailed_feedback=metrics.detailed_feedback,
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        return feedback

    async def generate_session_feedback(
        self, session: AsyncSession, session_id: UUID
    ) -> SessionFeedback:
        """Generate aggregated feedback for entire interview session.

        Args:
            session: Database session
            session_id: UUID of the interview session

        Returns:
            SessionFeedback with aggregated scores and recommendations

        Raises:
            ValueError: If session not found or has no responses
        """
        # Verify session exists
        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        interview = interview_result.first()
        if not interview:
            raise ValueError(f"Interview session {session_id} not found")

        # Check if session feedback already exists
        existing_session_feedback = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == session_id)
        )
        if existing_session_feedback.first():
            raise ValueError(f"Session feedback already exists for session {session_id}")

        # Get all responses for this session
        responses_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.session_id == session_id)
        )
        responses = list(responses_result.all())

        if not responses:
            raise ValueError(f"No responses found for session {session_id}")

        # Generate feedback for any responses that don't have it
        for response in responses:
            existing_feedback = await session.exec(
                select(ContentFeedback).where(ContentFeedback.response_id == response.id)
            )
            if not existing_feedback.first() and response.transcript:
                try:
                    await self.generate_feedback(session, response.id)
                except ValueError as e:
                    # Skip responses that can't be analyzed
                    print(f"Skipping response {response.id}: {e}")
                    continue

        # Fetch all content feedback for responses
        feedback_results = await session.exec(
            select(ContentFeedback)
            .join(InterviewResponse, ContentFeedback.response_id == InterviewResponse.id)
            .where(InterviewResponse.session_id == session_id)
        )
        all_feedback = list(feedback_results.all())

        if not all_feedback:
            raise ValueError(f"No feedback could be generated for session {session_id}")

        # Calculate aggregated scores
        content_scores = [f.overall_content_score for f in all_feedback]
        avg_content_score = sum(content_scores) / len(content_scores)

        # Get audio feedback for all responses
        audio_feedback_results = await session.exec(
            select(AudioFeedback)
            .join(InterviewResponse, AudioFeedback.response_id == InterviewResponse.id)
            .where(InterviewResponse.session_id == session_id)
        )
        all_audio_feedback = list(audio_feedback_results.all())

        # Calculate average audio score
        if all_audio_feedback:
            audio_scores = [f.overall_audio_score for f in all_audio_feedback]
            avg_audio_score = sum(audio_scores) / len(audio_scores)
        else:
            # No audio feedback available (e.g., no audio files uploaded)
            avg_audio_score = 0.0

        # Overall score is weighted average (80% content, 20% audio)
        overall_score = avg_content_score * 0.8 + avg_audio_score * 0.2

        # Aggregate strengths and improvements
        all_strengths = [strength for f in all_feedback for strength in f.strengths]
        all_improvements = [improvement for f in all_feedback for improvement in f.improvements]

        # Get top 3 most common strengths and improvements
        strength_counter = Counter(all_strengths)
        improvement_counter = Counter(all_improvements)

        top_strengths = [item for item, _ in strength_counter.most_common(3)]
        top_improvements = [item for item, _ in improvement_counter.most_common(3)]

        # Determine recommended practice areas based on weak scores
        practice_areas = []
        avg_technical = sum(f.technical_accuracy for f in all_feedback) / len(all_feedback)
        avg_structure = sum(f.answer_structure for f in all_feedback) / len(all_feedback)
        avg_completeness = sum(f.completeness for f in all_feedback) / len(all_feedback)
        avg_star = sum(f.star_adherence for f in all_feedback if f.star_adherence > 0) / max(
            1, len([f for f in all_feedback if f.star_adherence > 0])
        )

        if avg_technical < 70:
            practice_areas.append("Technical accuracy and depth")
        if avg_structure < 70:
            practice_areas.append("Answer structure and organization")
        if avg_completeness < 70:
            practice_areas.append("Completeness and thoroughness")
        if avg_star < 70 and avg_star > 0:
            practice_areas.append("STAR method application")

        # Get recommended next questions based on the last response
        next_question_ids: list[str] = []
        if responses:
            last_response = responses[-1]
            try:
                next_question_ids = await recommend_next_questions(
                    session=session,
                    user_id=interview.user_id,
                    question_id=last_response.question_id,
                    feedback_score=overall_score,
                )
            except Exception:
                # Fallback to empty if recommendation fails
                pass

        # Create session feedback
        session_feedback = SessionFeedback(
            session_id=session_id,
            overall_score=overall_score,
            audio_score=avg_audio_score,
            content_score=avg_content_score,
            top_strengths=top_strengths,
            top_improvements=top_improvements,
            recommended_practice_areas=practice_areas,
            next_question_ids=next_question_ids,
        )

        session.add(session_feedback)

        # Update interview session with scores
        interview.overall_score = overall_score
        interview.audio_score = avg_audio_score
        interview.content_score = avg_content_score
        interview.status = InterviewStatus.ANALYZED

        await session.commit()
        await session.refresh(session_feedback)

        return session_feedback

    async def get_response_feedback(
        self, session: AsyncSession, response_id: UUID
    ) -> ContentFeedback | None:
        """Retrieve feedback for a specific response.

        Args:
            session: Database session
            response_id: UUID of the response

        Returns:
            ContentFeedback if exists, None otherwise
        """
        result = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id == response_id)
        )
        return result.first()

    async def get_video_feedback(
        self, session: AsyncSession, response_id: UUID
    ) -> VideoFeedback | None:
        """Retrieve video feedback for a specific response."""
        result = await session.exec(
            select(VideoFeedback).where(VideoFeedback.response_id == response_id)
        )
        return result.first()

    async def generate_video_feedback(
        self, session: AsyncSession, response_id: UUID
    ) -> VideoFeedback:
        """Analyze stored video and create VideoFeedback."""
        # Verify response exists and has a video attached
        response_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.id == response_id)
        )
        response = response_result.first()
        if not response:
            raise ValueError(f"Response {response_id} not found")
        if not response.video_url:
            raise ValueError("Response has no video attached")

        existing = await session.exec(
            select(VideoFeedback).where(VideoFeedback.response_id == response_id)
        )
        if existing.first():
            raise ValueError(f"Video feedback already exists for response {response_id}")

        video_path = Path(response.video_url.lstrip("/"))
        if not video_path.exists():
            backend_relative = Path("backend") / video_path
            if backend_relative.exists():
                video_path = backend_relative
            else:
                raise ValueError(f"Video file not found at {response.video_url}")

        feedback = await self.video_service.process_response_video(
            session, response_id, str(video_path)
        )
        return feedback

    async def get_session_feedback(
        self, session: AsyncSession, session_id: UUID
    ) -> SessionFeedback | None:
        """Retrieve aggregated feedback for a session.

        Args:
            session: Database session
            session_id: UUID of the interview session

        Returns:
            SessionFeedback if exists, None otherwise
        """
        result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == session_id)
        )
        return result.first()

    async def get_all_session_feedbacks(
        self, session: AsyncSession, session_id: UUID
    ) -> list[ContentFeedback]:
        """Retrieve all response feedbacks for a session.

        Args:
            session: Database session
            session_id: UUID of the interview session

        Returns:
            List of ContentFeedback records for all responses in session
        """
        result = await session.exec(
            select(ContentFeedback)
            .join(InterviewResponse, ContentFeedback.response_id == InterviewResponse.id)
            .where(InterviewResponse.session_id == session_id)
            .order_by(InterviewResponse.created_at)
        )
        return list(result.all())

    async def get_processing_summary(self, session: AsyncSession, session_id: UUID) -> dict:
        """Get processing status summary for a session.

        Returns counts of responses by processing_status, whether session feedback exists,
        and whether all responses are fully processed.

        Args:
            session: Database session
            session_id: UUID of the interview session

        Returns:
            Dictionary with processing status summary
        """
        # Get all responses for this session
        responses_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.session_id == session_id)
        )
        responses = list(responses_result.all())

        # Count responses by status
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

        # Check if session feedback exists
        session_feedback_result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == session_id)
        )
        has_session_feedback = session_feedback_result.first() is not None

        # Determine if all responses are fully processed
        total_responses = len(responses)
        completed_or_failed = (
            status_counts[ProcessingStatus.COMPLETED] + status_counts[ProcessingStatus.FAILED]
        )
        all_processed = total_responses > 0 and completed_or_failed == total_responses

        # Determine current step
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

    async def get_user_progress(self, session: AsyncSession, user_id: UUID) -> dict:
        """Get aggregate progress metrics for a user.

        Returns last N sessions' scores, average audio/content scores,
        and top recurring recommended practice areas.

        Args:
            session: Database session
            user_id: UUID of the user

        Returns:
            Dictionary with progress metrics
        """
        from app.models.interview import InterviewSession, InterviewStatus

        # Get last 10 completed sessions
        sessions_result = await session.exec(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
            )
            .order_by(InterviewSession.created_at.desc())
            .limit(10)
        )
        sessions = list(sessions_result.all())

        if not sessions:
            return {
                "recommended_practice_areas": [],
                "average_audio_score": None,
                "average_content_score": None,
            }

        # Get session feedbacks
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

        # Calculate averages
        audio_scores = [f.audio_score for f in feedbacks if f.audio_score is not None]
        content_scores = [f.content_score for f in feedbacks if f.content_score is not None]

        avg_audio = sum(audio_scores) / len(audio_scores) if audio_scores else None
        avg_content = sum(content_scores) / len(content_scores) if content_scores else None

        # Aggregate recommended practice areas (most common across sessions)
        all_practice_areas = []
        for f in feedbacks:
            all_practice_areas.extend(f.recommended_practice_areas)

        practice_area_counter = Counter(all_practice_areas)
        top_practice_areas = [area for area, _ in practice_area_counter.most_common(3)]

        return {
            "recommended_practice_areas": top_practice_areas,
            "average_audio_score": round(avg_audio, 1) if avg_audio else None,
            "average_content_score": round(avg_content, 1) if avg_content else None,
        }

    async def get_user_improvements(self, session: AsyncSession, user_id: UUID) -> dict:
        """Aggregate improvement metrics by criteria category.

        Analyzes last 10 completed sessions, comparing recent (5) vs previous (5)
        to determine trends and extract actionable insights.

        Categories:
        - Delivery: Audio metrics (speech rate, filler words, confidence, volume)
        - Behavioral: STAR adherence, structure (behavioral questions only)
        - Technical: Accuracy, completeness (technical/system_design questions)

        Args:
            session: Database session
            user_id: UUID of the user

        Returns:
            Dictionary with delivery, behavioral, technical improvement data
        """
        # Get last 10 completed sessions
        sessions_result = await session.exec(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
            )
            .order_by(InterviewSession.created_at.desc())
            .limit(10)
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

        # Split into recent (first 5) vs previous (remaining)
        recent_sessions = sessions[:5]
        previous_sessions = sessions[5:] if len(sessions) > 5 else sessions[len(sessions) // 2 :]

        # Get all session IDs
        session_ids = [s.id for s in sessions]

        # Get responses with their questions (for category filtering)
        responses_result = await session.exec(
            select(InterviewResponse, Question)
            .join(Question, InterviewResponse.question_id == Question.id)
            .where(InterviewResponse.session_id.in_(session_ids))
        )
        responses_with_questions = list(responses_result.all())

        # Get response IDs for feedback lookup
        response_ids = [r.id for r, _ in responses_with_questions]

        # Get content feedbacks
        content_feedbacks_result = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id.in_(response_ids))
        )
        content_feedbacks = {cf.response_id: cf for cf in content_feedbacks_result.all()}

        # Get audio feedbacks
        audio_feedbacks_result = await session.exec(
            select(AudioFeedback).where(AudioFeedback.response_id.in_(response_ids))
        )
        audio_feedbacks = {af.response_id: af for af in audio_feedbacks_result.all()}

        # Aggregate by category
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

    def _aggregate_delivery(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        audio_feedbacks: dict[UUID, AudioFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> dict | None:
        """Aggregate delivery metrics from AudioFeedback."""
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

            # Calculate weighted delivery score
            score = (
                (af.speech_rate_score or 0) * 0.25
                + (af.filler_word_score or 0) * 0.25
                + (af.confidence_score or 0) * 0.25
                + (af.volume_consistency or 0) * 0.25
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

            # Extract insights from audio metrics
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

        # Determine trend
        if current > prev + 2:
            trend = "improving"
        elif current < prev - 2:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "current_score": round(current, 1),
            "previous_score": round(prev, 1),
            "trend": trend,
            "improvements": list(dict.fromkeys(all_improvements))[:3],  # Unique, max 3
            "areas_to_work_on": list(dict.fromkeys(all_areas))[:3],
        }

    def _aggregate_behavioral(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> dict | None:
        """Aggregate behavioral metrics from ContentFeedback where category='behavioral'."""
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        all_improvements: list[str] = []
        all_areas: list[str] = []

        for response, question in responses:
            # Only behavioral questions
            if str(question.category) != "behavioral":
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            # Calculate weighted behavioral score
            score = (
                (cf.star_adherence or 0) * 0.4
                + (cf.answer_structure or 0) * 0.35
                + (cf.completeness or 0) * 0.25
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

            # Extract insights
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

            # Extract from strengths/improvements lists
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

        if current > prev + 2:
            trend = "improving"
        elif current < prev - 2:
            trend = "declining"
        else:
            trend = "stable"

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
        """Aggregate technical metrics from ContentFeedback for technical/system_design questions."""
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        all_improvements: list[str] = []
        all_areas: list[str] = []

        for response, question in responses:
            # Only technical and system_design questions
            category = str(question.category)
            if category not in ("technical", "system_design"):
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            # Calculate weighted technical score
            score = (
                (cf.technical_accuracy or 0) * 0.4
                + (cf.completeness or 0) * 0.35
                + (cf.relevance or 0) * 0.25
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

            # Extract insights
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

            # Extract from strengths/improvements lists
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

        if current > prev + 2:
            trend = "improving"
        elif current < prev - 2:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "current_score": round(current, 1),
            "previous_score": round(prev, 1),
            "trend": trend,
            "improvements": list(dict.fromkeys(all_improvements))[:3],
            "areas_to_work_on": list(dict.fromkeys(all_areas))[:3],
        }

    async def get_user_skills_gap(self, session: AsyncSession, user_id: UUID) -> SkillsGapResponse:
        """Compute skills gap analysis for a user.

        Returns 6 skill dimensions computed from the user's interview sessions:
        - Content: Overall content quality (avg ContentFeedback.overall_content_score)
        - Delivery: Audio quality (avg AudioFeedback.overall_audio_score)
        - Behavioral: STAR + structure (behavioral questions only)
        - Technical: Technical accuracy (technical questions only)
        - System Design: System design skills (system_design questions only)
        - Communication: Clarity proxy (relevance + structure average)

        Args:
            session: Database session
            user_id: UUID of the user

        Returns:
            SkillsGapResponse with 6 dimensions and metadata
        """
        from datetime import UTC

        # Get last 20 completed sessions (limit for performance)
        sessions_result = await session.exec(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status.in_([InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]),
            )
            .order_by(InterviewSession.created_at.desc())
            .limit(20)
        )
        all_sessions = list(sessions_result.all())

        if len(all_sessions) < 2:
            return SkillsGapResponse(
                dimensions=[],
                sessions_analyzed=len(all_sessions),
                data_available=False,
                last_updated=None,
            )

        # Split into recent (first 5) vs previous (remaining) for trend
        recent_sessions = all_sessions[:5]
        previous_sessions = all_sessions[5:] if len(all_sessions) > 5 else all_sessions[len(all_sessions) // 2 :]

        # Get all session IDs
        session_ids = [s.id for s in all_sessions]

        # Get responses with their questions (for category filtering)
        responses_result = await session.exec(
            select(InterviewResponse, Question)
            .join(Question, InterviewResponse.question_id == Question.id)
            .where(InterviewResponse.session_id.in_(session_ids))
        )
        responses_with_questions = list(responses_result.all())

        # Get response IDs for feedback lookup
        response_ids = [r.id for r, _ in responses_with_questions]

        # Get content feedbacks
        content_feedbacks_result = await session.exec(
            select(ContentFeedback).where(ContentFeedback.response_id.in_(response_ids))
        )
        content_feedbacks = {cf.response_id: cf for cf in content_feedbacks_result.all()}

        # Get audio feedbacks
        audio_feedbacks_result = await session.exec(
            select(AudioFeedback).where(AudioFeedback.response_id.in_(response_ids))
        )
        audio_feedbacks = {af.response_id: af for af in audio_feedbacks_result.all()}

        # Compute each dimension
        dimensions = []

        # 1. Content dimension
        content_dim = self._compute_content_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if content_dim:
            dimensions.append(content_dim)

        # 2. Delivery dimension
        delivery_dim = self._compute_delivery_dimension(
            responses_with_questions, audio_feedbacks, recent_sessions, previous_sessions
        )
        if delivery_dim:
            dimensions.append(delivery_dim)

        # 3. Behavioral dimension
        behavioral_dim = self._compute_behavioral_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if behavioral_dim:
            dimensions.append(behavioral_dim)

        # 4. Technical dimension
        technical_dim = self._compute_technical_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if technical_dim:
            dimensions.append(technical_dim)

        # 5. System Design dimension
        system_design_dim = self._compute_system_design_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if system_design_dim:
            dimensions.append(system_design_dim)

        # 6. Communication dimension
        communication_dim = self._compute_communication_dimension(
            responses_with_questions, content_feedbacks, recent_sessions, previous_sessions
        )
        if communication_dim:
            dimensions.append(communication_dim)

        # Get latest session timestamp for last_updated
        last_updated = all_sessions[0].created_at if all_sessions else None
        # Ensure timezone awareness
        if last_updated and last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=UTC)

        return SkillsGapResponse(
            dimensions=dimensions,
            sessions_analyzed=len(all_sessions),
            data_available=len(dimensions) > 0,
            last_updated=last_updated,
        )

    def _compute_content_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        """Compute Content dimension from overall_content_score."""
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

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self._get_trend(current, prev)

        return SkillDimension(
            name="Content",
            current_score=round(current, 1),
            target_score=90,
            sessions_with_data=len(sessions_with_data),
            trend=trend,
        )

    def _compute_delivery_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        audio_feedbacks: dict[UUID, AudioFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        """Compute Delivery dimension from overall_audio_score."""
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

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self._get_trend(current, prev)

        return SkillDimension(
            name="Delivery",
            current_score=round(current, 1),
            target_score=85,
            sessions_with_data=len(sessions_with_data),
            trend=trend,
        )

    def _compute_behavioral_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        """Compute Behavioral dimension (behavioral questions only).

        Score = 40% STAR adherence + 35% answer_structure + 25% completeness
        """
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, question in responses:
            # Only behavioral questions
            if str(question.category) != "behavioral":
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            # Weighted score for behavioral
            score = (
                (cf.star_adherence or 0) * 0.4
                + (cf.answer_structure or 0) * 0.35
                + (cf.completeness or 0) * 0.25
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self._get_trend(current, prev)

        return SkillDimension(
            name="Behavioral",
            current_score=round(current, 1),
            target_score=90,
            sessions_with_data=len(sessions_with_data),
            trend=trend,
        )

    def _compute_technical_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        """Compute Technical dimension (technical + system_design questions).

        Score = 40% technical_accuracy + 35% completeness + 25% relevance
        """
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, question in responses:
            # Only technical and system_design questions
            category = str(question.category)
            if category not in ("technical", "system_design"):
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            # Weighted score for technical
            score = (
                (cf.technical_accuracy or 0) * 0.4
                + (cf.completeness or 0) * 0.35
                + (cf.relevance or 0) * 0.25
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self._get_trend(current, prev)

        return SkillDimension(
            name="Technical",
            current_score=round(current, 1),
            target_score=85,
            sessions_with_data=len(sessions_with_data),
            trend=trend,
        )

    def _compute_system_design_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        """Compute System Design dimension (system_design questions only).

        Score = 40% technical_accuracy + 35% completeness + 25% relevance
        """
        recent_ids = {s.id for s in recent}
        previous_ids = {s.id for s in previous}

        recent_scores: list[float] = []
        previous_scores: list[float] = []
        sessions_with_data: set[UUID] = set()

        for response, question in responses:
            # Only system_design questions
            if str(question.category) != "system_design":
                continue

            cf = content_feedbacks.get(response.id)
            if not cf:
                continue

            sessions_with_data.add(response.session_id)
            # Weighted score for system design
            score = (
                (cf.technical_accuracy or 0) * 0.4
                + (cf.completeness or 0) * 0.35
                + (cf.relevance or 0) * 0.25
            )

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self._get_trend(current, prev)

        return SkillDimension(
            name="System Design",
            current_score=round(current, 1),
            target_score=80,
            sessions_with_data=len(sessions_with_data),
            trend=trend,
        )

    def _compute_communication_dimension(
        self,
        responses: list[tuple[InterviewResponse, Question]],
        content_feedbacks: dict[UUID, ContentFeedback],
        recent: list[InterviewSession],
        previous: list[InterviewSession],
    ) -> SkillDimension | None:
        """Compute Communication dimension (clarity proxy).

        Score = 50% relevance + 50% answer_structure
        """
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
            # Clarity proxy: relevance + structure average
            score = ((cf.relevance or 0) * 0.5 + (cf.answer_structure or 0) * 0.5)

            if response.session_id in recent_ids:
                recent_scores.append(score)
            elif response.session_id in previous_ids:
                previous_scores.append(score)

        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        prev = sum(previous_scores) / len(previous_scores) if previous_scores else current
        trend = self._get_trend(current, prev)

        return SkillDimension(
            name="Communication",
            current_score=round(current, 1),
            target_score=90,
            sessions_with_data=len(sessions_with_data),
            trend=trend,
        )

    def _get_trend(self, current: float, previous: float) -> str:
        """Determine trend based on score difference."""
        if current > previous + 2:
            return "improving"
        elif current < previous - 2:
            return "declining"
        return "stable"
