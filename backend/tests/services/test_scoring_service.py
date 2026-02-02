"""Unit tests for ScoringService."""

import pytest

from app.services.scoring_service import ScoringService


@pytest.fixture
def service() -> ScoringService:
    return ScoringService()


def test_calculate_overall_score_default_weights(service: ScoringService) -> None:
    assert service.calculate_overall_score(80, 60) == 76.0


def test_calculate_overall_score_custom_weights(service: ScoringService) -> None:
    assert service.calculate_overall_score(70, 90, content_weight=0.5, audio_weight=0.5) == 80.0


def test_calculate_overall_score_zero_weight(service: ScoringService) -> None:
    assert service.calculate_overall_score(70, 90, content_weight=0.0, audio_weight=0.0) == 0.0


def test_calculate_delivery_score_all_present(service: ScoringService) -> None:
    assert service.calculate_delivery_score(80, 60, 70, 90) == 75.0


def test_calculate_delivery_score_with_none(service: ScoringService) -> None:
    assert service.calculate_delivery_score(80, None, 60, None) == 35.0


def test_calculate_behavioral_score(service: ScoringService) -> None:
    assert service.calculate_behavioral_score(80, 70, 60) == 71.5


def test_calculate_behavioral_score_with_none(service: ScoringService) -> None:
    assert service.calculate_behavioral_score(None, 70, None) == 24.5


def test_calculate_technical_score(service: ScoringService) -> None:
    assert service.calculate_technical_score(80, 70, 60) == 71.5


def test_calculate_technical_score_with_none(service: ScoringService) -> None:
    assert service.calculate_technical_score(None, 70, None) == 24.5


def test_calculate_trend_improving(service: ScoringService) -> None:
    assert service.calculate_trend(85, 80) == "improving"


def test_calculate_trend_declining(service: ScoringService) -> None:
    assert service.calculate_trend(70, 75) == "declining"


def test_calculate_trend_stable(service: ScoringService) -> None:
    assert service.calculate_trend(82, 81, threshold=2.0) == "stable"


def test_calculate_trend_custom_threshold(service: ScoringService) -> None:
    assert service.calculate_trend(83, 81, threshold=1.5) == "improving"


def test_evaluate_skill_dimension_returns_none(service: ScoringService) -> None:
    assert (
        service.evaluate_skill_dimension(
            name="Content",
            recent_scores=[],
            previous_scores=[70, 72],
            sessions_with_data=2,
            target_score=90,
        )
        is None
    )


def test_evaluate_skill_dimension_no_previous(service: ScoringService) -> None:
    dimension = service.evaluate_skill_dimension(
        name="Delivery",
        recent_scores=[80, 70],
        previous_scores=None,
        sessions_with_data=2,
        target_score=85,
    )

    assert dimension is not None
    assert dimension.name == "Delivery"
    assert dimension.current_score == 75.0
    assert dimension.target_score == 85
    assert dimension.sessions_with_data == 2
    assert dimension.trend == "stable"


def test_evaluate_skill_dimension_with_previous(service: ScoringService) -> None:
    dimension = service.evaluate_skill_dimension(
        name="Technical",
        recent_scores=[90, 80],
        previous_scores=[70, 75],
        sessions_with_data=3,
        target_score=85,
    )

    assert dimension is not None
    assert dimension.current_score == 85.0
    assert dimension.trend == "improving"
