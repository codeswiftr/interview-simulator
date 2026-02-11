"""Unit tests for video analyzer service (no OpenCV required)."""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.ai.video_analyzer import VideoAnalyzer, VideoMetrics


class TestVideoAnalyzerInit:
    """Tests for VideoAnalyzer initialization."""

    def test_default_sample_stride(self):
        """Test default sample stride is 15."""
        analyzer = VideoAnalyzer()
        assert analyzer.sample_stride == 15

    def test_custom_sample_stride(self):
        """Test custom sample stride can be set."""
        analyzer = VideoAnalyzer(sample_stride=30)
        assert analyzer.sample_stride == 30


class TestVideoMetrics:
    """Tests for VideoMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating VideoMetrics instance."""
        metrics = VideoMetrics(
            confidence_score=0.8,
            nervousness_score=0.2,
            engagement_score=0.75,
            eye_contact_percentage=0.65,
            looking_away_count=3,
            fidget_count=5,
            hand_gesture_frequency=0.4,
            processing_duration_ms=150,
            frame_count=450,
        )

        assert metrics.confidence_score == 0.8
        assert metrics.nervousness_score == 0.2
        assert metrics.engagement_score == 0.75
        assert metrics.eye_contact_percentage == 0.65
        assert metrics.looking_away_count == 3
        assert metrics.fidget_count == 5
        assert metrics.hand_gesture_frequency == 0.4
        assert metrics.processing_duration_ms == 150
        assert metrics.frame_count == 450

    def test_metrics_with_none_values(self):
        """Test VideoMetrics with None values for optional fields."""
        metrics = VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=None,
            hand_gesture_frequency=None,
            processing_duration_ms=100,
            frame_count=0,
        )

        assert metrics.fidget_count is None
        assert metrics.hand_gesture_frequency is None


class TestVideoAnalyzerAnalyze:
    """Tests for the analyze method."""

    @pytest.mark.asyncio
    async def test_analyze_missing_file(self):
        """Test that analyze raises ValueError for missing file."""
        analyzer = VideoAnalyzer()

        with pytest.raises(ValueError, match="Video file not found"):
            await analyzer.analyze("/nonexistent/path/video.mp4")

    @pytest.mark.asyncio
    async def test_analyze_without_opencv(self):
        """Test that analyze returns neutral metrics when OpenCV unavailable."""
        analyzer = VideoAnalyzer()

        # Create temp file to pass existence check
        with patch("pathlib.Path.exists", return_value=True):
            # Make cv2 import fail
            with patch.dict("sys.modules", {"cv2": None}):
                import builtins
                original_import = builtins.__import__

                def mock_import(name, *args, **kwargs):
                    if name == "cv2":
                        raise ImportError("No module named 'cv2'")
                    return original_import(name, *args, **kwargs)

                with patch.object(builtins, "__import__", mock_import):
                    metrics = await analyzer.analyze("/tmp/test.mp4")

        # Should return neutral defaults
        assert metrics.confidence_score == 0.5
        assert metrics.nervousness_score == 0.5
        assert metrics.engagement_score == 0.5
        assert metrics.eye_contact_percentage == 0.0
        assert metrics.fidget_count is None

    @pytest.mark.asyncio
    async def test_analyze_video_capture_fails(self):
        """Test handling when video capture cannot be opened."""
        analyzer = VideoAnalyzer()

        mock_cv2 = MagicMock()
        mock_capture = MagicMock()
        mock_capture.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_capture

        with patch("pathlib.Path.exists", return_value=True):
            with patch.dict("sys.modules", {"cv2": mock_cv2}):
                metrics = await analyzer.analyze("/tmp/test.mp4")
                # Should return neutral metrics when capture fails
                assert metrics.confidence_score == 0.5

    @pytest.mark.asyncio
    async def test_analyze_exception_during_loop(self):
        """Test handling exception during frame processing loop."""
        analyzer = VideoAnalyzer()

        mock_cv2 = MagicMock()
        mock_capture = MagicMock()
        mock_capture.isOpened.return_value = True
        mock_capture.read.side_effect = Exception("Hardware failure")
        mock_cv2.VideoCapture.return_value = mock_capture

        with patch("pathlib.Path.exists", return_value=True):
            with patch.dict("sys.modules", {"cv2": mock_cv2}):
                metrics = await analyzer.analyze("/tmp/test.mp4")
                # Should return neutral metrics due to exception
                assert metrics.confidence_score == 0.5
                mock_capture.release.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_partial_success(self):
        """Test handling when some frames are processed before failure."""
        analyzer = VideoAnalyzer()

        mock_cv2 = MagicMock()
        mock_capture = MagicMock()
        mock_capture.isOpened.return_value = True
        # Return one frame then fail
        mock_capture.read.side_effect = [
            (True, MagicMock()),
            Exception("Hardware failure")
        ]
        mock_cv2.VideoCapture.return_value = mock_capture

        with patch("pathlib.Path.exists", return_value=True):
            with patch.dict("sys.modules", {"cv2": mock_cv2}):
                metrics = await analyzer.analyze("/tmp/test.mp4")
                assert metrics.frame_count == 1
                mock_capture.release.assert_called_once()


class TestNeutralMetrics:
    """Tests for _neutral_metrics method."""

    def test_neutral_metrics_returns_defaults(self):
        """Test neutral metrics returns expected defaults."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        metrics = analyzer._neutral_metrics(start_time, frame_count=100)

        assert metrics.confidence_score == 0.5
        assert metrics.nervousness_score == 0.5
        assert metrics.engagement_score == 0.5
        assert metrics.eye_contact_percentage == 0.0
        assert metrics.looking_away_count == 0
        assert metrics.fidget_count is None
        assert metrics.hand_gesture_frequency is None
        assert metrics.frame_count == 100
        assert metrics.processing_duration_ms >= 0

    def test_neutral_metrics_with_zero_frames(self):
        """Test neutral metrics with zero frames."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        metrics = analyzer._neutral_metrics(start_time, frame_count=0)

        assert metrics.frame_count == 0


class TestCalculateMetrics:
    """Tests for _calculate_metrics method."""

    def test_calculate_metrics_zero_sampled_frames(self):
        """Test _calculate_metrics returns neutral when no frames sampled."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        metrics = analyzer._calculate_metrics(
            start_time=start_time,
            frame_count=100,
            sampled_frames=0,
            motion_scores=[],
            center_hits=0,
            looking_away=0,
        )

        # Should return neutral metrics
        assert metrics.confidence_score == 0.5
        assert metrics.nervousness_score == 0.5

    def test_calculate_metrics_with_motion(self):
        """Test _calculate_metrics with motion data."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        metrics = analyzer._calculate_metrics(
            start_time=start_time,
            frame_count=450,
            sampled_frames=30,
            motion_scores=[10.0, 12.0, 8.0, 15.0, 11.0],
            center_hits=20,
            looking_away=5,
        )

        assert 0.0 <= metrics.confidence_score <= 1.0
        assert 0.0 <= metrics.nervousness_score <= 1.0
        assert 0.0 <= metrics.engagement_score <= 1.0
        assert metrics.eye_contact_percentage > 0
        assert metrics.looking_away_count == 5
        assert metrics.frame_count == 450

    def test_calculate_metrics_high_motion(self):
        """Test _calculate_metrics with high motion (nervousness)."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        # High variance in motion scores indicates jittery movement
        metrics = analyzer._calculate_metrics(
            start_time=start_time,
            frame_count=300,
            sampled_frames=20,
            motion_scores=[5.0, 50.0, 3.0, 45.0, 2.0, 48.0],
            center_hits=10,
            looking_away=2,
        )

        # High variance should result in higher nervousness score
        assert metrics.nervousness_score > 0.1

    def test_calculate_metrics_low_motion(self):
        """Test _calculate_metrics with low consistent motion."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        # Low consistent motion scores
        metrics = analyzer._calculate_metrics(
            start_time=start_time,
            frame_count=300,
            sampled_frames=20,
            motion_scores=[5.0, 5.2, 4.8, 5.1, 5.0, 5.3],
            center_hits=18,
            looking_away=0,
        )

        # Low variance should result in lower nervousness
        assert metrics.nervousness_score < 0.5
        # High center hits should result in good eye contact
        assert metrics.eye_contact_percentage > 0.5

    def test_calculate_metrics_empty_motion_scores(self):
        """Test _calculate_metrics with no motion scores but sampled frames."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        metrics = analyzer._calculate_metrics(
            start_time=start_time,
            frame_count=100,
            sampled_frames=5,
            motion_scores=[],
            center_hits=3,
            looking_away=0,
        )

        # Should handle empty motion scores gracefully
        assert metrics.engagement_score >= 0.5

    def test_calculate_metrics_zero_sampled_frames_path(self):
        """Test _calculate_metrics calls _neutral_metrics when sampled_frames is 0."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        metrics = analyzer._calculate_metrics(
            start_time=start_time,
            frame_count=100,
            sampled_frames=0,
            motion_scores=[1.0],
            center_hits=0,
            looking_away=0,
        )

        assert metrics.confidence_score == 0.5
        assert metrics.fidget_count is None

    def test_calculate_metrics_extreme_values(self):
        """Test metrics with extremely high motion."""
        analyzer = VideoAnalyzer()
        start_time = time.perf_counter()

        metrics = analyzer._calculate_metrics(
            start_time=start_time,
            frame_count=100,
            sampled_frames=10,
            motion_scores=[1000.0] * 10,
            center_hits=0,
            looking_away=10,
        )

        assert metrics.confidence_score >= 0.0
        assert metrics.nervousness_score == 1.0  # Capped at 1.0
        assert metrics.hand_gesture_frequency == 1.0 # Capped at 1.0


class TestCountCenterHits:
    """Tests for _count_center_hits static method."""

    def test_count_center_hits_centered_face(self):
        """Test counting a centered face."""
        # Face at center of 1920x1080 frame
        faces = [(860, 440, 200, 200)]  # x, y, w, h
        frame_shape = (1080, 1920, 3)

        hits = VideoAnalyzer._count_center_hits(faces, frame_shape)

        assert hits == 1

    def test_count_center_hits_off_center_face(self):
        """Test counting an off-center face."""
        # Face at far left of frame
        faces = [(50, 440, 200, 200)]
        frame_shape = (1080, 1920, 3)

        hits = VideoAnalyzer._count_center_hits(faces, frame_shape)

        assert hits == 0

    def test_count_center_hits_multiple_faces(self):
        """Test counting multiple faces."""
        # One centered, one off-center
        faces = [
            (860, 440, 200, 200),  # Centered
            (50, 100, 100, 100),   # Off-center
            (900, 400, 150, 150),  # Also centered
        ]
        frame_shape = (1080, 1920, 3)

        hits = VideoAnalyzer._count_center_hits(faces, frame_shape)

        assert hits == 2

    def test_count_center_hits_no_faces(self):
        """Test with no faces detected."""
        faces = []
        frame_shape = (1080, 1920, 3)

        hits = VideoAnalyzer._count_center_hits(faces, frame_shape)

        assert hits == 0

    def test_count_center_hits_invalid_frame_shape(self):
        """Test with invalid frame shape."""
        faces = [(100, 100, 50, 50)]
        frame_shape = (1,)  # Invalid - less than 2 dimensions

        hits = VideoAnalyzer._count_center_hits(faces, frame_shape)

        assert hits == 0


class TestLoadFaceDetector:
    """Tests for _load_face_detector static method."""

    def test_load_face_detector_success(self):
        """Test successful face detector loading."""
        mock_cv2 = MagicMock()
        mock_cv2.data.haarcascades = "/path/to/cascades/"
        mock_detector = MagicMock()
        mock_cv2.CascadeClassifier.return_value = mock_detector

        result = VideoAnalyzer._load_face_detector(mock_cv2)

        assert result == mock_detector
        mock_cv2.CascadeClassifier.assert_called_once()

    def test_load_face_detector_failure(self):
        """Test face detector loading failure returns None."""
        mock_cv2 = MagicMock()
        mock_cv2.data.haarcascades = "/path/to/cascades/"
        mock_cv2.CascadeClassifier.side_effect = Exception("Cascade not found")

        result = VideoAnalyzer._load_face_detector(mock_cv2)

        assert result is None
