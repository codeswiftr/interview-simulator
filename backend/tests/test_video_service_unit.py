"""Pure unit tests for VideoService without database.

Tests video analysis service with mocked database and analyzer.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.ai.video_analyzer import VideoMetrics
from app.models.feedback import VideoFeedback
from app.models.interview import InterviewResponse
from app.services.video_service import VideoService


@pytest.fixture
def video_service():
    """Provide VideoService instance with mocked analyzer."""
    with patch("app.services.video_service.VideoAnalyzer") as MockAnalyzer:
        mock_analyzer = MagicMock()
        MockAnalyzer.return_value = mock_analyzer
        service = VideoService()
        service.analyzer = mock_analyzer
        yield service


@pytest.fixture
def sample_video_metrics():
    """Sample video metrics for testing."""
    return VideoMetrics(
        confidence_score=75.0,
        nervousness_score=25.0,
        engagement_score=80.0,
        eye_contact_percentage=70.0,
        looking_away_count=5,
        fidget_count=3,
        hand_gesture_frequency=0.8,
        processing_duration_ms=1500,
        frame_count=450,
    )


class TestVideoServiceInit:
    """Tests for VideoService initialization."""

    def test_creates_video_analyzer(self):
        """Test service creates VideoAnalyzer on init."""
        with patch("app.services.video_service.VideoAnalyzer") as MockAnalyzer:
            service = VideoService()
            MockAnalyzer.assert_called_once()
            assert service.analyzer is not None


class TestAnalyzeVideo:
    """Tests for analyze_video method."""

    @pytest.mark.asyncio
    async def test_raises_error_when_response_not_found(self, video_service):
        """Test raises ValueError when response doesn't exist."""
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc_info:
            await video_service.analyze_video(mock_session, response_id, "/path/to/video.mp4")

        assert str(response_id) in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_error_when_video_file_not_found(self, video_service):
        """Test raises ValueError when video file doesn't exist."""
        mock_session = AsyncMock()
        response_id = uuid4()

        # Mock response exists
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_session.exec = AsyncMock(return_value=mock_result)

        # Non-existent path
        fake_path = f"/nonexistent/path/video_{uuid4().hex}.mp4"

        with pytest.raises(ValueError) as exc_info:
            await video_service.analyze_video(mock_session, response_id, fake_path)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calls_analyzer_with_video_path(self, video_service, sample_video_metrics, tmp_path):
        """Test calls analyzer with correct video path."""
        mock_session = AsyncMock()
        response_id = uuid4()

        # Create temp video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"fake video content")

        # Mock response exists
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_session.exec = AsyncMock(return_value=mock_result)

        # Mock analyzer
        video_service.analyzer.analyze = AsyncMock(return_value=sample_video_metrics)

        result = await video_service.analyze_video(mock_session, response_id, str(video_file))

        assert result == sample_video_metrics
        video_service.analyzer.analyze.assert_called_once()


class TestSaveVideoFeedback:
    """Tests for save_video_feedback method."""

    @pytest.mark.asyncio
    async def test_raises_error_when_feedback_exists(self, video_service, sample_video_metrics):
        """Test raises ValueError when feedback already exists."""
        mock_session = AsyncMock()
        response_id = uuid4()

        # Mock existing feedback
        existing_feedback = MagicMock(spec=VideoFeedback)
        mock_result = MagicMock()
        mock_result.first.return_value = existing_feedback
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc_info:
            await video_service.save_video_feedback(mock_session, response_id, sample_video_metrics)

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_creates_and_saves_feedback(self, video_service, sample_video_metrics):
        """Test creates and commits VideoFeedback."""
        mock_session = AsyncMock()
        response_id = uuid4()

        # No existing feedback
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await video_service.save_video_feedback(mock_session, response_id, sample_video_metrics)

        assert result is not None
        assert result.confidence_score == sample_video_metrics.confidence_score
        assert result.engagement_score == sample_video_metrics.engagement_score
        assert result.eye_contact_percentage == sample_video_metrics.eye_contact_percentage
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()


class TestProcessResponseVideo:
    """Tests for process_response_video method."""

    @pytest.mark.asyncio
    async def test_orchestrates_analyze_and_save(self, video_service, sample_video_metrics, tmp_path):
        """Test orchestrates analyze_video and save_video_feedback."""
        mock_session = AsyncMock()
        response_id = uuid4()

        # Create temp video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"fake video content")

        # Mock response exists (for analyze_video)
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id

        # Setup mocks for both calls
        call_count = [0]

        def mock_exec(query):
            result = MagicMock()
            if call_count[0] == 0:
                # analyze_video: response exists
                result.first.return_value = mock_response
            else:
                # save_video_feedback: no existing feedback
                result.first.return_value = None
            call_count[0] += 1
            return result

        mock_session.exec = AsyncMock(side_effect=mock_exec)

        # Mock analyzer
        video_service.analyzer.analyze = AsyncMock(return_value=sample_video_metrics)

        result = await video_service.process_response_video(
            mock_session, response_id, str(video_file)
        )

        assert result is not None
        assert result.confidence_score == sample_video_metrics.confidence_score


class TestGetResponse:
    """Tests for _get_response helper method."""

    @pytest.mark.asyncio
    async def test_returns_response_when_found(self, video_service):
        """Test returns response when it exists."""
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await video_service._get_response(mock_session, response_id)

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_raises_error_when_not_found(self, video_service):
        """Test raises ValueError when response not found."""
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc_info:
            await video_service._get_response(mock_session, response_id)

        assert "not found" in str(exc_info.value)
