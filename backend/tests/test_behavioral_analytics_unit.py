"""Pure unit tests for BehavioralAnalyticsService.

Tests transcript analysis, STAR scoring, WPM scoring, and async DB methods.
No database required.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.behavioral_analytics_service import BehavioralAnalyticsService


@pytest.fixture
def service():
    return BehavioralAnalyticsService()


class TestAnalyzeTranscript:
    def test_empty_transcript(self, service):
        result = service.analyze_transcript("", 60)
        assert result["filler_word_count"] == 0
        assert result["speaking_pace_wpm"] == 0.0

    def test_none_transcript(self, service):
        result = service.analyze_transcript(None, 60)
        assert result["filler_word_count"] == 0

    def test_zero_duration(self, service):
        result = service.analyze_transcript("hello world", 0)
        assert result["filler_word_count"] == 0

    def test_negative_duration(self, service):
        result = service.analyze_transcript("hello", -1)
        assert result["speaking_pace_wpm"] == 0.0

    def test_filler_word_count(self, service):
        transcript = "Um I think that like basically we um did it"
        result = service.analyze_transcript(transcript, 60)
        assert result["filler_word_count"] >= 3  # um(x2), like, basically

    def test_speaking_pace_wpm(self, service):
        words = " ".join(["word"] * 120)
        result = service.analyze_transcript(words, 60)
        assert result["speaking_pace_wpm"] == 120.0

    def test_filler_words_per_minute(self, service):
        transcript = "um uh like basically actually"
        result = service.analyze_transcript(transcript, 60)
        assert result["filler_words_per_minute"] == 5.0

    def test_pause_detection_ellipsis(self, service):
        transcript = "I thought about it.. and then.. decided"
        result = service.analyze_transcript(transcript, 60)
        assert result["pause_count"] >= 2

    def test_pause_detection_marker(self, service):
        transcript = "I [pause] thought about it [pause] carefully"
        result = service.analyze_transcript(transcript, 60)
        assert result["pause_count"] >= 2

    def test_avg_pause_duration_with_pauses(self, service):
        transcript = "I [pause] thought about it"
        result = service.analyze_transcript(transcript, 60)
        assert result["avg_pause_duration"] == 1.5

    def test_avg_pause_duration_no_pauses(self, service):
        transcript = "I thought about it carefully"
        result = service.analyze_transcript(transcript, 60)
        assert result["avg_pause_duration"] == 0.0


class TestScoreStarCompliance:
    def test_empty_transcript(self, service):
        assert service.score_star_compliance("") == 0.0

    def test_none_transcript(self, service):
        assert service.score_star_compliance(None) == 0.0

    def test_full_star_response(self, service):
        transcript = (
            "The situation was that our context required a new approach. "
            "The task was a challenge we had to solve. "
            "I implemented an action and created a solution. "
            "The result was that we achieved success and improved metrics."
        )
        score = service.score_star_compliance(transcript)
        assert score >= 80.0

    def test_partial_star_single_component(self, service):
        transcript = "The situation was very complex and the context was unclear"
        score = service.score_star_compliance(transcript)
        assert 0 < score < 50

    def test_no_star_keywords(self, service):
        transcript = "I went to the store and bought some groceries"
        score = service.score_star_compliance(transcript)
        assert score == 0.0

    def test_all_components_bonus(self, service):
        transcript = (
            "The situation was clear. The task and challenge were defined. "
            "I implemented and created the solution. The result achieved success."
        )
        score = service.score_star_compliance(transcript)
        # Should get bonus for all 4 components present
        assert score > 60


class TestCalculateWpmScore:
    def test_optimal_range(self, service):
        assert service._calculate_wpm_score(135) == 100.0
        assert service._calculate_wpm_score(120) == 100.0
        assert service._calculate_wpm_score(150) == 100.0

    def test_slightly_slow(self, service):
        score = service._calculate_wpm_score(110)
        assert 80 < score < 100

    def test_slightly_fast(self, service):
        score = service._calculate_wpm_score(165)
        assert 80 < score < 100

    def test_very_slow(self, service):
        score = service._calculate_wpm_score(50)
        assert 0 <= score < 80

    def test_very_fast(self, service):
        score = service._calculate_wpm_score(220)
        assert 0 <= score < 80

    def test_zero_wpm(self, service):
        score = service._calculate_wpm_score(0)
        assert score >= 0


class TestCalculateSessionAnalytics:
    @pytest.mark.asyncio
    async def test_raises_if_analytics_exist(self, service):
        session = AsyncMock()
        existing = MagicMock()
        result = MagicMock()
        result.first.return_value = existing
        session.exec.return_value = result

        with pytest.raises(ValueError, match="already exist"):
            await service.calculate_session_analytics(session, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_raises_if_no_responses(self, service):
        session = AsyncMock()
        existing_result = MagicMock()
        existing_result.first.return_value = None
        responses_result = MagicMock()
        responses_result.all.return_value = []

        session.exec.side_effect = [existing_result, responses_result]

        with pytest.raises(ValueError, match="No responses"):
            await service.calculate_session_analytics(session, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_raises_if_no_valid_transcripts(self, service):
        session = AsyncMock()
        existing_result = MagicMock()
        existing_result.first.return_value = None

        response = MagicMock()
        response.transcript = None
        response.duration_seconds = 60

        responses_result = MagicMock()
        responses_result.all.return_value = [response]

        session.exec.side_effect = [existing_result, responses_result]

        with pytest.raises(ValueError, match="No valid transcripts"):
            await service.calculate_session_analytics(session, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_computes_analytics(self, service):
        session = AsyncMock()
        existing_result = MagicMock()
        existing_result.first.return_value = None

        response = MagicMock()
        response.transcript = "The situation was that we needed to solve a task. I implemented the action and achieved a great result."
        response.duration_seconds = 60.0

        responses_result = MagicMock()
        responses_result.all.return_value = [response]

        session.exec.side_effect = [existing_result, responses_result]

        await service.calculate_session_analytics(session, uuid4(), uuid4())
        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()


class TestGetSessionAnalytics:
    @pytest.mark.asyncio
    async def test_returns_analytics(self, service):
        session = AsyncMock()
        analytics = MagicMock()
        result = MagicMock()
        result.first.return_value = analytics
        session.exec.return_value = result

        got = await service.get_session_analytics(session, uuid4())
        assert got is analytics

    @pytest.mark.asyncio
    async def test_returns_none(self, service):
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec.return_value = result

        got = await service.get_session_analytics(session, uuid4())
        assert got is None


class TestGetUserProgress:
    @pytest.mark.asyncio
    async def test_returns_data_points(self, service):
        session = AsyncMock()
        a = MagicMock()
        a.session_id = uuid4()
        a.created_at = MagicMock()
        a.filler_words_per_minute = 2.0
        a.speaking_pace_wpm = 130.0
        a.star_compliance_score = 80.0
        a.overall_confidence_score = 75.0

        result = MagicMock()
        result.all.return_value = [a]
        session.exec.return_value = result

        points = await service.get_user_progress(session, uuid4())
        assert len(points) == 1

    @pytest.mark.asyncio
    async def test_returns_empty(self, service):
        session = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        session.exec.return_value = result

        points = await service.get_user_progress(session, uuid4())
        assert points == []


class TestGetAnalyticsSummary:
    @pytest.mark.asyncio
    async def test_empty_returns_zeroes(self, service):
        session = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        session.exec.return_value = result

        summary = await service.get_analytics_summary(session, uuid4())
        assert summary.total_sessions_analyzed == 0
        assert summary.avg_filler_words_per_minute == 0.0

    @pytest.mark.asyncio
    async def test_computes_averages(self, service):
        session = AsyncMock()
        a1 = MagicMock()
        a1.filler_words_per_minute = 2.0
        a1.speaking_pace_wpm = 130.0
        a1.star_compliance_score = 80.0
        a1.overall_confidence_score = 70.0

        a2 = MagicMock()
        a2.filler_words_per_minute = 4.0
        a2.speaking_pace_wpm = 140.0
        a2.star_compliance_score = 60.0
        a2.overall_confidence_score = 80.0

        result = MagicMock()
        result.all.return_value = [a1, a2]
        session.exec.return_value = result

        summary = await service.get_analytics_summary(session, uuid4())
        assert summary.total_sessions_analyzed == 2
        assert summary.avg_filler_words_per_minute == 3.0
        assert summary.avg_speaking_pace_wpm == 135.0

    @pytest.mark.asyncio
    async def test_trends_with_4_sessions(self, service):
        session = AsyncMock()
        analytics_list = []
        for i in range(4):
            a = MagicMock()
            a.filler_words_per_minute = 5.0 - i
            a.speaking_pace_wpm = 130.0
            a.star_compliance_score = 50.0 + i * 10
            a.overall_confidence_score = 60.0 + i * 5
            analytics_list.append(a)

        result = MagicMock()
        result.all.return_value = analytics_list
        session.exec.return_value = result

        summary = await service.get_analytics_summary(session, uuid4())
        assert summary.total_sessions_analyzed == 4
        assert summary.improvement_filler_words is not None
        assert summary.improvement_star_compliance is not None
        assert summary.improvement_confidence is not None
