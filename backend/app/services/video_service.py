"""Video processing service that extracts engagement and eye-contact metrics."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.video_analyzer import VideoAnalyzer, VideoMetrics
from app.models.feedback import VideoFeedback
from app.models.interview import InterviewResponse

logger = logging.getLogger(__name__)


class VideoService:
    """Orchestrates lightweight video analysis for interview responses."""

    def __init__(self) -> None:
        self.analyzer = VideoAnalyzer()

    async def process_response_video(
        self,
        session: AsyncSession,
        response_id: UUID,
        video_path: str,
    ) -> VideoFeedback:
        """Analyze a response video and persist metrics."""
        metrics = await self.analyze_video(session, response_id, video_path)
        return await self.save_video_feedback(session, response_id, metrics)

    async def analyze_video(
        self,
        session: AsyncSession,
        response_id: UUID,
        video_path: str,
    ) -> VideoMetrics:
        """Run the analyzer on a saved video file."""
        await self._get_response(session, response_id)

        path = Path(video_path)
        if not path.exists():
            raise ValueError(f"Video file not found: {video_path}")

        return await self.analyzer.analyze(str(path))

    async def save_video_feedback(
        self,
        session: AsyncSession,
        response_id: UUID,
        metrics: VideoMetrics,
    ) -> VideoFeedback:
        """Persist video feedback if it doesn't already exist."""
        existing = await session.exec(
            select(VideoFeedback).where(VideoFeedback.response_id == response_id)
        )
        if existing.first():
            raise ValueError(f"VideoFeedback already exists for response {response_id}")

        feedback = VideoFeedback(
            response_id=response_id,
            confidence_score=metrics.confidence_score,
            nervousness_score=metrics.nervousness_score,
            engagement_score=metrics.engagement_score,
            eye_contact_percentage=metrics.eye_contact_percentage,
            looking_away_count=metrics.looking_away_count,
            fidget_count=metrics.fidget_count,
            hand_gesture_frequency=metrics.hand_gesture_frequency,
            processing_duration_ms=metrics.processing_duration_ms,
            frame_count=metrics.frame_count,
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return feedback

    async def _get_response(self, session: AsyncSession, response_id: UUID) -> InterviewResponse:
        result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.id == response_id)
        )
        response = result.first()
        if not response:
            raise ValueError(f"Response {response_id} not found")
        return response
