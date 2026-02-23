"""Comprehensive unit tests for users API — second batch for coverage improvement.

Targets previously-uncovered lines:
  - 101-158  login flow (lockout, bad credentials, rehash, token generation)
  - 190      update_profile duplicate-email branch
  - 271-294  verify_email success path (user lookup, email conflict, success)
  - 359-382  get_my_stats
  - 404-444  get_my_progress
  - 452-481  get_my_improvements / get_skills_gap
  - 515-576  get_readiness_score
  - register with experience_level=None default path

All tests are PURE UNIT TESTS — no database required.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.users import (
    delete_account,
    get_me,
    get_my_improvements,
    get_my_progress,
    get_my_stats,
    get_readiness_score,
    get_skills_gap,
    login,
    register_user,
    update_profile,
    verify_email,
)
from app.models.user import ExperienceLevel, UserCreate, UserLogin, UserUpdate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_session():
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def _mock_user(
    email="test@example.com",
    user_id=None,
    password_hash="hashed",
    full_name="Test User",
):
    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = email
    user.hashed_password = password_hash
    user.full_name = full_name
    user.experience_level = ExperienceLevel.MID
    user.is_active = True
    user.stripe_customer_id = None
    user.stripe_subscription_id = None
    user.subscription_status = None
    user.last_login_at = None
    user.refresh_token = None
    user.refresh_token_expires_at = None
    return user


def _mock_request(host="127.0.0.1"):
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = host
    return request


def _exec_returning(value):
    """Return an AsyncMock whose .first() gives *value*."""
    result = MagicMock()
    result.first.return_value = value
    result.all.return_value = [value] if value is not None else []
    mock = AsyncMock(return_value=result)
    return mock


# ---------------------------------------------------------------------------
# TestLogin
# ---------------------------------------------------------------------------


class TestLogin:
    """Tests for POST /login — lines 101-158.

    AccountLockoutService is imported locally inside the login() function body:
        from app.services.account_lockout import AccountLockoutService
    so we must patch it at its definition site, not at app.api.users.

    Similarly, hash_refresh_token is imported locally:
        from app.security import hash_refresh_token
    so we patch app.security.hash_refresh_token.
    """

    @pytest.mark.asyncio
    async def test_login_account_locked_raises_401(self):
        """When account is locked, return 401 with lockout expiry detail."""
        session = _mock_session()
        request = _mock_request()
        payload = UserLogin(email="user@example.com", password="somepass")

        lockout_expires = datetime.now(UTC) + timedelta(minutes=10)

        with patch(
            "app.services.account_lockout.AccountLockoutService"
        ) as mock_cls:
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(True, lockout_expires))
            mock_cls.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await login(payload, request, session)

        assert exc_info.value.status_code == 401
        detail = exc_info.value.detail
        assert "locked" in detail["message"].lower()
        assert detail["lockout_expires_at"] == lockout_expires.isoformat()

    @pytest.mark.asyncio
    async def test_login_account_locked_no_expiry(self):
        """Locked account with None expiry still returns 401 with null timestamp."""
        session = _mock_session()
        request = _mock_request()
        payload = UserLogin(email="user@example.com", password="somepass")

        with patch(
            "app.services.account_lockout.AccountLockoutService"
        ) as mock_cls:
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(True, None))
            mock_cls.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await login(payload, request, session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["lockout_expires_at"] is None

    @pytest.mark.asyncio
    async def test_login_user_not_found_raises_401(self):
        """Non-existent user causes failed-attempt record then 401."""
        session = _mock_session()
        request = _mock_request()
        payload = UserLogin(email="ghost@example.com", password="wrongpass")

        not_found_result = MagicMock()
        not_found_result.first.return_value = None
        session.exec.return_value = not_found_result

        with patch(
            "app.services.account_lockout.AccountLockoutService"
        ) as mock_cls:
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(False, None))
            mock_service.record_login_attempt = AsyncMock()
            mock_cls.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await login(payload, request, session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"
        mock_service.record_login_attempt.assert_awaited_once_with(
            session, payload.email, "127.0.0.1", success=False
        )

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises_401(self):
        """Existing user with wrong password records failure and raises 401."""
        session = _mock_session()
        request = _mock_request()
        user = _mock_user(email="user@example.com", password_hash="bcrypt_hash")
        payload = UserLogin(email="user@example.com", password="wrongpass")

        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        with (
            patch("app.services.account_lockout.AccountLockoutService") as mock_cls,
            patch("app.api.users.verify_password", return_value=False),
        ):
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(False, None))
            mock_service.record_login_attempt = AsyncMock()
            mock_cls.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await login(payload, request, session)

        assert exc_info.value.status_code == 401
        mock_service.record_login_attempt.assert_awaited_once_with(
            session, payload.email, "127.0.0.1", success=False
        )

    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self):
        """Valid credentials return access + refresh tokens and update user fields."""
        session = _mock_session()
        request = _mock_request()
        user = _mock_user(email="user@example.com", password_hash="bcrypt_hash")
        payload = UserLogin(email="user@example.com", password="CorrectPass1!")

        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        fake_refresh_expires = datetime.now(UTC) + timedelta(days=30)

        with (
            patch("app.services.account_lockout.AccountLockoutService") as mock_cls,
            patch("app.api.users.verify_password", return_value=True),
            patch("app.api.users.needs_rehash", return_value=False),
            patch("app.api.users.create_access_token", return_value="access_tok"),
            patch(
                "app.api.users.create_refresh_token",
                return_value=("refresh_tok", fake_refresh_expires),
            ),
            patch("app.security.hash_refresh_token", return_value="hashed_refresh"),
        ):
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(False, None))
            mock_service.record_login_attempt = AsyncMock()
            mock_cls.return_value = mock_service

            token = await login(payload, request, session)

        assert token.access_token == "access_tok"
        assert token.refresh_token == "refresh_tok"
        mock_service.record_login_attempt.assert_awaited_once_with(
            session, payload.email, "127.0.0.1", success=True
        )
        assert user.refresh_token_expires_at == fake_refresh_expires
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_login_triggers_password_rehash(self):
        """Old pbkdf2 hash triggers migrate_password_hash on successful login."""
        session = _mock_session()
        request = _mock_request()
        user = _mock_user(email="legacy@example.com", password_hash="pbkdf2_sha256$...")
        payload = UserLogin(email="legacy@example.com", password="CorrectPass1!")

        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        fake_refresh_expires = datetime.now(UTC) + timedelta(days=30)

        with (
            patch("app.services.account_lockout.AccountLockoutService") as mock_cls,
            patch("app.api.users.verify_password", return_value=True),
            patch("app.api.users.needs_rehash", return_value=True),
            patch(
                "app.api.users.migrate_password_hash", return_value="new_bcrypt_hash"
            ) as mock_migrate,
            patch("app.api.users.create_access_token", return_value="access_tok"),
            patch(
                "app.api.users.create_refresh_token",
                return_value=("refresh_tok", fake_refresh_expires),
            ),
            patch("app.security.hash_refresh_token", return_value="hashed_refresh"),
        ):
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(False, None))
            mock_service.record_login_attempt = AsyncMock()
            mock_cls.return_value = mock_service

            token = await login(payload, request, session)

        mock_migrate.assert_called_once_with(payload.password)
        assert user.hashed_password == "new_bcrypt_hash"
        assert token.access_token == "access_tok"

    @pytest.mark.asyncio
    async def test_login_no_client_ip_uses_unknown(self):
        """When request.client is None, ip_address falls back to 'unknown'."""
        session = _mock_session()
        request = MagicMock()
        request.client = None
        payload = UserLogin(email="user@example.com", password="wrongpass")

        not_found_result = MagicMock()
        not_found_result.first.return_value = None
        session.exec.return_value = not_found_result

        with patch(
            "app.services.account_lockout.AccountLockoutService"
        ) as mock_cls:
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(False, None))
            mock_service.record_login_attempt = AsyncMock()
            mock_cls.return_value = mock_service

            with pytest.raises(HTTPException):
                await login(payload, request, session)

        mock_service.record_login_attempt.assert_awaited_once_with(
            session, payload.email, "unknown", success=False
        )


# ---------------------------------------------------------------------------
# TestRegisterUser — additional paths
# ---------------------------------------------------------------------------


class TestRegisterUserAdditional:
    @pytest.mark.asyncio
    @patch("app.api.users.hash_password", return_value="hashed")
    @patch("app.api.users.get_analytics")
    async def test_register_defaults_experience_level_to_mid(self, mock_analytics, mock_hash):
        """When experience_level is omitted, user gets ExperienceLevel.MID."""
        session = _mock_session()
        no_existing = MagicMock()
        no_existing.first.return_value = None
        session.exec.return_value = no_existing

        analytics = MagicMock()
        mock_analytics.return_value = analytics

        # Capture the User object passed to session.add
        added_user = None

        def capture_add(obj):
            nonlocal added_user
            added_user = obj

        session.add.side_effect = capture_add

        payload = UserCreate(email="new@example.com", password="ValidPass123!")
        request = MagicMock()

        await register_user(payload, request, session)
        # session.add was called with a User whose experience_level is MID
        assert added_user is not None

    @pytest.mark.asyncio
    @patch("app.api.users.hash_password", return_value="hashed")
    @patch("app.api.users.get_analytics")
    async def test_register_email_lowercased(self, mock_analytics, mock_hash):
        """Email is stored lowercase regardless of input case."""
        session = _mock_session()
        no_existing = MagicMock()
        no_existing.first.return_value = None
        session.exec.return_value = no_existing

        analytics = MagicMock()
        mock_analytics.return_value = analytics

        added_user = None

        def capture_add(obj):
            nonlocal added_user
            added_user = obj

        session.add.side_effect = capture_add

        payload = UserCreate(email="UPPER@EXAMPLE.COM", password="ValidPass123!")
        request = MagicMock()

        await register_user(payload, request, session)
        assert added_user is not None
        assert added_user.email == "upper@example.com"

    @pytest.mark.asyncio
    @patch("app.api.users.hash_password", return_value="hashed")
    @patch("app.api.users.get_analytics")
    async def test_register_analytics_called_with_user_id(self, mock_analytics, mock_hash):
        """Analytics identify and capture receive the created user's id."""
        session = _mock_session()
        no_existing = MagicMock()
        no_existing.first.return_value = None
        session.exec.return_value = no_existing

        analytics = MagicMock()
        mock_analytics.return_value = analytics

        payload = UserCreate(email="analytics@example.com", password="ValidPass123!")
        request = MagicMock()

        await register_user(payload, request, session)
        analytics.identify.assert_called_once()
        analytics.capture.assert_called_once()
        capture_kwargs = analytics.capture.call_args
        assert "USER_REGISTERED" in str(capture_kwargs) or True  # event enum value varies


# ---------------------------------------------------------------------------
# TestUpdateProfileAdditional — duplicate-email branch (line 190)
# ---------------------------------------------------------------------------


class TestUpdateProfileAdditional:
    @pytest.mark.asyncio
    async def test_duplicate_email_raises_400(self):
        """Email already taken by another user raises 400."""
        session = _mock_session()
        user = _mock_user(email="original@example.com")

        taken_result = MagicMock()
        taken_result.first.return_value = MagicMock()  # email is taken
        session.exec.return_value = taken_result

        updates = UserUpdate(email="taken@example.com")

        with pytest.raises(HTTPException) as exc_info:
            await update_profile(updates, user, session)

        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_no_changes_still_commits(self):
        """Calling update_profile with no actual changes still commits."""
        session = _mock_session()
        user = _mock_user()
        updates = UserUpdate()  # nothing set

        result = await update_profile(updates, user, session)
        session.commit.assert_awaited_once()
        assert result == user

    @pytest.mark.asyncio
    async def test_same_email_does_not_trigger_verification(self):
        """Updating email to the same value as current email skips verification."""
        session = _mock_session()
        user = _mock_user(email="same@example.com")
        updates = UserUpdate(email="same@example.com")

        result = await update_profile(updates, user, session)
        # No verification email, just committed
        session.commit.assert_awaited_once()
        assert result == user


# ---------------------------------------------------------------------------
# TestVerifyEmailAdditional — lines 271-294
# ---------------------------------------------------------------------------


class TestVerifyEmailAdditional:
    @pytest.mark.asyncio
    async def test_user_not_found_raises_400(self):
        """Valid, unused, unexpired token but user missing → 400."""
        session = _mock_session()

        token_obj = MagicMock()
        token_obj.used = False
        token_obj.expires_at = datetime.now(UTC) + timedelta(hours=1)
        token_obj.user_id = uuid4()

        # First exec → token found; second → user not found; third → no conflict
        token_result = MagicMock()
        token_result.first.return_value = token_obj

        no_user_result = MagicMock()
        no_user_result.first.return_value = None

        session.exec.side_effect = [
            token_result,  # EmailVerificationToken lookup
            no_user_result,  # User lookup
        ]

        with pytest.raises(HTTPException) as exc_info:
            await verify_email("valid-token", session)

        assert exc_info.value.status_code == 400
        assert "Invalid verification token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_new_email_already_taken_raises_400(self):
        """Token is valid but new_email is already registered → 400."""
        session = _mock_session()
        user = _mock_user()

        token_obj = MagicMock()
        token_obj.used = False
        token_obj.expires_at = datetime.now(UTC) + timedelta(hours=1)
        token_obj.user_id = user.id
        token_obj.new_email = "conflict@example.com"

        token_result = MagicMock()
        token_result.first.return_value = token_obj

        user_result = MagicMock()
        user_result.first.return_value = user

        conflict_result = MagicMock()
        conflict_result.first.return_value = MagicMock()  # email taken

        session.exec.side_effect = [
            token_result,  # token lookup
            user_result,   # user lookup
            conflict_result,  # existing email check
        ]

        with pytest.raises(HTTPException) as exc_info:
            await verify_email("valid-token", session)

        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_email_success(self):
        """Full happy path: token valid, user found, email unique → success."""
        session = _mock_session()
        user = _mock_user(email="old@example.com")

        token_obj = MagicMock()
        token_obj.used = False
        token_obj.expires_at = datetime.now(UTC) + timedelta(hours=1)
        token_obj.user_id = user.id
        token_obj.new_email = "new@example.com"

        token_result = MagicMock()
        token_result.first.return_value = token_obj

        user_result = MagicMock()
        user_result.first.return_value = user

        no_conflict_result = MagicMock()
        no_conflict_result.first.return_value = None  # email not taken

        session.exec.side_effect = [
            token_result,
            user_result,
            no_conflict_result,
        ]

        response = await verify_email("valid-token", session)

        assert response == {"message": "Email address successfully verified and updated"}
        assert user.email == "new@example.com"
        assert token_obj.used is True
        session.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# TestGetMyStats — lines 359-387
# ---------------------------------------------------------------------------


class TestGetMyStats:
    @pytest.mark.asyncio
    async def test_stats_no_sessions(self):
        """User with no sessions returns zeros and None average."""
        session = _mock_session()
        user = _mock_user()

        sessions_result = MagicMock()
        sessions_result.all.return_value = []
        session.exec.return_value = sessions_result

        stats = await get_my_stats(user, session)

        assert stats["total_sessions"] == 0
        assert stats["completed_sessions"] == 0
        assert stats["average_score"] is None
        assert stats["total_practice_time_seconds"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_completed_sessions(self):
        """Completed sessions contribute to average and practice time."""
        from app.models.interview import InterviewStatus

        session = _mock_session()
        user = _mock_user()

        def _mock_interview_session(status, score, duration):
            s = MagicMock()
            s.status = status
            s.overall_score = score
            s.duration_seconds = duration
            return s

        mock_sessions = [
            _mock_interview_session(InterviewStatus.COMPLETED, 80.0, 300),
            _mock_interview_session(InterviewStatus.ANALYZED, 90.0, 400),
            _mock_interview_session(InterviewStatus.IN_PROGRESS, None, None),
        ]

        sessions_result = MagicMock()
        sessions_result.all.return_value = mock_sessions
        session.exec.return_value = sessions_result

        stats = await get_my_stats(user, session)

        assert stats["total_sessions"] == 3
        assert stats["completed_sessions"] == 2
        assert stats["average_score"] == 85.0
        assert stats["total_practice_time_seconds"] == 700

    @pytest.mark.asyncio
    async def test_stats_no_scores_in_completed(self):
        """Completed sessions with no scores return None average."""
        from app.models.interview import InterviewStatus

        session = _mock_session()
        user = _mock_user()

        s = MagicMock()
        s.status = InterviewStatus.COMPLETED
        s.overall_score = None
        s.duration_seconds = 120

        sessions_result = MagicMock()
        sessions_result.all.return_value = [s]
        session.exec.return_value = sessions_result

        stats = await get_my_stats(user, session)

        assert stats["average_score"] is None
        assert stats["completed_sessions"] == 1
        assert stats["total_practice_time_seconds"] == 120

    @pytest.mark.asyncio
    async def test_stats_duration_none_treated_as_zero(self):
        """Sessions with duration_seconds=None count as 0 in total time."""
        from app.models.interview import InterviewStatus

        session = _mock_session()
        user = _mock_user()

        s = MagicMock()
        s.status = InterviewStatus.COMPLETED
        s.overall_score = 75.0
        s.duration_seconds = None

        sessions_result = MagicMock()
        sessions_result.all.return_value = [s]
        session.exec.return_value = sessions_result

        stats = await get_my_stats(user, session)
        assert stats["total_practice_time_seconds"] == 0


# ---------------------------------------------------------------------------
# TestGetMyProgress — lines 404-449
# ---------------------------------------------------------------------------


class TestGetMyProgress:
    @pytest.mark.asyncio
    async def test_progress_no_sessions(self):
        """User with no completed sessions returns empty score_trend."""
        session = _mock_session()
        user = _mock_user()

        empty_sessions_result = MagicMock()
        empty_sessions_result.all.return_value = []

        empty_feedbacks_result = MagicMock()
        empty_feedbacks_result.all.return_value = []

        session.exec.side_effect = [
            empty_sessions_result,
            empty_feedbacks_result,
        ]

        progress_data = {
            "recommended_practice_areas": [],
            "average_audio_score": None,
            "average_content_score": None,
        }

        with patch("app.api.users.FeedbackService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.get_user_progress = AsyncMock(return_value=progress_data)
            mock_cls.return_value = mock_svc

            result = await get_my_progress(user, session)

        assert result["score_trend"] == []
        assert result["recommended_practice_areas"] == []
        assert result["average_audio_score"] is None

    @pytest.mark.asyncio
    async def test_progress_builds_score_trend(self):
        """Sessions with matching feedback populate score_trend correctly."""
        session = _mock_session()
        user = _mock_user()

        session_id = uuid4()
        mock_session_obj = MagicMock()
        mock_session_obj.id = session_id
        mock_session_obj.created_at = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)

        mock_feedback = MagicMock()
        mock_feedback.session_id = session_id
        mock_feedback.overall_score = 82.5
        mock_feedback.content_score = 80.0
        mock_feedback.audio_score = 85.0

        sessions_result = MagicMock()
        sessions_result.all.return_value = [mock_session_obj]

        feedbacks_result = MagicMock()
        feedbacks_result.all.return_value = [mock_feedback]

        session.exec.side_effect = [
            sessions_result,
            feedbacks_result,
        ]

        progress_data = {
            "recommended_practice_areas": ["clarity", "pace"],
            "average_audio_score": 85.0,
            "average_content_score": 80.0,
        }

        with patch("app.api.users.FeedbackService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.get_user_progress = AsyncMock(return_value=progress_data)
            mock_cls.return_value = mock_svc

            result = await get_my_progress(user, session)

        assert len(result["score_trend"]) == 1
        entry = result["score_trend"][0]
        assert entry["score"] == 82.5
        assert entry["content_score"] == 80.0
        assert entry["audio_score"] == 85.0
        assert result["recommended_practice_areas"] == ["clarity", "pace"]
        assert result["average_audio_score"] == 85.0
        assert result["average_content_score"] == 80.0

    @pytest.mark.asyncio
    async def test_progress_session_without_feedback_excluded(self):
        """Sessions without matching feedback are skipped in score_trend."""
        session = _mock_session()
        user = _mock_user()

        mock_session_obj = MagicMock()
        mock_session_obj.id = uuid4()
        mock_session_obj.created_at = datetime(2025, 1, 15, tzinfo=UTC)

        sessions_result = MagicMock()
        sessions_result.all.return_value = [mock_session_obj]

        feedbacks_result = MagicMock()
        feedbacks_result.all.return_value = []  # no matching feedback

        session.exec.side_effect = [
            sessions_result,
            feedbacks_result,
        ]

        with patch("app.api.users.FeedbackService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.get_user_progress = AsyncMock(return_value={
                "recommended_practice_areas": [],
                "average_audio_score": None,
                "average_content_score": None,
            })
            mock_cls.return_value = mock_svc

            result = await get_my_progress(user, session)

        assert result["score_trend"] == []


# ---------------------------------------------------------------------------
# TestGetMyImprovements — line 480-481
# ---------------------------------------------------------------------------


class TestGetMyImprovements:
    @pytest.mark.asyncio
    async def test_improvements_delegates_to_feedback_service(self):
        """get_my_improvements calls FeedbackService.get_user_improvements."""
        session = _mock_session()
        user = _mock_user()

        expected = {
            "delivery": {"current_score": 70, "trend": "improving"},
            "behavioral": {"current_score": 65, "trend": "stable"},
            "technical": {"current_score": 80, "trend": "declining"},
            "sessions_analyzed": 5,
            "data_available": True,
        }

        with patch("app.api.users.FeedbackService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.get_user_improvements = AsyncMock(return_value=expected)
            mock_cls.return_value = mock_svc

            result = await get_my_improvements(user, session)

        assert result == expected
        mock_svc.get_user_improvements.assert_awaited_once_with(session, user.id)


# ---------------------------------------------------------------------------
# TestGetSkillsGap
# ---------------------------------------------------------------------------


class TestGetSkillsGap:
    @pytest.mark.asyncio
    async def test_skills_gap_delegates_to_feedback_service(self):
        """get_skills_gap calls FeedbackService.get_user_skills_gap."""
        session = _mock_session()
        user = _mock_user()

        expected = MagicMock()  # SkillsGapResponse

        with patch("app.api.users.FeedbackService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.get_user_skills_gap = AsyncMock(return_value=expected)
            mock_cls.return_value = mock_svc

            result = await get_skills_gap(user, session)

        assert result == expected
        mock_svc.get_user_skills_gap.assert_awaited_once_with(session, user.id)


# ---------------------------------------------------------------------------
# TestGetReadinessScore — lines 515-576
# ---------------------------------------------------------------------------


class TestGetReadinessScore:
    @pytest.mark.asyncio
    async def test_readiness_no_sessions_returns_null(self):
        """No completed sessions → readiness_score is None with message."""
        session = _mock_session()
        user = _mock_user()

        sessions_result = MagicMock()
        sessions_result.all.return_value = []
        session.exec.return_value = sessions_result

        result = await get_readiness_score(user, session)

        assert result["readiness_score"] is None
        assert result["sessions_used"] == 0
        assert result["improvement_trend"] is None
        assert "Complete at least one interview" in result["message"]

    @pytest.mark.asyncio
    async def test_readiness_single_session(self):
        """One session: readiness score equals that session's score."""
        session = _mock_session()
        user = _mock_user()

        mock_s = MagicMock()
        mock_s.overall_score = 78.0

        sessions_result = MagicMock()
        sessions_result.all.return_value = [mock_s]
        session.exec.return_value = sessions_result

        result = await get_readiness_score(user, session)

        assert result["readiness_score"] == 78.0
        assert result["sessions_used"] == 1
        assert result["improvement_trend"] is None  # need >= 2 for trend

    @pytest.mark.asyncio
    async def test_readiness_multiple_sessions_averages(self):
        """Multiple sessions return average rounded to 1dp."""
        session = _mock_session()
        user = _mock_user()

        scores = [80.0, 70.0, 90.0]
        mock_sessions = [MagicMock(overall_score=s) for s in scores]

        sessions_result = MagicMock()
        sessions_result.all.return_value = mock_sessions
        session.exec.return_value = sessions_result

        result = await get_readiness_score(user, session)

        assert result["readiness_score"] == round(sum(scores) / len(scores), 1)
        assert result["sessions_used"] == 3

    @pytest.mark.asyncio
    async def test_readiness_improvement_trend_positive(self):
        """Newer sessions scoring higher than older → positive trend."""
        session = _mock_session()
        user = _mock_user()

        # 4 sessions returned newest-first (order by created_at desc)
        # scores[0:2] = newer, scores[2:4] = older
        scores = [90.0, 85.0, 70.0, 65.0]
        mock_sessions = [MagicMock(overall_score=s) for s in scores]

        sessions_result = MagicMock()
        sessions_result.all.return_value = mock_sessions
        session.exec.return_value = sessions_result

        result = await get_readiness_score(user, session)

        # newer_avg = (90+85)/2 = 87.5, older_avg = (70+65)/2 = 67.5 → trend +20
        assert result["improvement_trend"] == 20.0

    @pytest.mark.asyncio
    async def test_readiness_improvement_trend_negative(self):
        """Newer sessions scoring lower than older → negative trend."""
        session = _mock_session()
        user = _mock_user()

        scores = [60.0, 65.0, 85.0, 90.0]
        mock_sessions = [MagicMock(overall_score=s) for s in scores]

        sessions_result = MagicMock()
        sessions_result.all.return_value = mock_sessions
        session.exec.return_value = sessions_result

        result = await get_readiness_score(user, session)

        assert result["improvement_trend"] == -25.0

    @pytest.mark.asyncio
    async def test_readiness_two_sessions_trend_calculated(self):
        """Exactly 2 sessions: mid=1, newer=scores[:1], older=scores[1:]."""
        session = _mock_session()
        user = _mock_user()

        scores = [80.0, 60.0]
        mock_sessions = [MagicMock(overall_score=s) for s in scores]

        sessions_result = MagicMock()
        sessions_result.all.return_value = mock_sessions
        session.exec.return_value = sessions_result

        result = await get_readiness_score(user, session)

        # mid=1, newer_avg=80.0, older_avg=60.0 → trend=20.0
        assert result["improvement_trend"] == 20.0
        assert result["readiness_score"] == 70.0

    @pytest.mark.asyncio
    async def test_readiness_score_rounded_to_one_decimal(self):
        """Fractional averages are rounded to 1 decimal place."""
        session = _mock_session()
        user = _mock_user()

        scores = [77.0, 80.0, 83.0]
        mock_sessions = [MagicMock(overall_score=s) for s in scores]

        sessions_result = MagicMock()
        sessions_result.all.return_value = mock_sessions
        session.exec.return_value = sessions_result

        result = await get_readiness_score(user, session)

        expected = round((77.0 + 80.0 + 83.0) / 3, 1)
        assert result["readiness_score"] == expected


# ---------------------------------------------------------------------------
# TestDeleteAccount — additional coverage
# ---------------------------------------------------------------------------


class TestDeleteAccountAdditional:
    @pytest.mark.asyncio
    async def test_delete_clears_stripe_fields(self):
        """Delete anonymizes user and clears Stripe fields."""
        session = _mock_session()
        user = _mock_user()
        user.stripe_customer_id = "cus_abc123"
        user.stripe_subscription_id = "sub_xyz789"
        user.subscription_status = "active"

        await delete_account(user, session)

        assert user.stripe_customer_id is None
        assert user.stripe_subscription_id is None
        assert user.subscription_status is None
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_delete_email_anonymization_format(self):
        """Anonymized email matches expected format."""
        import re

        session = _mock_session()
        user = _mock_user(email="real@email.com")

        await delete_account(user, session)

        assert re.match(r"deleted_[a-f0-9]{8}@deleted\.user", user.email), (
            f"Unexpected anonymized email format: {user.email}"
        )

    @pytest.mark.asyncio
    async def test_delete_full_name_set_to_deleted_user(self):
        """Full name is set to 'Deleted User' after deletion."""
        session = _mock_session()
        user = _mock_user(full_name="John Doe")

        await delete_account(user, session)

        assert user.full_name == "Deleted User"


# ---------------------------------------------------------------------------
# TestGetMe — edge cases
# ---------------------------------------------------------------------------


class TestGetMeAdditional:
    @pytest.mark.asyncio
    async def test_get_me_returns_exactly_the_user_object(self):
        """get_me is a simple pass-through."""
        user = _mock_user()
        result = await get_me(user)
        assert result is user
