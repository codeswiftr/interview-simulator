"""Unit tests for VideoService."""

import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.ai.video_analyzer import VideoMetrics
from app.models.feedback import VideoFeedback
from app.models.interview import InterviewResponse
from app.services.video_service import VideoService


class TestVideoServiceInit:
    """Tests for VideoService initialization."""

    def test_initialization_creates_analyzer(self):
        """Test that initialization creates a video analyzer."""
        service = VideoService()
        assert service.analyzer is not None


class TestProcessResponseVideo:
    """Tests for process_response_video method."""

    @pytest.mark.asyncio
    async def test_orchestrates_full_processing_flow(self):
        """Test the full processing orchestration."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()
        video_path = "/tmp/test_video.mp4"

        mock_metrics = MagicMock(spec=VideoMetrics)
        mock_feedback = MagicMock(spec=VideoFeedback)

        with patch.object(service, "analyze_video", return_value=mock_metrics) as mock_analyze:
            with patch.object(service, "save_video_feedback", return_value=mock_feedback) as mock_save:
                result = await service.process_response_video(mock_session, response_id, video_path)

                assert result == mock_feedback
                mock_analyze.assert_called_once_with(mock_session, response_id, video_path)
                mock_save.assert_called_once_with(mock_session, response_id, mock_metrics)

    @pytest.mark.asyncio
    async def test_raises_if_analyze_fails(self):
        """Test that analysis failures are propagated."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        with patch.object(service, "analyze_video", side_effect=ValueError("Analysis failed")):
            with pytest.raises(ValueError, match="Analysis failed"):
                await service.process_response_video(mock_session, response_id, "/path/video.mp4")

    @pytest.mark.asyncio
    async def test_raises_if_save_fails(self):
        """Test that save failures are propagated."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()
        mock_metrics = MagicMock(spec=VideoMetrics)

        with patch.object(service, "analyze_video", return_value=mock_metrics):
            with patch.object(service, "save_video_feedback", side_effect=ValueError("Save failed")):
                with pytest.raises(ValueError, match="Save failed"):
                    await service.process_response_video(mock_session, response_id, "/path/video.mp4")


class TestAnalyzeVideo:
    """Tests for analyze_video method."""

    @pytest.mark.asyncio
    async def test_raises_if_response_not_found(self):
        """Test that ValueError is raised if response not found."""
        service = VideoService()
        response_id = uuid4()
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match=f"Response {response_id} not found"):
            await service.analyze_video(mock_session, response_id, "/path/video.mp4")

    @pytest.mark.asyncio
    async def test_raises_if_video_file_not_found(self):
        """Test analyzing a video file that doesn't exist."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Mock _get_response to succeed
        with patch.object(service, "_get_response", return_value=MagicMock()):
            with pytest.raises(ValueError, match="Video file not found"):
                await service.analyze_video(mock_session, response_id, "/non/existent/path.mp4")

    @pytest.mark.asyncio
    async def test_analyzes_video_successfully(self, tmp_path):
        """Test successful video analysis."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Create temp video file
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video data")

        mock_metrics = VideoMetrics(
            confidence_score=0.8,
            nervousness_score=0.2,
            engagement_score=0.9,
            eye_contact_percentage=0.855,
            looking_away_count=2,
            fidget_count=1,
            hand_gesture_frequency=0.5,
            processing_duration_ms=1000,
            frame_count=300
        )

        with patch.object(service, "_get_response", return_value=MagicMock()):
            with patch.object(service.analyzer, "analyze", new_callable=AsyncMock, return_value=mock_metrics):
                result = await service.analyze_video(mock_session, response_id, str(video_file))

                assert result == mock_metrics
                assert result.confidence_score == 0.8
                assert result.frame_count == 300

    @pytest.mark.asyncio
    async def test_handles_analyzer_exception(self, tmp_path, caplog):
        """Test that analyzer exceptions are propagated."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video data")

        with patch.object(service, "_get_response", return_value=MagicMock()):
            with patch.object(
                service.analyzer, "analyze",
                new_callable=AsyncMock,
                side_effect=Exception("Analyzer crashed")
            ):
                with pytest.raises(Exception, match="Analyzer crashed"):
                    await service.analyze_video(mock_session, response_id, str(video_file))

    @pytest.mark.asyncio
    async def test_passes_correct_path_to_analyzer(self, tmp_path):
        """Test that the correct path is passed to the analyzer."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        video_file = tmp_path / "specific_video.mp4"
        video_file.write_bytes(b"fake")

        mock_metrics = VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=0,
            hand_gesture_frequency=0.0,
            processing_duration_ms=500,
            frame_count=100
        )

        with patch.object(service, "_get_response", return_value=MagicMock()):
            with patch.object(service.analyzer, "analyze", new_callable=AsyncMock, return_value=mock_metrics) as mock_analyze:
                await service.analyze_video(mock_session, response_id, str(video_file))

                mock_analyze.assert_called_once_with(str(video_file))


class TestSaveVideoFeedback:
    """Tests for save_video_feedback method."""

    @pytest.mark.asyncio
    async def test_prevents_duplicate_feedback(self):
        """Test error when video feedback already exists."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Mock existing feedback
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(spec=VideoFeedback)
        mock_session.exec.return_value = mock_result

        mock_metrics = VideoMetrics(
            confidence_score=0.8,
            nervousness_score=0.2,
            engagement_score=0.9,
            eye_contact_percentage=0.855,
            looking_away_count=2,
            fidget_count=1,
            hand_gesture_frequency=0.5,
            processing_duration_ms=1000,
            frame_count=300
        )

        with pytest.raises(ValueError, match="VideoFeedback already exists"):
            await service.save_video_feedback(mock_session, response_id, mock_metrics)

    @pytest.mark.asyncio
    async def test_creates_feedback_successfully(self):
        """Test successful video feedback persistence."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_metrics = VideoMetrics(
            confidence_score=0.8,
            nervousness_score=0.2,
            engagement_score=0.9,
            eye_contact_percentage=0.855,
            looking_away_count=2,
            fidget_count=1,
            hand_gesture_frequency=0.5,
            processing_duration_ms=1000,
            frame_count=300
        )

        # Mock no existing feedback
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert isinstance(result, VideoFeedback)
        assert result.response_id == response_id
        assert result.confidence_score == 0.8
        assert result.nervousness_score == 0.2
        assert result.engagement_score == 0.9
        assert result.eye_contact_percentage == 0.855
        assert result.looking_away_count == 2
        assert result.fidget_count == 1
        assert result.hand_gesture_frequency == 0.5
        assert result.processing_duration_ms == 1000
        assert result.frame_count == 300
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called

    @pytest.mark.asyncio
    async def test_handles_none_fidget_count(self):
        """Test handling of None fidget_count in metrics."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_metrics = VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=None,  # None value
            hand_gesture_frequency=None,  # None value
            processing_duration_ms=500,
            frame_count=0
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.fidget_count is None
        assert result.hand_gesture_frequency is None

    @pytest.mark.asyncio
    async def test_handles_zero_values(self):
        """Test handling of zero values in metrics."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_metrics = VideoMetrics(
            confidence_score=0.0,
            nervousness_score=0.0,
            engagement_score=0.0,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=0,
            hand_gesture_frequency=0.0,
            processing_duration_ms=0,
            frame_count=0
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.confidence_score == 0.0
        assert result.engagement_score == 0.0
        assert result.frame_count == 0

    @pytest.mark.asyncio
    async def test_handles_maximum_values(self):
        """Test handling of maximum values in metrics."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_metrics = VideoMetrics(
            confidence_score=1.0,
            nervousness_score=1.0,
            engagement_score=1.0,
            eye_contact_percentage=1.0,
            looking_away_count=999,
            fidget_count=999,
            hand_gesture_frequency=1.0,
            processing_duration_ms=60000,
            frame_count=9999
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.confidence_score == 1.0
        assert result.looking_away_count == 999
        assert result.frame_count == 9999

    @pytest.mark.asyncio
    async def test_handles_commit_failure(self):
        """Test handling of database commit failure."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_metrics = VideoMetrics(
            confidence_score=0.8,
            nervousness_score=0.2,
            engagement_score=0.9,
            eye_contact_percentage=0.855,
            looking_away_count=2,
            fidget_count=1,
            hand_gesture_frequency=0.5,
            processing_duration_ms=1000,
            frame_count=300
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await service.save_video_feedback(mock_session, response_id, mock_metrics)

    @pytest.mark.asyncio
    async def test_handles_refresh_failure(self):
        """Test handling of database refresh failure."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_metrics = VideoMetrics(
            confidence_score=0.8,
            nervousness_score=0.2,
            engagement_score=0.9,
            eye_contact_percentage=0.855,
            looking_away_count=2,
            fidget_count=1,
            hand_gesture_frequency=0.5,
            processing_duration_ms=1000,
            frame_count=300
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        mock_session.refresh.side_effect = Exception("Refresh error")

        with pytest.raises(Exception, match="Refresh error"):
            await service.save_video_feedback(mock_session, response_id, mock_metrics)


class TestGetResponse:
    """Tests for _get_response method."""

    @pytest.mark.asyncio
    async def test_retrieves_existing_response(self):
        """Test successful retrieval of existing response."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id

        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_session.exec.return_value = mock_result

        result = await service._get_response(mock_session, response_id)

        assert result == mock_response
        assert result.id == response_id

    @pytest.mark.asyncio
    async def test_raises_if_response_not_found(self):
        """Test retrieving a non-existent response."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match=f"Response {response_id} not found"):
            await service._get_response(mock_session, response_id)

    @pytest.mark.asyncio
    async def test_handles_database_exception(self):
        """Test handling of database exceptions during query."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        mock_session.exec.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await service._get_response(mock_session, response_id)


class TestVideoMetricsHandling:
    """Tests for handling VideoMetrics data structures."""

    @pytest.mark.asyncio
    async def test_handles_neutral_metrics(self):
        """Test handling of neutral/default metrics."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Neutral metrics (as returned when OpenCV unavailable)
        mock_metrics = VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=None,
            hand_gesture_frequency=None,
            processing_duration_ms=100,
            frame_count=0
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.confidence_score == 0.5
        assert result.engagement_score == 0.5
        assert result.frame_count == 0

    @pytest.mark.asyncio
    async def test_handles_high_quality_metrics(self):
        """Test handling of high-quality video metrics."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # High quality metrics (good eye contact, low nervousness)
        mock_metrics = VideoMetrics(
            confidence_score=0.95,
            nervousness_score=0.1,
            engagement_score=0.98,
            eye_contact_percentage=0.92,
            looking_away_count=1,
            fidget_count=0,
            hand_gesture_frequency=0.8,
            processing_duration_ms=2000,
            frame_count=900
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.confidence_score == 0.95
        assert result.nervousness_score == 0.1
        assert result.engagement_score == 0.98
        assert result.eye_contact_percentage == 0.92

    @pytest.mark.asyncio
    async def test_handles_poor_quality_metrics(self):
        """Test handling of poor-quality video metrics."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Poor quality metrics (low eye contact, high nervousness)
        mock_metrics = VideoMetrics(
            confidence_score=0.3,
            nervousness_score=0.9,
            engagement_score=0.2,
            eye_contact_percentage=0.1,
            looking_away_count=50,
            fidget_count=25,
            hand_gesture_frequency=0.05,
            processing_duration_ms=3000,
            frame_count=600
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.confidence_score == 0.3
        assert result.nervousness_score == 0.9
        assert result.looking_away_count == 50
        assert result.fidget_count == 25


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_handles_different_video_extensions(self, tmp_path):
        """Test handling of different video file extensions."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        for ext in [".mp4", ".webm", ".avi", ".mov"]:
            video_file = tmp_path / f"test{ext}"
            video_file.write_bytes(b"fake video")

            mock_metrics = VideoMetrics(
                confidence_score=0.5,
                nervousness_score=0.5,
                engagement_score=0.5,
                eye_contact_percentage=0.0,
                looking_away_count=0,
                fidget_count=0,
                hand_gesture_frequency=0.0,
                processing_duration_ms=100,
                frame_count=100
            )

            with patch.object(service, "_get_response", return_value=MagicMock()):
                with patch.object(service.analyzer, "analyze", new_callable=AsyncMock, return_value=mock_metrics):
                    result = await service.analyze_video(mock_session, response_id, str(video_file))
                    assert result is not None

    @pytest.mark.asyncio
    async def test_handles_very_long_video_path(self, tmp_path):
        """Test handling of very long file paths."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Create nested directory structure
        long_path = tmp_path / "very" / "long" / "nested" / "directory" / "structure" / "test.mp4"
        long_path.parent.mkdir(parents=True, exist_ok=True)
        long_path.write_bytes(b"fake video")

        mock_metrics = VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=0,
            hand_gesture_frequency=0.0,
            processing_duration_ms=100,
            frame_count=100
        )

        with patch.object(service, "_get_response", return_value=MagicMock()):
            with patch.object(service.analyzer, "analyze", new_callable=AsyncMock, return_value=mock_metrics):
                result = await service.analyze_video(mock_session, response_id, str(long_path))
                assert result is not None

    @pytest.mark.asyncio
    async def test_handles_unicode_in_path(self, tmp_path):
        """Test handling of Unicode characters in file path."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        video_file = tmp_path / "test_видео_测试.mp4"
        video_file.write_bytes(b"fake video")

        mock_metrics = VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=0,
            hand_gesture_frequency=0.0,
            processing_duration_ms=100,
            frame_count=100
        )

        with patch.object(service, "_get_response", return_value=MagicMock()):
            with patch.object(service.analyzer, "analyze", new_callable=AsyncMock, return_value=mock_metrics):
                result = await service.analyze_video(mock_session, response_id, str(video_file))
                assert result is not None

    @pytest.mark.asyncio
    async def test_handles_very_short_video(self):
        """Test handling of very short video (few frames)."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Metrics for a very short video
        mock_metrics = VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=0,
            hand_gesture_frequency=0.0,
            processing_duration_ms=50,
            frame_count=5  # Very few frames
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.frame_count == 5
        assert result.processing_duration_ms == 50

    @pytest.mark.asyncio
    async def test_handles_very_long_processing_time(self):
        """Test handling of very long processing duration."""
        service = VideoService()
        mock_session = AsyncMock()
        response_id = uuid4()

        # Metrics for a video that took a long time to process
        mock_metrics = VideoMetrics(
            confidence_score=0.8,
            nervousness_score=0.2,
            engagement_score=0.9,
            eye_contact_percentage=0.85,
            looking_away_count=2,
            fidget_count=1,
            hand_gesture_frequency=0.5,
            processing_duration_ms=300000,  # 5 minutes
            frame_count=9000
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await service.save_video_feedback(mock_session, response_id, mock_metrics)

        assert result.processing_duration_ms == 300000
        assert result.frame_count == 9000
