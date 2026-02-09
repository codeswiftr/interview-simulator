"""Behavioral analytics service for interview analysis.

This service analyzes interview transcripts to extract behavioral metrics:
- Filler word detection and frequency
- Speaking pace (WPM)
- STAR method compliance scoring
- Confidence indicators
"""

import re
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.analytics import AnalyticsSummary, InterviewAnalytics, ProgressDataPoint
from app.models.interview import InterviewResponse, InterviewSession


class BehavioralAnalyticsService:
    """Service for computing and storing behavioral analytics."""

    # Filler words to track (case-insensitive)
    FILLER_WORDS = [
        "um",
        "uh",
        "like",
        "you know",
        "basically",
        "actually",
        "literally",
        "right",
        "so",
    ]

    # STAR method keywords for pattern matching
    STAR_KEYWORDS = {
        "situation": [
            "situation",
            "context",
            "background",
            "when",
            "at the time",
            "previously",
        ],
        "task": [
            "task",
            "challenge",
            "problem",
            "goal",
            "objective",
            "needed to",
            "had to",
        ],
        "action": [
            "action",
            "did",
            "implemented",
            "created",
            "developed",
            "led",
            "coordinated",
            "analyzed",
            "designed",
        ],
        "result": [
            "result",
            "outcome",
            "achieved",
            "success",
            "improved",
            "increased",
            "decreased",
            "saved",
            "delivered",
        ],
    }

    def analyze_transcript(self, transcript: str, duration_seconds: float) -> dict:
        """Extract behavioral metrics from transcript.

        Args:
            transcript: Full interview response transcript
            duration_seconds: Total duration of the response

        Returns:
            Dictionary with filler_word_count, filler_words_per_minute, speaking_pace_wpm,
            pause_count, avg_pause_duration
        """
        if not transcript or duration_seconds <= 0:
            return {
                "filler_word_count": 0,
                "filler_words_per_minute": 0.0,
                "speaking_pace_wpm": 0.0,
                "pause_count": 0,
                "avg_pause_duration": 0.0,
            }

        # Normalize transcript for analysis
        normalized = transcript.lower()

        # Count filler words
        filler_count = 0
        for filler in self.FILLER_WORDS:
            # Use word boundaries to avoid false positives
            pattern = r"\b" + re.escape(filler) + r"\b"
            matches = re.findall(pattern, normalized)
            filler_count += len(matches)

        # Calculate words per minute
        words = transcript.split()
        word_count = len(words)
        duration_minutes = duration_seconds / 60.0
        wpm = word_count / duration_minutes if duration_minutes > 0 else 0.0

        # Calculate filler words per minute
        filler_per_minute = filler_count / duration_minutes if duration_minutes > 0 else 0.0

        # Detect pauses (using common pause indicators in transcripts)
        # Count occurrences of multiple spaces, ellipsis, or [pause] markers
        pause_patterns = [r"\s{3,}", r"\.{2,}", r"\[pause\]"]
        pause_count = 0
        for pattern in pause_patterns:
            pause_count += len(re.findall(pattern, transcript))

        # Estimate average pause duration (simplified heuristic)
        # Assume each detected pause is ~1.5 seconds on average
        avg_pause_duration = 1.5 if pause_count > 0 else 0.0

        return {
            "filler_word_count": filler_count,
            "filler_words_per_minute": round(filler_per_minute, 2),
            "speaking_pace_wpm": round(wpm, 1),
            "pause_count": pause_count,
            "avg_pause_duration": avg_pause_duration,
        }

    def score_star_compliance(self, transcript: str) -> float:
        """Score STAR method compliance using pattern matching.

        Args:
            transcript: Full interview response transcript

        Returns:
            Float score from 0-100 representing STAR adherence
        """
        if not transcript:
            return 0.0

        normalized = transcript.lower()
        component_scores = {}

        # Check for each STAR component
        for component, keywords in self.STAR_KEYWORDS.items():
            matches = 0
            for keyword in keywords:
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, normalized):
                    matches += 1

            # Score each component: 25 points max per component
            # Full points if 2+ keywords found, partial if 1 keyword
            if matches >= 2:
                component_scores[component] = 25.0
            elif matches == 1:
                component_scores[component] = 15.0
            else:
                component_scores[component] = 0.0

        # Total score is sum of all components
        total_score = sum(component_scores.values())

        # Bonus points for structure (all 4 components present)
        if all(score > 0 for score in component_scores.values()):
            total_score = min(100.0, total_score * 1.1)  # 10% bonus, capped at 100

        return round(total_score, 1)

    async def calculate_session_analytics(
        self, session: AsyncSession, session_id: UUID, user_id: UUID
    ) -> InterviewAnalytics:
        """Compute and store analytics for a completed interview session.

        Args:
            session: Database session
            session_id: UUID of the interview session
            user_id: UUID of the user

        Returns:
            Newly created InterviewAnalytics record

        Raises:
            ValueError: If session not found or has no responses
        """
        # Check if analytics already exist
        existing_result = await session.exec(
            select(InterviewAnalytics).where(InterviewAnalytics.session_id == session_id)
        )
        existing = existing_result.first()
        if existing:
            raise ValueError(f"Analytics already exist for session {session_id}")

        # Get all responses for this session
        responses_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.session_id == session_id)
        )
        responses = list(responses_result.all())

        if not responses:
            raise ValueError(f"No responses found for session {session_id}")

        # Aggregate metrics across all responses
        total_filler_words = 0
        total_duration = 0.0
        total_wpm = 0.0
        total_pause_count = 0
        total_pause_duration = 0.0
        star_scores = []

        for response in responses:
            if not response.transcript or not response.duration_seconds:
                continue

            metrics = self.analyze_transcript(
                response.transcript, response.duration_seconds
            )

            total_filler_words += metrics["filler_word_count"]
            total_duration += response.duration_seconds
            total_wpm += metrics["speaking_pace_wpm"]
            total_pause_count += metrics["pause_count"]
            total_pause_duration += metrics["avg_pause_duration"] * metrics["pause_count"]

            star_score = self.score_star_compliance(response.transcript)
            star_scores.append(star_score)

        # Calculate averages
        response_count = len([r for r in responses if r.transcript])
        if response_count == 0:
            raise ValueError(f"No valid transcripts found for session {session_id}")

        avg_wpm = total_wpm / response_count
        avg_star_score = sum(star_scores) / len(star_scores) if star_scores else 0.0
        avg_pause_duration = (
            total_pause_duration / total_pause_count if total_pause_count > 0 else 0.0
        )

        # Calculate filler words per minute
        duration_minutes = total_duration / 60.0
        filler_per_minute = (
            total_filler_words / duration_minutes if duration_minutes > 0 else 0.0
        )

        # Calculate overall confidence score (composite metric)
        # Lower filler words = higher confidence
        # WPM in optimal range (120-150) = higher confidence
        # Higher STAR compliance = higher confidence
        filler_score = max(0, 100 - (filler_per_minute * 20))  # Penalize high filler rate
        wpm_score = self._calculate_wpm_score(avg_wpm)
        confidence_score = (filler_score * 0.4 + wpm_score * 0.3 + avg_star_score * 0.3)

        # Create analytics record
        analytics = InterviewAnalytics(
            user_id=user_id,
            session_id=session_id,
            filler_word_count=total_filler_words,
            filler_words_per_minute=round(filler_per_minute, 2),
            speaking_pace_wpm=round(avg_wpm, 1),
            total_duration_seconds=round(total_duration, 1),
            pause_count=total_pause_count,
            avg_pause_duration=round(avg_pause_duration, 2),
            star_compliance_score=round(avg_star_score, 1),
            overall_confidence_score=round(confidence_score, 1),
        )

        session.add(analytics)
        await session.commit()
        await session.refresh(analytics)

        return analytics

    def _calculate_wpm_score(self, wpm: float) -> float:
        """Calculate confidence score based on speaking pace.

        Optimal range is 120-150 WPM. Score decreases for too fast or too slow.

        Args:
            wpm: Words per minute

        Returns:
            Score from 0-100
        """
        if 120 <= wpm <= 150:
            return 100.0
        elif 100 <= wpm < 120:
            return 80 + ((wpm - 100) / 20) * 20
        elif 150 < wpm <= 180:
            return 100 - ((wpm - 150) / 30) * 20
        elif wpm < 100:
            return max(0, 60 + (wpm / 100) * 20)
        else:  # > 180
            return max(0, 80 - ((wpm - 180) / 40) * 40)

    async def get_session_analytics(
        self, session: AsyncSession, session_id: UUID
    ) -> InterviewAnalytics | None:
        """Get analytics for a specific session.

        Args:
            session: Database session
            session_id: UUID of the interview session

        Returns:
            InterviewAnalytics if exists, None otherwise
        """
        result = await session.exec(
            select(InterviewAnalytics).where(InterviewAnalytics.session_id == session_id)
        )
        return result.first()

    async def get_user_progress(
        self, session: AsyncSession, user_id: UUID
    ) -> list[ProgressDataPoint]:
        """Get user's progress over time (all sessions sorted by date).

        Args:
            session: Database session
            user_id: UUID of the user

        Returns:
            List of ProgressDataPoint objects sorted by created_at
        """
        result = await session.exec(
            select(InterviewAnalytics)
            .where(InterviewAnalytics.user_id == user_id)
            .order_by(InterviewAnalytics.created_at)
        )
        analytics_list = list(result.all())

        return [
            ProgressDataPoint(
                session_id=analytics.session_id,
                created_at=analytics.created_at,
                filler_words_per_minute=analytics.filler_words_per_minute,
                speaking_pace_wpm=analytics.speaking_pace_wpm,
                star_compliance_score=analytics.star_compliance_score,
                overall_confidence_score=analytics.overall_confidence_score,
            )
            for analytics in analytics_list
        ]

    async def get_analytics_summary(
        self, session: AsyncSession, user_id: UUID
    ) -> AnalyticsSummary:
        """Get aggregated summary with averages and trends.

        Args:
            session: Database session
            user_id: UUID of the user

        Returns:
            AnalyticsSummary with aggregated metrics and improvement percentages
        """
        result = await session.exec(
            select(InterviewAnalytics)
            .where(InterviewAnalytics.user_id == user_id)
            .order_by(InterviewAnalytics.created_at)
        )
        analytics_list = list(result.all())

        if not analytics_list:
            return AnalyticsSummary(
                avg_filler_words_per_minute=0.0,
                avg_speaking_pace_wpm=0.0,
                avg_star_compliance_score=0.0,
                avg_confidence_score=0.0,
                total_sessions_analyzed=0,
            )

        # Calculate averages
        total_sessions = len(analytics_list)
        avg_filler = sum(a.filler_words_per_minute for a in analytics_list) / total_sessions
        avg_wpm = sum(a.speaking_pace_wpm for a in analytics_list) / total_sessions
        avg_star = sum(a.star_compliance_score for a in analytics_list) / total_sessions
        avg_confidence = sum(a.overall_confidence_score for a in analytics_list) / total_sessions

        # Calculate improvement trends (compare first half vs second half)
        improvement_filler = None
        improvement_star = None
        improvement_confidence = None

        if total_sessions >= 4:  # Need at least 4 sessions for meaningful trends
            midpoint = total_sessions // 2
            first_half = analytics_list[:midpoint]
            second_half = analytics_list[midpoint:]

            avg_filler_first = (
                sum(a.filler_words_per_minute for a in first_half) / len(first_half)
            )
            avg_filler_second = (
                sum(a.filler_words_per_minute for a in second_half) / len(second_half)
            )
            avg_star_first = (
                sum(a.star_compliance_score for a in first_half) / len(first_half)
            )
            avg_star_second = (
                sum(a.star_compliance_score for a in second_half) / len(second_half)
            )
            avg_confidence_first = (
                sum(a.overall_confidence_score for a in first_half) / len(first_half)
            )
            avg_confidence_second = (
                sum(a.overall_confidence_score for a in second_half) / len(second_half)
            )

            # Improvement percentages (negative filler improvement is good)
            if avg_filler_first > 0:
                improvement_filler = round(
                    ((avg_filler_second - avg_filler_first) / avg_filler_first) * 100, 1
                )
            if avg_star_first > 0:
                improvement_star = round(
                    ((avg_star_second - avg_star_first) / avg_star_first) * 100, 1
                )
            if avg_confidence_first > 0:
                improvement_confidence = round(
                    ((avg_confidence_second - avg_confidence_first) / avg_confidence_first) * 100,
                    1,
                )

        return AnalyticsSummary(
            avg_filler_words_per_minute=round(avg_filler, 2),
            avg_speaking_pace_wpm=round(avg_wpm, 1),
            avg_star_compliance_score=round(avg_star, 1),
            avg_confidence_score=round(avg_confidence, 1),
            total_sessions_analyzed=total_sessions,
            improvement_filler_words=improvement_filler,
            improvement_star_compliance=improvement_star,
            improvement_confidence=improvement_confidence,
        )
