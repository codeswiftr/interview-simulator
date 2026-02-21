"""Pure unit tests for AggregationService _compute_*_dimension methods.

Tests _compute_content_dimension, _compute_delivery_dimension,
_compute_behavioral_dimension, _compute_technical_dimension,
_compute_system_design_dimension, _compute_communication_dimension.
No database required.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.feedback import AudioFeedback, ContentFeedback
from app.models.interview import InterviewResponse, InterviewSession
from app.models.question import Question
from app.services.aggregation_service import AggregationService
from app.services.scoring_service import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


@pytest.fixture
def agg_service(scoring_service):
    return AggregationService(scoring_service)


def _make_session(session_id=None):
    s = MagicMock(spec=InterviewSession)
    s.id = session_id or uuid4()
    return s


def _make_response(session_id, response_id=None, category="behavioral"):
    r = MagicMock(spec=InterviewResponse)
    r.id = response_id or uuid4()
    r.session_id = session_id
    q = MagicMock(spec=Question)
    q.category = category
    return (r, q)


def _make_content_feedback(response_id, overall=75.0, technical=80.0, structure=70.0,
                           completeness=65.0, relevance=85.0, star=60.0):
    cf = MagicMock(spec=ContentFeedback)
    cf.response_id = response_id
    cf.overall_content_score = overall
    cf.technical_accuracy = technical
    cf.answer_structure = structure
    cf.completeness = completeness
    cf.relevance = relevance
    cf.star_adherence = star
    return cf


def _make_audio_feedback(response_id, overall=70.0):
    af = MagicMock(spec=AudioFeedback)
    af.response_id = response_id
    af.overall_audio_score = overall
    return af


class TestComputeContentDimension:
    def test_returns_dimension_with_recent_scores(self, agg_service):
        recent = _make_session()
        prev = _make_session()
        r1, q1 = _make_response(recent.id)
        r2, q2 = _make_response(prev.id)
        cf1 = _make_content_feedback(r1.id, overall=80.0)
        cf2 = _make_content_feedback(r2.id, overall=70.0)
        feedbacks = {r1.id: cf1, r2.id: cf2}

        dim = agg_service._compute_content_dimension(
            [(r1, q1), (r2, q2)], feedbacks, [recent], [prev]
        )
        assert dim is not None
        assert dim.name == "Content"
        assert dim.current_score == 80.0
        assert dim.target_score == 90

    def test_returns_none_when_no_feedbacks(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id)
        dim = agg_service._compute_content_dimension([(r1, q1)], {}, [recent], [])
        assert dim is None

    def test_stable_trend_when_no_previous(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id)
        cf1 = _make_content_feedback(r1.id, overall=75.0)
        dim = agg_service._compute_content_dimension([(r1, q1)], {r1.id: cf1}, [recent], [])
        assert dim.trend == "stable"


class TestComputeDeliveryDimension:
    def test_returns_dimension_with_audio_feedbacks(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id)
        af1 = _make_audio_feedback(r1.id, overall=82.0)
        feedbacks = {r1.id: af1}

        dim = agg_service._compute_delivery_dimension([(r1, q1)], feedbacks, [recent], [])
        assert dim is not None
        assert dim.name == "Delivery"
        assert dim.current_score == 82.0
        assert dim.target_score == 85

    def test_returns_none_without_audio_feedbacks(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id)
        dim = agg_service._compute_delivery_dimension([(r1, q1)], {}, [recent], [])
        assert dim is None


class TestComputeBehavioralDimension:
    def test_filters_by_behavioral_category(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id, category="behavioral")
        r2, q2 = _make_response(recent.id, category="technical")
        cf1 = _make_content_feedback(r1.id, star=80.0, structure=70.0, completeness=60.0)
        cf2 = _make_content_feedback(r2.id, star=90.0, structure=90.0, completeness=90.0)
        feedbacks = {r1.id: cf1, r2.id: cf2}

        dim = agg_service._compute_behavioral_dimension(
            [(r1, q1), (r2, q2)], feedbacks, [recent], []
        )
        assert dim is not None
        assert dim.name == "Behavioral"
        # Only r1 (behavioral) should contribute

    def test_returns_none_no_behavioral_questions(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id, category="technical")
        cf1 = _make_content_feedback(r1.id)
        dim = agg_service._compute_behavioral_dimension(
            [(r1, q1)], {r1.id: cf1}, [recent], []
        )
        assert dim is None


class TestComputeTechnicalDimension:
    def test_includes_technical_and_system_design(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id, category="technical")
        r2, q2 = _make_response(recent.id, category="system_design")
        cf1 = _make_content_feedback(r1.id, technical=80.0, completeness=70.0, relevance=90.0)
        cf2 = _make_content_feedback(r2.id, technical=60.0, completeness=50.0, relevance=70.0)
        feedbacks = {r1.id: cf1, r2.id: cf2}

        dim = agg_service._compute_technical_dimension(
            [(r1, q1), (r2, q2)], feedbacks, [recent], []
        )
        assert dim is not None
        assert dim.name == "Technical"

    def test_excludes_behavioral(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id, category="behavioral")
        cf1 = _make_content_feedback(r1.id)
        dim = agg_service._compute_technical_dimension(
            [(r1, q1)], {r1.id: cf1}, [recent], []
        )
        assert dim is None


class TestComputeSystemDesignDimension:
    def test_only_system_design_questions(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id, category="system_design")
        r2, q2 = _make_response(recent.id, category="technical")
        cf1 = _make_content_feedback(r1.id)
        cf2 = _make_content_feedback(r2.id)
        feedbacks = {r1.id: cf1, r2.id: cf2}

        dim = agg_service._compute_system_design_dimension(
            [(r1, q1), (r2, q2)], feedbacks, [recent], []
        )
        assert dim is not None
        assert dim.name == "System Design"
        assert dim.target_score == 80


class TestComputeCommunicationDimension:
    def test_uses_relevance_and_structure(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id)
        cf1 = _make_content_feedback(r1.id, relevance=80.0, structure=60.0)
        feedbacks = {r1.id: cf1}

        dim = agg_service._compute_communication_dimension(
            [(r1, q1)], feedbacks, [recent], []
        )
        assert dim is not None
        assert dim.name == "Communication"
        # Score = relevance * 0.5 + structure * 0.5 = 80*0.5 + 60*0.5 = 70.0
        assert dim.current_score == 70.0

    def test_returns_none_without_content_feedbacks(self, agg_service):
        recent = _make_session()
        r1, q1 = _make_response(recent.id)
        dim = agg_service._compute_communication_dimension(
            [(r1, q1)], {}, [recent], []
        )
        assert dim is None
