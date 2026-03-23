"""Pure unit tests for model classes.

Tests InterviewShare, EmailVerificationToken, LoginAttempt, InterviewAnalytics,
and related schemas. No database required.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.models.analytics import (
    InterviewAnalytics,
)
from app.models.interview_share import (
    InterviewShare,
    InterviewShareCreate,
    SharedInterviewRead,
    default_expiry,
    generate_share_token,
)
from app.models.login_attempt import LoginAttempt


class TestGenerateShareToken:
    def test_returns_string(self):
        token = generate_share_token()
        assert isinstance(token, str)

    def test_tokens_are_unique(self):
        tokens = {generate_share_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_token_is_url_safe(self):
        token = generate_share_token()
        # URL-safe base64 only contains alphanumeric, -, _
        assert all(c.isalnum() or c in "-_" for c in token)


class TestDefaultExpiry:
    def test_returns_future_datetime(self):
        expiry = default_expiry()
        assert expiry > datetime.now(UTC)

    def test_approximately_7_days(self):
        before = datetime.now(UTC)
        expiry = default_expiry()
        _ = datetime.now(UTC)  # upper bound (unused but documents intent)
        delta = expiry - before
        assert timedelta(days=6, hours=23) < delta < timedelta(days=7, hours=1)


class TestInterviewShareIsExpired:
    def test_expired_when_past(self):
        share = InterviewShare(
            interview_id=uuid4(),
            created_by=uuid4(),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert share.is_expired is True

    def test_not_expired_when_future(self):
        share = InterviewShare(
            interview_id=uuid4(),
            created_by=uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        assert share.is_expired is False


class TestInterviewShareCreate:
    def test_schema_accepts_uuid(self):
        uid = uuid4()
        schema = InterviewShareCreate(interview_id=uid)
        assert schema.interview_id == uid


class TestSharedInterviewRead:
    def test_defaults(self):
        schema = SharedInterviewRead(
            interview_type="behavioral",
            overall_score=85.0,
            audio_score=80.0,
            content_score=90.0,
            question_count=3,
            created_at=datetime.now(UTC),
            shared_by="testuser",
        )
        assert schema.responses == []


class TestLoginAttempt:
    def test_default_success_is_false(self):
        attempt = LoginAttempt(email="test@example.com", ip_address="127.0.0.1")
        assert attempt.success is False

    def test_fields_set_correctly(self):
        attempt = LoginAttempt(
            email="test@example.com",
            ip_address="192.168.1.1",
            success=True,
        )
        assert attempt.email == "test@example.com"
        assert attempt.ip_address == "192.168.1.1"
        assert attempt.success is True


class TestInterviewAnalyticsDefaults:
    def test_default_scores_are_zero(self):
        analytics = InterviewAnalytics(
            user_id=uuid4(),
            session_id=uuid4(),
        )
        assert analytics.filler_word_count == 0
        assert analytics.filler_words_per_minute == 0.0
        assert analytics.speaking_pace_wpm == 0.0
        assert analytics.star_compliance_score == 0.0
        assert analytics.overall_confidence_score == 0.0

    def test_fields_set_correctly(self):
        analytics = InterviewAnalytics(
            user_id=uuid4(),
            session_id=uuid4(),
            filler_word_count=15,
            speaking_pace_wpm=145.5,
            star_compliance_score=85.0,
        )
        assert analytics.filler_word_count == 15
        assert analytics.speaking_pace_wpm == 145.5
        assert analytics.star_compliance_score == 85.0
