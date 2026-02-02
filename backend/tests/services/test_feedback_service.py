"""Minimal tests for FeedbackService orchestrator wiring."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.interview import InterviewResponse
from app.services.aggregation_service import AggregationService
from app.services.feedback_persistence_service import FeedbackPersistenceService
from app.services.feedback_service import FeedbackService
from app.services.scoring_service import ScoringService


def test_init_injects_services() -> None:
    scoring = ScoringService()
    persistence = FeedbackPersistenceService()
    aggregation = AggregationService(scoring)

    service = FeedbackService(
        scoring_service=scoring,
        persistence_service=persistence,
        aggregation_service=aggregation,
    )

    assert service.scoring_service is scoring
    assert service.persistence_service is persistence
    assert service.aggregation_service is aggregation
    assert service.content_analyzer is not None
    assert service.video_service is not None


@pytest.mark.asyncio
async def test_generate_feedback_raises_missing_response() -> None:
    service = FeedbackService()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="not found"):
        await service.generate_feedback(mock_session, uuid4())


@pytest.mark.asyncio
async def test_generate_feedback_raises_no_transcript() -> None:
    service = FeedbackService()
    response_id = uuid4()
    mock_response = MagicMock(spec=InterviewResponse)
    mock_response.id = response_id
    mock_response.transcript = None

    call_count = 0

    def exec_side_effect(_query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.first.return_value = mock_response
        else:
            result.first.return_value = None
        return result

    mock_session = AsyncMock()
    mock_session.exec = AsyncMock(side_effect=exec_side_effect)

    with pytest.raises(ValueError, match="no transcript"):
        await service.generate_feedback(mock_session, response_id)
