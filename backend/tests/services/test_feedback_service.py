"""Minimal tests for FeedbackService orchestrator wiring."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.interview import InterviewResponse, InterviewStatus
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_session() -> AsyncMock:
    """Return a bare AsyncMock that can have exec calls configured."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


def _make_exec_results(*return_values):
    """Build a side_effect list for session.exec where each call returns the
    next MagicMock whose .first() / .all() is pre-configured.

    Each element of *return_values* can be:
    - A single object   -> result.first() returns it; result.all() returns [it]
    - A list            -> result.first() returns list[0]; result.all() returns list
    - None              -> result.first() returns None; result.all() returns []
    """
    results = []
    for val in return_values:
        result = MagicMock()
        if val is None:
            result.first.return_value = None
            result.all.return_value = []
        elif isinstance(val, list):
            result.first.return_value = val[0] if val else None
            result.all.return_value = val
        else:
            result.first.return_value = val
            result.all.return_value = [val]
        results.append(result)
    return results


def _make_mock_interview(session_id=None, user_id=None):
    interview = MagicMock()
    interview.id = session_id or uuid4()
    interview.user_id = user_id or uuid4()
    interview.overall_score = None
    interview.audio_score = None
    interview.content_score = None
    interview.status = None
    return interview


def _make_mock_response(session_id=None, question_id=None, transcript="some text"):
    response = MagicMock(spec=InterviewResponse)
    response.id = uuid4()
    response.session_id = session_id or uuid4()
    response.question_id = question_id or uuid4()
    response.transcript = transcript
    return response


def _make_aggregated(
    overall_score=75.0,
    audio_score=70.0,
    content_score=80.0,
    top_strengths=None,
    top_improvements=None,
    recommended_practice_areas=None,
):
    agg = MagicMock()
    agg.overall_score = overall_score
    agg.audio_score = audio_score
    agg.content_score = content_score
    agg.top_strengths = top_strengths or ["Good structure"]
    agg.top_improvements = top_improvements or ["More detail"]
    agg.recommended_practice_areas = recommended_practice_areas or ["behavioral"]
    return agg


# ---------------------------------------------------------------------------
# generate_session_feedback — lines 127-189
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_session_feedback_generates_missing_feedbacks() -> None:
    """Responses without existing content feedback trigger generate_feedback."""
    session_id = uuid4()
    interview = _make_mock_interview(session_id=session_id)
    response = _make_mock_response(session_id=session_id, transcript="My answer")

    mock_session = _make_mock_session()
    # session.exec calls in order:
    #   1. InterviewSession lookup (generate_session_feedback preamble)
    #   2. InterviewResponse list
    exec_results = _make_exec_results(interview, [response])
    mock_session.exec = AsyncMock(side_effect=exec_results)

    mock_persistence = AsyncMock(spec=FeedbackPersistenceService)
    mock_persistence.exists_for_session.return_value = False
    # First call: no existing feedbacks (so response needs generation)
    mock_content_feedback = MagicMock()
    mock_content_feedback.response_id = response.id
    # After generation, get_all_by_session_id returns one item
    mock_persistence.get_all_by_session_id.side_effect = [
        [],                        # call 1: existing_feedbacks (line 127) — none yet
        [mock_content_feedback],   # call 2: all_feedback (line 137) — now populated
    ]
    mock_persistence.get_audio_by_session_id.return_value = []

    aggregated = _make_aggregated()
    mock_aggregation = AsyncMock(spec=AggregationService)
    mock_aggregation.aggregate_session_feedback.return_value = aggregated

    session_fb = MagicMock()
    mock_persistence.create_session_feedback.return_value = session_fb

    service = FeedbackService(
        persistence_service=mock_persistence,
        aggregation_service=mock_aggregation,
    )

    # generate_feedback is called internally; stub it so it doesn't fail
    stub_generate = AsyncMock(return_value=MagicMock())
    with (
        patch.object(service, "generate_feedback", new=stub_generate),
        patch("app.services.feedback_service.recommend_next_questions", new=AsyncMock(return_value=[])),
        patch("app.services.feedback_service.BehavioralAnalyticsService") as mock_ba_cls,
    ):
        mock_ba_cls.return_value.calculate_session_analytics = AsyncMock()
        result = await service.generate_session_feedback(mock_session, session_id)

    assert result is session_fb
    # generate_feedback was called once for the response that had no feedback
    stub_generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_session_feedback_skips_failed_feedback_generation() -> None:
    """ValueError from generate_feedback is caught and the loop continues."""
    session_id = uuid4()
    interview = _make_mock_interview(session_id=session_id)
    response1 = _make_mock_response(session_id=session_id, transcript="answer 1")
    response2 = _make_mock_response(session_id=session_id, transcript="answer 2")

    mock_session = _make_mock_session()
    exec_results = _make_exec_results(interview, [response1, response2])
    mock_session.exec = AsyncMock(side_effect=exec_results)

    mock_content_feedback = MagicMock()
    mock_content_feedback.response_id = response2.id

    mock_persistence = AsyncMock(spec=FeedbackPersistenceService)
    mock_persistence.exists_for_session.return_value = False
    mock_persistence.get_all_by_session_id.side_effect = [
        [],                        # existing_feedbacks — none
        [mock_content_feedback],   # all_feedback after loop
    ]
    mock_persistence.get_audio_by_session_id.return_value = []

    aggregated = _make_aggregated()
    mock_aggregation = AsyncMock(spec=AggregationService)
    mock_aggregation.aggregate_session_feedback.return_value = aggregated
    mock_persistence.create_session_feedback.return_value = MagicMock()

    service = FeedbackService(
        persistence_service=mock_persistence,
        aggregation_service=mock_aggregation,
    )

    call_count = 0

    async def failing_generate(sess, resp_id):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("analysis failed")
        return MagicMock()

    with (
        patch.object(service, "generate_feedback", new=failing_generate),
        patch("app.services.feedback_service.recommend_next_questions", new=AsyncMock(return_value=[])),
        patch("app.services.feedback_service.BehavioralAnalyticsService") as mock_ba_cls,
    ):
        mock_ba_cls.return_value.calculate_session_analytics = AsyncMock()
        # Should NOT raise — errors are swallowed
        result = await service.generate_session_feedback(mock_session, session_id)

    assert result is not None
    assert call_count == 2  # both responses attempted


@pytest.mark.asyncio
async def test_generate_session_feedback_full_orchestration() -> None:
    """Happy path: all persistence, aggregation, recommendation, analytics called."""
    session_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    interview = _make_mock_interview(session_id=session_id, user_id=user_id)
    response = _make_mock_response(session_id=session_id, question_id=question_id)

    mock_session = _make_mock_session()
    exec_results = _make_exec_results(interview, [response])
    mock_session.exec = AsyncMock(side_effect=exec_results)

    existing_cf = MagicMock()
    existing_cf.response_id = response.id
    audio_fb = MagicMock()

    mock_persistence = AsyncMock(spec=FeedbackPersistenceService)
    mock_persistence.exists_for_session.return_value = False
    # existing_feedbacks already has an entry → no generate_feedback call needed
    mock_persistence.get_all_by_session_id.side_effect = [
        [existing_cf],   # existing_feedbacks (line 127)
        [existing_cf],   # all_feedback (line 137)
    ]
    mock_persistence.get_audio_by_session_id.return_value = [audio_fb]

    aggregated = _make_aggregated(
        overall_score=82.0,
        audio_score=78.0,
        content_score=86.0,
        top_strengths=["Clear examples"],
        top_improvements=["Slow down"],
        recommended_practice_areas=["technical"],
    )
    mock_aggregation = AsyncMock(spec=AggregationService)
    mock_aggregation.aggregate_session_feedback.return_value = aggregated

    session_fb = MagicMock()
    mock_persistence.create_session_feedback.return_value = session_fb

    service = FeedbackService(
        persistence_service=mock_persistence,
        aggregation_service=mock_aggregation,
    )

    recommended_ids = [str(uuid4()), str(uuid4())]

    with (
        patch("app.services.feedback_service.recommend_next_questions", new=AsyncMock(return_value=recommended_ids)),
        patch("app.services.feedback_service.BehavioralAnalyticsService") as mock_ba_cls,
    ):
        mock_ba_inst = mock_ba_cls.return_value
        mock_ba_inst.calculate_session_analytics = AsyncMock()
        result = await service.generate_session_feedback(mock_session, session_id)

    # Verify aggregation called with correct args
    mock_aggregation.aggregate_session_feedback.assert_awaited_once_with(
        mock_session, interview, [existing_cf], [audio_fb]
    )

    # Verify session feedback created with aggregated values
    mock_persistence.create_session_feedback.assert_awaited_once_with(
        mock_session,
        session_id=session_id,
        overall_score=82.0,
        audio_score=78.0,
        content_score=86.0,
        top_strengths=["Clear examples"],
        top_improvements=["Slow down"],
        recommended_practice_areas=["technical"],
        next_question_ids=recommended_ids,
    )

    # Verify interview scores updated
    assert interview.overall_score == 82.0
    assert interview.audio_score == 78.0
    assert interview.content_score == 86.0
    assert interview.status == InterviewStatus.ANALYZED

    # Verify behavioral analytics triggered
    mock_ba_inst.calculate_session_analytics.assert_awaited_once_with(
        mock_session, session_id, user_id
    )

    # Verify commit and refresh called
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(session_fb)

    assert result is session_fb


@pytest.mark.asyncio
async def test_generate_session_feedback_recommendation_failure_handled() -> None:
    """Exception from recommend_next_questions returns empty list, does not raise."""
    session_id = uuid4()
    interview = _make_mock_interview(session_id=session_id)
    response = _make_mock_response(session_id=session_id)

    mock_session = _make_mock_session()
    exec_results = _make_exec_results(interview, [response])
    mock_session.exec = AsyncMock(side_effect=exec_results)

    existing_cf = MagicMock()
    existing_cf.response_id = response.id

    mock_persistence = AsyncMock(spec=FeedbackPersistenceService)
    mock_persistence.exists_for_session.return_value = False
    mock_persistence.get_all_by_session_id.side_effect = [
        [existing_cf],
        [existing_cf],
    ]
    mock_persistence.get_audio_by_session_id.return_value = []
    mock_persistence.create_session_feedback.return_value = MagicMock()

    aggregated = _make_aggregated()
    mock_aggregation = AsyncMock(spec=AggregationService)
    mock_aggregation.aggregate_session_feedback.return_value = aggregated

    service = FeedbackService(
        persistence_service=mock_persistence,
        aggregation_service=mock_aggregation,
    )

    async def boom(*args, **kwargs):
        raise RuntimeError("recommender offline")

    with (
        patch("app.services.feedback_service.recommend_next_questions", new=boom),
        patch("app.services.feedback_service.BehavioralAnalyticsService") as mock_ba_cls,
    ):
        mock_ba_cls.return_value.calculate_session_analytics = AsyncMock()
        result = await service.generate_session_feedback(mock_session, session_id)

    # Should have fallen back to empty list — create_session_feedback called with []
    _, call_kwargs = mock_persistence.create_session_feedback.call_args
    assert call_kwargs["next_question_ids"] == []
    assert result is not None


@pytest.mark.asyncio
async def test_generate_session_feedback_behavioral_analytics_failure_handled() -> None:
    """ValueError from BehavioralAnalyticsService is silently swallowed."""
    session_id = uuid4()
    interview = _make_mock_interview(session_id=session_id)
    response = _make_mock_response(session_id=session_id)

    mock_session = _make_mock_session()
    exec_results = _make_exec_results(interview, [response])
    mock_session.exec = AsyncMock(side_effect=exec_results)

    existing_cf = MagicMock()
    existing_cf.response_id = response.id

    mock_persistence = AsyncMock(spec=FeedbackPersistenceService)
    mock_persistence.exists_for_session.return_value = False
    mock_persistence.get_all_by_session_id.side_effect = [
        [existing_cf],
        [existing_cf],
    ]
    mock_persistence.get_audio_by_session_id.return_value = []
    session_fb = MagicMock()
    mock_persistence.create_session_feedback.return_value = session_fb

    aggregated = _make_aggregated()
    mock_aggregation = AsyncMock(spec=AggregationService)
    mock_aggregation.aggregate_session_feedback.return_value = aggregated

    service = FeedbackService(
        persistence_service=mock_persistence,
        aggregation_service=mock_aggregation,
    )

    with (
        patch("app.services.feedback_service.recommend_next_questions", new=AsyncMock(return_value=[])),
        patch("app.services.feedback_service.BehavioralAnalyticsService") as mock_ba_cls,
    ):
        mock_ba_inst = mock_ba_cls.return_value
        mock_ba_inst.calculate_session_analytics = AsyncMock(side_effect=ValueError("analytics already exist"))
        # Should NOT propagate — ValueError is caught silently
        result = await service.generate_session_feedback(mock_session, session_id)

    assert result is session_fb
    mock_session.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# generate_video_feedback — path resolution (lines 217-225)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_video_feedback_path_resolution_direct() -> None:
    """video_url path exists directly — no fallback needed."""
    relative_video = "uploads/session/video.mp4"

    response_id = uuid4()
    mock_response = MagicMock(spec=InterviewResponse)
    mock_response.id = response_id
    # Service does: Path(video_url.lstrip("/")) → Path("uploads/session/video.mp4")
    mock_response.video_url = "/" + relative_video

    mock_session = _make_mock_session()
    result_obj = MagicMock()
    result_obj.first.side_effect = [mock_response, None]
    mock_session.exec = AsyncMock(return_value=result_obj)

    video_fb = MagicMock()
    service = FeedbackService()

    # Make Path.exists return True for the direct path, so no fallback occurs
    def direct_exists(self: Path) -> bool:
        return str(self) == relative_video

    with (
        patch.object(service.persistence_service, "get_video_by_response_id", new=AsyncMock(return_value=None)),
        patch.object(service.video_service, "process_response_video", new=AsyncMock(return_value=video_fb)) as mock_pvr,
        patch.object(Path, "exists", direct_exists),
    ):
        result = await service.generate_video_feedback(mock_session, response_id)

    assert result is video_fb
    # Path passed to process_response_video should be the direct path (no backend/ prefix)
    resolved_path: str = mock_pvr.call_args[0][2]
    assert resolved_path == relative_video
    assert not resolved_path.startswith("backend/")


@pytest.mark.asyncio
async def test_generate_video_feedback_path_resolution_backend_prefix(tmp_path: Path) -> None:
    """Direct path does not exist — falls back to backend/ prefix."""
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    # relative path: "uploads/video.mp4" — direct does NOT exist; backend/uploads/video.mp4 DOES
    relative_path = "uploads/video.mp4"
    (backend_dir / "uploads").mkdir()
    (backend_dir / "uploads" / "video.mp4").write_bytes(b"video")

    response_id = uuid4()
    mock_response = MagicMock(spec=InterviewResponse)
    mock_response.id = response_id
    mock_response.video_url = "/" + relative_path  # leading slash stripped → "uploads/video.mp4"

    mock_session = _make_mock_session()
    result_obj = MagicMock()
    result_obj.first.side_effect = [mock_response, None]
    mock_session.exec = AsyncMock(return_value=result_obj)

    video_fb = MagicMock()
    service = FeedbackService()

    # Patch Path.exists so direct path returns False and backend/ path returns True
    original_exists = Path.exists

    def patched_exists(self: Path) -> bool:
        if self == Path(relative_path):
            return False
        if self == Path("backend") / relative_path:
            return True
        return original_exists(self)

    with (
        patch.object(service.persistence_service, "get_video_by_response_id", new=AsyncMock(return_value=None)),
        patch.object(service.video_service, "process_response_video", new=AsyncMock(return_value=video_fb)) as mock_pvr,
        patch.object(Path, "exists", patched_exists),
    ):
        result = await service.generate_video_feedback(mock_session, response_id)

    assert result is video_fb
    # Path passed must start with "backend/"
    resolved_path: str = mock_pvr.call_args[0][2]
    assert resolved_path.startswith("backend/")


@pytest.mark.asyncio
async def test_generate_video_feedback_path_not_found() -> None:
    """Neither direct path nor backend/ prefix exists — raises ValueError."""
    response_id = uuid4()
    mock_response = MagicMock(spec=InterviewResponse)
    mock_response.id = response_id
    mock_response.video_url = "/uploads/nonexistent/video.mp4"

    mock_session = _make_mock_session()
    result_obj = MagicMock()
    result_obj.first.side_effect = [mock_response, None]
    mock_session.exec = AsyncMock(return_value=result_obj)

    service = FeedbackService()

    def always_false(self: Path) -> bool:
        return False

    with (
        patch.object(service.persistence_service, "get_video_by_response_id", new=AsyncMock(return_value=None)),
        patch.object(Path, "exists", always_false),
        pytest.raises(ValueError, match="Video file not found"),
    ):
        await service.generate_video_feedback(mock_session, response_id)
