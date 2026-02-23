"""Basic video analysis utilities for interview responses.

This is a lightweight placeholder that extracts simple motion and framing
signals so we can persist video metrics without relying on heavyweight ML
models. If OpenCV is available, we sample frames to detect faces and motion;
otherwise we fall back to neutral defaults.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class VideoMetrics:
    """Metrics extracted from video analysis."""

    confidence_score: float
    nervousness_score: float
    engagement_score: float
    eye_contact_percentage: float
    looking_away_count: int
    fidget_count: int | None
    hand_gesture_frequency: float | None
    processing_duration_ms: int
    frame_count: int


class VideoAnalyzer:
    """Analyzes interview video for basic engagement and eye-contact signals."""

    def __init__(self, sample_stride: int = 15) -> None:
        """Configure analyzer.

        Args:
            sample_stride: Number of frames to skip between samples to keep
                processing light (e.g., 15 ~ every 0.5s at 30fps)
        """
        self.sample_stride = sample_stride

    async def analyze(self, video_path: str) -> VideoMetrics:
        """Analyze a video file and return lightweight metrics.

        Uses OpenCV if available; otherwise returns neutral defaults so the
        pipeline can continue without blocking on dependencies.
        """
        start_time = time.perf_counter()
        path = Path(video_path)
        if not path.exists():
            raise ValueError(f"Video file not found: {video_path}")

        try:
            import cv2  # type: ignore
        except Exception:  # pragma: no cover - exercised in environments without cv2
            logger.info("OpenCV not installed; returning neutral video metrics")
            return self._neutral_metrics(start_time, frame_count=0)

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            logger.warning("Failed to open video capture for %s", video_path)
            return self._neutral_metrics(start_time, frame_count=0)

        face_detector = self._load_face_detector(cv2)
        frame_index = 0
        sampled_frames = 0
        center_hits = 0
        looking_away = 0
        motion_scores: list[float] = []
        prev_gray = None

        try:
            while True:
                success, frame = capture.read()
                if not success:
                    break
                frame_index += 1
                if frame_index % self.sample_stride != 0:
                    continue

                sampled_frames += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Motion proxy using frame diff
                if prev_gray is not None:
                    diff = cv2.absdiff(gray, prev_gray)
                    motion_scores.append(float(diff.mean()))
                prev_gray = gray

                # Eye contact proxy: detect face and see if its center is near frame center
                if face_detector:
                    faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                    if len(faces) > 0:
                        center_hits += self._count_center_hits(faces, frame.shape)
                        looking_away += max(0, len(faces) - 1)

            capture.release()
        except Exception:
            capture.release()
            logger.exception("Video analysis failed for %s, returning partial metrics", video_path)
            return self._neutral_metrics(start_time, frame_count=frame_index)

        return self._calculate_metrics(
            start_time=start_time,
            frame_count=frame_index,
            sampled_frames=sampled_frames,
            motion_scores=motion_scores,
            center_hits=center_hits,
            looking_away=looking_away,
        )

    @staticmethod
    def _load_face_detector(cv2) -> object | None:
        """Load Haar cascade face detector if available."""
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            return cv2.CascadeClassifier(cascade_path)
        except Exception:
            logger.debug("Face detector unavailable; skipping eye-contact proxy", exc_info=True)
            return None

    def _calculate_metrics(
        self,
        start_time: float,
        frame_count: int,
        sampled_frames: int,
        motion_scores: list[float],
        center_hits: int,
        looking_away: int,
    ) -> VideoMetrics:
        """Convert raw measurements into user-facing metrics."""
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        if sampled_frames == 0:
            return self._neutral_metrics(duration_ms / 1000, frame_count=frame_count)

        avg_motion = sum(motion_scores) / len(motion_scores) if motion_scores else 0.0
        motion_variance = (
            sum((score - avg_motion) ** 2 for score in motion_scores) / len(motion_scores)
            if motion_scores
            else 0.0
        )

        # Normalize motion into 0-1 bands (heuristic)
        motion_score = min(1.0, avg_motion / 25.0)
        jitter_score = min(1.0, motion_variance / 50.0)

        engagement = max(0.0, min(1.0, 0.6 + (motion_score * 0.2) - (jitter_score * 0.1)))
        nervousness = max(0.0, min(1.0, jitter_score))
        confidence = max(0.0, min(1.0, 1.0 - nervousness + (0.1 * engagement)))

        eye_contact_pct = center_hits / sampled_frames if sampled_frames else 0.0

        return VideoMetrics(
            confidence_score=round(confidence, 3),
            nervousness_score=round(nervousness, 3),
            engagement_score=round(engagement, 3),
            eye_contact_percentage=round(eye_contact_pct, 3),
            looking_away_count=looking_away,
            fidget_count=int(jitter_score * 10) if jitter_score > 0 else 0,
            hand_gesture_frequency=round(motion_score, 3),
            processing_duration_ms=duration_ms,
            frame_count=frame_count,
        )

    def _neutral_metrics(self, start_time: float, frame_count: int) -> VideoMetrics:
        """Return neutral defaults when video analysis cannot run."""
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return VideoMetrics(
            confidence_score=0.5,
            nervousness_score=0.5,
            engagement_score=0.5,
            eye_contact_percentage=0.0,
            looking_away_count=0,
            fidget_count=None,
            hand_gesture_frequency=None,
            processing_duration_ms=duration_ms,
            frame_count=frame_count,
        )

    @staticmethod
    def _count_center_hits(faces, frame_shape: tuple[int, ...]) -> int:
        """Count faces that are roughly centered in the frame."""
        if len(frame_shape) < 2:
            return 0
        height, width = frame_shape[:2]
        center_x, center_y = width / 2, height / 2
        hits = 0
        for x, y, w, h in faces:
            face_center_x = x + w / 2
            face_center_y = y + h / 2
            centered_x = abs(face_center_x - center_x) < width * 0.2
            centered_y = abs(face_center_y - center_y) < height * 0.2
            if centered_x and centered_y:
                hits += 1
        return hits
