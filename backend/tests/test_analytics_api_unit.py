"""Pure unit tests for app/api/analytics.py.

Covers every endpoint function and the _verify_session_ownership helper.
No database required — all DB interactions and service calls are mocked.

Targets:
- _verify_session_ownership: found path, 404 path (lines 39-50)
- get_session_analytics: happy path, 404 on no analytics (lines 76-91)
- get_user_progress: happy path with data, empty data path (lines 111-114)
- get_analytics_summary: happy path (lines 137-140)
- generate_session_analytics: happy path, ValueError -> 400 path (lines 170-180)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.analytics import (
    _require_admin_key,
    _verify_session_ownership,
    generate_session_analytics,
    get_activation_metrics,
    get_analytics_summary,
    get_session_analytics,
    get_user_progress,
)
from app.models.analytics import (
    AnalyticsSummary,
    InterviewAnalytics,
    InterviewAnalyticsRead,
    ProgressDataPoint,
    ProgressResponse,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _mock_session():
    """Return a fully-mocked AsyncSession."""
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _mock_user(user_id=None):
    """Return a MagicMock that behaves like a User model instance."""
    user = MagicMock()
    user.id = user_id or uuid4()
    return user


def _make_analytics(user_id=None, session_id=None) -> InterviewAnalytics:
    """Create a minimal InterviewAnalytics instance for testing."""
    uid = user_id or uuid4()
    sid = session_id or uuid4()
    return InterviewAnalytics(
        id=uuid4(),
        user_id=uid,
        session_id=sid,
        filler_word_count=3,
        filler_words_per_minute=1.5,
        speaking_pace_wpm=135.0,
        total_duration_seconds=90.0,
        pause_count=2,
        avg_pause_duration=1.5,
        star_compliance_score=70.0,
        overall_confidence_score=80.0,
        created_at=datetime.now(UTC),
    )


def _make_progress_data_point(session_id=None) -> ProgressDataPoint:
    """Create a minimal ProgressDataPoint for testing."""
    return ProgressDataPoint(
        session_id=session_id or uuid4(),
        created_at=datetime.now(UTC),
        filler_words_per_minute=1.5,
        speaking_pace_wpm=135.0,
        star_compliance_score=70.0,
        overall_confidence_score=80.0,
    )


def _make_analytics_summary() -> AnalyticsSummary:
    """Create a minimal AnalyticsSummary for testing."""
    return AnalyticsSummary(
        avg_filler_words_per_minute=1.5,
        avg_speaking_pace_wpm=135.0,
        avg_star_compliance_score=70.0,
        avg_confidence_score=80.0,
        total_sessions_analyzed=3,
        improvement_filler_words=None,
        improvement_star_compliance=None,
        improvement_confidence=None,
    )


# ===========================================================================
# _verify_session_ownership
# ===========================================================================


class TestVerifySessionOwnership:
    """Unit tests for the _verify_session_ownership helper."""

    @pytest.mark.asyncio
    async def test_returns_interview_when_found(self):
        """Should return the InterviewSession when it exists and belongs to user."""
        session = _mock_session()
        interview = MagicMock()
        result = MagicMock()
        result.first.return_value = interview
        session.exec.return_value = result

        found = await _verify_session_ownership(session, uuid4(), uuid4())

        assert found is interview

    @pytest.mark.asyncio
    async def test_exec_called_once(self):
        """DB exec should be called exactly once."""
        session = _mock_session()
        interview = MagicMock()
        result = MagicMock()
        result.first.return_value = interview
        session.exec.return_value = result

        await _verify_session_ownership(session, uuid4(), uuid4())

        session.exec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        """Should raise HTTP 404 when no matching session is found."""
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await _verify_session_ownership(session, uuid4(), uuid4())

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_404_detail_message(self):
        """404 exception detail should mention access denied."""
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await _verify_session_ownership(session, uuid4(), uuid4())

        assert "not found or access denied" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_uses_provided_session_id(self):
        """The query should incorporate the given session_id."""
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = MagicMock()
        session.exec.return_value = result

        session_id = uuid4()
        user_id = uuid4()
        await _verify_session_ownership(session, session_id, user_id)

        # exec was called — we verified it accepted our IDs without raising
        session.exec.assert_awaited_once()


# ===========================================================================
# get_session_analytics
# ===========================================================================


class TestGetSessionAnalytics:
    """Unit tests for GET /sessions/{session_id}."""

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_returns_analytics_read_model(self, mock_service_cls, mock_verify):
        """Should return InterviewAnalyticsRead when analytics exist."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.get_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        result = await get_session_analytics(session_id, user, session)

        assert isinstance(result, InterviewAnalyticsRead)
        assert result.session_id == session_id

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_verify_ownership_called_with_correct_args(
        self, mock_service_cls, mock_verify
    ):
        """_verify_session_ownership should be called with session, session_id, user.id."""
        db = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.get_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        await get_session_analytics(session_id, user, db)

        mock_verify.assert_awaited_once_with(db, session_id, user.id)

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_raises_404_when_analytics_not_found(self, mock_service_cls, mock_verify):
        """Should raise HTTP 404 when the service returns None."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.get_session_analytics = AsyncMock(return_value=None)
        mock_service_cls.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await get_session_analytics(session_id, user, session)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_404_detail_mentions_not_generated(self, mock_service_cls, mock_verify):
        """404 message should mention analytics not yet generated."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.get_session_analytics = AsyncMock(return_value=None)
        mock_service_cls.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await get_session_analytics(session_id, user, session)

        assert "not yet generated" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_service_called_with_session_and_session_id(
        self, mock_service_cls, mock_verify
    ):
        """BehavioralAnalyticsService.get_session_analytics should receive the db session and UUID."""
        db = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.get_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        await get_session_analytics(session_id, user, db)

        mock_service.get_session_analytics.assert_awaited_once_with(db, session_id)

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_returned_model_fields_match_analytics(self, mock_service_cls, mock_verify):
        """All numeric fields in the result should match the analytics record."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.get_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        result = await get_session_analytics(session_id, user, session)

        assert result.filler_word_count == analytics.filler_word_count
        assert result.speaking_pace_wpm == analytics.speaking_pace_wpm
        assert result.star_compliance_score == analytics.star_compliance_score
        assert result.overall_confidence_score == analytics.overall_confidence_score

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_ownership_failure_propagates(self, mock_service_cls, mock_verify):
        """If _verify_session_ownership raises 404, the endpoint propagates it."""
        session = _mock_session()
        user = _mock_user()
        mock_verify.side_effect = HTTPException(status_code=404, detail="not found or access denied")

        with pytest.raises(HTTPException) as exc_info:
            await get_session_analytics(uuid4(), user, session)

        assert exc_info.value.status_code == 404


# ===========================================================================
# get_user_progress
# ===========================================================================


class TestGetUserProgress:
    """Unit tests for GET /progress."""

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_returns_progress_response(self, mock_service_cls):
        """Should return a ProgressResponse with the correct data points."""
        session = _mock_session()
        user = _mock_user()

        data_points = [_make_progress_data_point(), _make_progress_data_point()]
        mock_service = MagicMock()
        mock_service.get_user_progress = AsyncMock(return_value=data_points)
        mock_service_cls.return_value = mock_service

        result = await get_user_progress(user, session)

        assert isinstance(result, ProgressResponse)
        assert result.data_points == data_points
        assert result.total_sessions == 2

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_total_sessions_equals_data_points_length(self, mock_service_cls):
        """total_sessions should always equal len(data_points)."""
        session = _mock_session()
        user = _mock_user()

        data_points = [_make_progress_data_point() for _ in range(5)]
        mock_service = MagicMock()
        mock_service.get_user_progress = AsyncMock(return_value=data_points)
        mock_service_cls.return_value = mock_service

        result = await get_user_progress(user, session)

        assert result.total_sessions == 5
        assert len(result.data_points) == 5

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_returns_empty_progress_when_no_data(self, mock_service_cls):
        """Should return total_sessions=0 and empty list when no analytics exist."""
        session = _mock_session()
        user = _mock_user()

        mock_service = MagicMock()
        mock_service.get_user_progress = AsyncMock(return_value=[])
        mock_service_cls.return_value = mock_service

        result = await get_user_progress(user, session)

        assert result.total_sessions == 0
        assert result.data_points == []

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_service_called_with_session_and_user_id(self, mock_service_cls):
        """Service should be called with the db session and current_user.id."""
        db = _mock_session()
        user = _mock_user()

        mock_service = MagicMock()
        mock_service.get_user_progress = AsyncMock(return_value=[])
        mock_service_cls.return_value = mock_service

        await get_user_progress(user, db)

        mock_service.get_user_progress.assert_awaited_once_with(db, user.id)

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_single_data_point(self, mock_service_cls):
        """Single-element progress list is handled without error."""
        session = _mock_session()
        user = _mock_user()
        point = _make_progress_data_point()

        mock_service = MagicMock()
        mock_service.get_user_progress = AsyncMock(return_value=[point])
        mock_service_cls.return_value = mock_service

        result = await get_user_progress(user, session)

        assert result.total_sessions == 1
        assert result.data_points[0] is point


# ===========================================================================
# get_analytics_summary
# ===========================================================================


class TestGetAnalyticsSummary:
    """Unit tests for GET /summary."""

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_returns_analytics_summary(self, mock_service_cls):
        """Should return the AnalyticsSummary produced by the service."""
        session = _mock_session()
        user = _mock_user()

        summary = _make_analytics_summary()
        mock_service = MagicMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=summary)
        mock_service_cls.return_value = mock_service

        result = await get_analytics_summary(user, session)

        assert result is summary

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_service_called_with_session_and_user_id(self, mock_service_cls):
        """Service should receive the db session and user.id."""
        db = _mock_session()
        user = _mock_user()

        summary = _make_analytics_summary()
        mock_service = MagicMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=summary)
        mock_service_cls.return_value = mock_service

        await get_analytics_summary(user, db)

        mock_service.get_analytics_summary.assert_awaited_once_with(db, user.id)

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_returns_empty_summary_when_no_sessions(self, mock_service_cls):
        """Service returns a zero-value summary when no sessions exist."""
        session = _mock_session()
        user = _mock_user()

        empty_summary = AnalyticsSummary(
            avg_filler_words_per_minute=0.0,
            avg_speaking_pace_wpm=0.0,
            avg_star_compliance_score=0.0,
            avg_confidence_score=0.0,
            total_sessions_analyzed=0,
        )
        mock_service = MagicMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=empty_summary)
        mock_service_cls.return_value = mock_service

        result = await get_analytics_summary(user, session)

        assert result.total_sessions_analyzed == 0
        assert result.avg_confidence_score == 0.0

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_improvement_fields_present_in_result(self, mock_service_cls):
        """Summary with improvement data is passed through unchanged."""
        session = _mock_session()
        user = _mock_user()

        summary = AnalyticsSummary(
            avg_filler_words_per_minute=2.0,
            avg_speaking_pace_wpm=130.0,
            avg_star_compliance_score=75.0,
            avg_confidence_score=82.0,
            total_sessions_analyzed=6,
            improvement_filler_words=-15.0,
            improvement_star_compliance=20.0,
            improvement_confidence=10.0,
        )
        mock_service = MagicMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=summary)
        mock_service_cls.return_value = mock_service

        result = await get_analytics_summary(user, session)

        assert result.improvement_filler_words == -15.0
        assert result.improvement_star_compliance == 20.0
        assert result.improvement_confidence == 10.0

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_new_service_instance_created_per_call(self, mock_service_cls):
        """A new BehavioralAnalyticsService is instantiated on each call."""
        session = _mock_session()
        user = _mock_user()

        mock_service = MagicMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=_make_analytics_summary())
        mock_service_cls.return_value = mock_service

        await get_analytics_summary(user, session)

        mock_service_cls.assert_called_once_with()


# ===========================================================================
# generate_session_analytics
# ===========================================================================


class TestGenerateSessionAnalytics:
    """Unit tests for POST /generate/{session_id}."""

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_returns_analytics_read_on_success(self, mock_service_cls, mock_verify):
        """Should return InterviewAnalyticsRead on successful generation."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        result = await generate_session_analytics(session_id, user, session)

        assert isinstance(result, InterviewAnalyticsRead)
        assert result.session_id == session_id

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_verify_ownership_called(self, mock_service_cls, mock_verify):
        """_verify_session_ownership must be called before analytics generation."""
        db = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        await generate_session_analytics(session_id, user, db)

        mock_verify.assert_awaited_once_with(db, session_id, user.id)

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_raises_400_on_value_error(self, mock_service_cls, mock_verify):
        """ValueError from the service should be converted to HTTP 400."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock(
            side_effect=ValueError("No responses found for session")
        )
        mock_service_cls.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await generate_session_analytics(session_id, user, session)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_400_detail_matches_value_error_message(self, mock_service_cls, mock_verify):
        """HTTP 400 detail should be the original ValueError message."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        error_message = "No responses found for session abc"
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock(
            side_effect=ValueError(error_message)
        )
        mock_service_cls.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await generate_session_analytics(session_id, user, session)

        assert exc_info.value.detail == error_message

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_service_called_with_session_session_id_and_user_id(
        self, mock_service_cls, mock_verify
    ):
        """calculate_session_analytics receives db, session_id, user.id."""
        db = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        await generate_session_analytics(session_id, user, db)

        mock_service.calculate_session_analytics.assert_awaited_once_with(
            db, session_id, user.id
        )

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_ownership_failure_propagates_before_generation(
        self, mock_service_cls, mock_verify
    ):
        """404 from ownership check prevents analytics generation."""
        session = _mock_session()
        user = _mock_user()
        mock_verify.side_effect = HTTPException(status_code=404, detail="not found or access denied")

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock()
        mock_service_cls.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await generate_session_analytics(uuid4(), user, session)

        assert exc_info.value.status_code == 404
        mock_service.calculate_session_analytics.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_raises_400_when_analytics_already_exist(self, mock_service_cls, mock_verify):
        """Duplicate generation (analytics already exist) raises HTTP 400."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock(
            side_effect=ValueError(f"Analytics already exist for session {session_id}")
        )
        mock_service_cls.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await generate_session_analytics(session_id, user, session)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.analytics._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_result_user_id_matches_current_user(self, mock_service_cls, mock_verify):
        """The returned analytics user_id should match the authenticated user."""
        session = _mock_session()
        user = _mock_user()
        session_id = uuid4()

        analytics = _make_analytics(user_id=user.id, session_id=session_id)
        mock_verify.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.calculate_session_analytics = AsyncMock(return_value=analytics)
        mock_service_cls.return_value = mock_service

        result = await generate_session_analytics(session_id, user, session)

        assert result.user_id == user.id


# ---------------------------------------------------------------------------
# _require_admin_key
# ---------------------------------------------------------------------------


class TestRequireAdminKey:
    def test_valid_key_passes(self, monkeypatch):
        monkeypatch.setenv("ADMIN_API_KEY", "secret123")
        # Should not raise
        _require_admin_key("secret123")

    def test_wrong_key_raises_401(self, monkeypatch):
        monkeypatch.setenv("ADMIN_API_KEY", "secret123")
        with pytest.raises(Exception) as exc_info:
            _require_admin_key("wrongkey")
        assert exc_info.value.status_code == 401

    def test_empty_env_key_raises_401(self, monkeypatch):
        monkeypatch.delenv("ADMIN_API_KEY", raising=False)
        with pytest.raises(Exception) as exc_info:
            _require_admin_key("anykey")
        assert exc_info.value.status_code == 401

    def test_empty_header_raises_401(self, monkeypatch):
        monkeypatch.setenv("ADMIN_API_KEY", "secret123")
        with pytest.raises(Exception) as exc_info:
            _require_admin_key("")
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_activation_metrics
# ---------------------------------------------------------------------------


class TestGetActivationMetrics:
    @pytest.mark.asyncio
    async def test_returns_activation_counts(self):
        """Returns dict with total_activated, activated_7d, activated_30d, as_of."""
        session = _mock_session()

        # exec().one() returns count values
        session.exec.return_value.one = MagicMock(side_effect=[5, 2, 4])

        result = await get_activation_metrics(db=session)

        assert result["total_activated"] == 5
        assert result["activated_7d"] == 2
        assert result["activated_30d"] == 4
        assert "as_of" in result

    @pytest.mark.asyncio
    async def test_returns_zeros_when_no_activations(self):
        session = _mock_session()
        session.exec.return_value.one = MagicMock(side_effect=[0, 0, 0])

        result = await get_activation_metrics(db=session)

        assert result["total_activated"] == 0
        assert result["activated_7d"] == 0
        assert result["activated_30d"] == 0

    @pytest.mark.asyncio
    async def test_as_of_is_iso_string(self):
        session = _mock_session()
        session.exec.return_value.one = MagicMock(side_effect=[1, 1, 1])

        result = await get_activation_metrics(db=session)

        # as_of should be parseable as ISO datetime
        from datetime import datetime
        dt = datetime.fromisoformat(result["as_of"])
        assert dt is not None
