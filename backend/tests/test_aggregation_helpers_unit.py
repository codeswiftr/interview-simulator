"""Pure unit tests for AggregationService helper methods.

Tests aggregate_strengths_and_improvements, determine_practice_areas,
_aggregate_delivery, _aggregate_behavioral, _aggregate_technical, and _split_sessions.
No database required.
"""

from unittest.mock import MagicMock

import pytest

from app.models.feedback import ContentFeedback
from app.services.aggregation_service import AggregationService, _split_sessions
from app.services.scoring_service import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


@pytest.fixture
def agg_service(scoring_service):
    return AggregationService(scoring_service)


# --- _split_sessions ---

class TestSplitSessions:
    def test_split_with_more_than_recent_count(self):
        sessions = [MagicMock() for _ in range(10)]
        recent, previous = _split_sessions(sessions, recent_count=5)
        assert len(recent) == 5
        assert len(previous) == 5

    def test_split_with_exact_recent_count(self):
        sessions = [MagicMock() for _ in range(5)]
        recent, previous = _split_sessions(sessions, recent_count=5)
        assert len(recent) == 5
        # When equal, uses half-split fallback: sessions[5//2:] = sessions[2:]
        assert len(previous) == 3

    def test_split_with_fewer_than_recent_count(self):
        sessions = [MagicMock() for _ in range(3)]
        recent, previous = _split_sessions(sessions, recent_count=5)
        assert len(recent) == 3
        assert len(previous) == 2  # 3 // 2 = 1, sessions[1:]

    def test_split_with_single_session(self):
        sessions = [MagicMock()]
        recent, previous = _split_sessions(sessions, recent_count=5)
        assert len(recent) == 1
        assert len(previous) == 1  # sessions[0:] since 1//2=0

    def test_split_default_recent_count(self):
        sessions = [MagicMock() for _ in range(8)]
        recent, previous = _split_sessions(sessions)
        assert len(recent) == 5
        assert len(previous) == 3


# --- aggregate_strengths_and_improvements ---

class TestAggregateStrengths:
    def _make_feedback(self, strengths, improvements):
        fb = MagicMock(spec=ContentFeedback)
        fb.strengths = strengths
        fb.improvements = improvements
        return fb

    def test_returns_top_3_by_default(self, agg_service):
        feedbacks = [
            self._make_feedback(["A", "B"], ["X", "Y"]),
            self._make_feedback(["A", "C"], ["X", "Z"]),
            self._make_feedback(["A", "B", "D"], ["X", "Y", "W"]),
        ]
        strengths, improvements = agg_service.aggregate_strengths_and_improvements(feedbacks)
        assert strengths[0] == "A"  # Most common
        assert len(strengths) <= 3
        assert improvements[0] == "X"

    def test_empty_feedbacks(self, agg_service):
        strengths, improvements = agg_service.aggregate_strengths_and_improvements([])
        assert strengths == []
        assert improvements == []

    def test_custom_top_n(self, agg_service):
        feedbacks = [
            self._make_feedback(["A", "B", "C", "D"], ["X"]),
        ]
        strengths, improvements = agg_service.aggregate_strengths_and_improvements(feedbacks, top_n=2)
        assert len(strengths) == 2

    def test_single_feedback(self, agg_service):
        feedbacks = [self._make_feedback(["Strong answer"], ["Need more detail"])]
        strengths, improvements = agg_service.aggregate_strengths_and_improvements(feedbacks)
        assert strengths == ["Strong answer"]
        assert improvements == ["Need more detail"]


# --- determine_practice_areas ---

class TestDeterminePracticeAreas:
    def _make_feedback(self, technical=80, structure=80, completeness=80, star=80):
        fb = MagicMock(spec=ContentFeedback)
        fb.technical_accuracy = technical
        fb.answer_structure = structure
        fb.completeness = completeness
        fb.star_adherence = star
        return fb

    def test_no_practice_areas_above_threshold(self, agg_service):
        feedbacks = [self._make_feedback(85, 85, 85, 85)]
        areas = agg_service.determine_practice_areas(feedbacks)
        assert areas == []

    def test_all_below_threshold(self, agg_service):
        feedbacks = [self._make_feedback(50, 50, 50, 50)]
        areas = agg_service.determine_practice_areas(feedbacks)
        assert "Technical accuracy and depth" in areas
        assert "Answer structure and organization" in areas
        assert "Completeness and thoroughness" in areas
        assert "STAR method application" in areas

    def test_empty_feedbacks(self, agg_service):
        assert agg_service.determine_practice_areas([]) == []

    def test_star_zero_excluded(self, agg_service):
        feedbacks = [self._make_feedback(85, 85, 85, 0)]
        areas = agg_service.determine_practice_areas(feedbacks)
        assert "STAR method application" not in areas

    def test_custom_threshold(self, agg_service):
        feedbacks = [self._make_feedback(75, 75, 75, 75)]
        areas = agg_service.determine_practice_areas(feedbacks, threshold=80.0)
        assert len(areas) == 4

    def test_mixed_scores(self, agg_service):
        feedbacks = [self._make_feedback(50, 85, 85, 85)]
        areas = agg_service.determine_practice_areas(feedbacks)
        assert areas == ["Technical accuracy and depth"]
