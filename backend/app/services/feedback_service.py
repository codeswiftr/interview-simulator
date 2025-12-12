"""Feedback generation service for interview responses."""

from collections import Counter
from pathlib import Path
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.content_analyzer import ContentAnalyzer
from app.models.feedback import AudioFeedback, ContentFeedback, SessionFeedback, VideoFeedback
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    ProcessingStatus,
)
from app.models.question import Question
from app.models.user import User
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
                experience_level = (
                    user.experience_level.value
                    if hasattr(user.experience_level, "value")
                    else user.experience_level
                )

        # Analyze content using Claude
        # Note: question.category is already a string, not an enum
        question_type = (
            question.category.value if hasattr(question.category, "value") else question.category
        )
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

        # Create session feedback
        session_feedback = SessionFeedback(
            session_id=session_id,
            overall_score=overall_score,
            audio_score=avg_audio_score,
            content_score=avg_content_score,
            top_strengths=top_strengths,
            top_improvements=top_improvements,
            recommended_practice_areas=practice_areas,
            next_question_ids=[],  # TODO: Implement intelligent question recommendations
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
