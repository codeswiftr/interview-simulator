"""Tests for behavioral analytics service."""

from uuid import uuid4

import pytest

from app.models.analytics import InterviewAnalytics
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus, InterviewType
from app.models.user import User
from app.services.behavioral_analytics_service import BehavioralAnalyticsService
from tests.conftest import requires_db


@pytest.fixture
def analytics_service():
    """Create analytics service instance."""
    return BehavioralAnalyticsService()


def test_analyze_transcript_filler_words(analytics_service):
    """Test filler word extraction from transcript."""
    transcript = "Um, so like, I think basically the solution was actually pretty good, you know?"
    duration_seconds = 60.0

    metrics = analytics_service.analyze_transcript(transcript, duration_seconds)

    assert metrics["filler_word_count"] >= 5  # um, so, like, basically, actually, you know
    assert metrics["filler_words_per_minute"] > 0
    assert metrics["speaking_pace_wpm"] > 0


def test_analyze_transcript_wpm_calculation(analytics_service):
    """Test WPM calculation."""
    transcript = "This is a test transcript with exactly ten words total"
    duration_seconds = 30.0  # 30 seconds = 0.5 minutes

    metrics = analytics_service.analyze_transcript(transcript, duration_seconds)

    # 10 words / 0.5 minutes = 20 WPM
    assert metrics["speaking_pace_wpm"] == 20.0


def test_analyze_transcript_empty(analytics_service):
    """Test handling of empty transcript."""
    metrics = analytics_service.analyze_transcript("", 60.0)

    assert metrics["filler_word_count"] == 0
    assert metrics["filler_words_per_minute"] == 0.0
    assert metrics["speaking_pace_wpm"] == 0.0
    assert metrics["pause_count"] == 0


def test_analyze_transcript_pauses(analytics_service):
    """Test pause detection in transcript."""
    transcript = "I was working on...   and then I implemented the solution"
    duration_seconds = 60.0

    metrics = analytics_service.analyze_transcript(transcript, duration_seconds)

    # Should detect ellipsis and multiple spaces
    assert metrics["pause_count"] > 0
    assert metrics["avg_pause_duration"] > 0


def test_score_star_compliance_full_star(analytics_service):
    """Test STAR scoring with all components present."""
    transcript = """
    In the situation where our system was down, the context was that we had
    a critical task to restore service. The challenge was significant as we
    needed to act quickly. I implemented a solution by analyzing the logs
    and designing a fix. The result was that we achieved 99.9% uptime and
    delivered the improvement ahead of schedule.
    """

    score = analytics_service.score_star_compliance(transcript)

    # Should score high with all components present
    assert score >= 80.0
    assert score <= 100.0


def test_score_star_compliance_partial(analytics_service):
    """Test STAR scoring with partial components."""
    transcript = "I implemented a solution and the result was positive"

    score = analytics_service.score_star_compliance(transcript)

    # Should score lower with only action and result
    assert score > 0
    assert score < 80.0


def test_score_star_compliance_empty(analytics_service):
    """Test STAR scoring with no STAR components."""
    transcript = "This is a generic response without structure"

    score = analytics_service.score_star_compliance(transcript)

    assert score == 0.0


def test_calculate_wpm_score_optimal(analytics_service):
    """Test WPM scoring in optimal range."""
    # Optimal range: 120-150 WPM
    score_120 = analytics_service._calculate_wpm_score(120)
    score_135 = analytics_service._calculate_wpm_score(135)
    score_150 = analytics_service._calculate_wpm_score(150)

    assert score_120 == 100.0
    assert score_135 == 100.0
    assert score_150 == 100.0


def test_calculate_wpm_score_suboptimal(analytics_service):
    """Test WPM scoring outside optimal range."""
    score_too_slow = analytics_service._calculate_wpm_score(80)
    score_too_fast = analytics_service._calculate_wpm_score(200)

    # Should be lower than optimal but not zero
    assert 0 < score_too_slow < 100
    assert 0 < score_too_fast < 100


@requires_db
@pytest.mark.asyncio
async def test_calculate_session_analytics(prepare_database, test_session, analytics_service):
    """Test calculation and storage of session analytics."""
    # Create test user
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create interview session
    session = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # Create responses with transcripts
    response1 = InterviewResponse(
        session_id=session.id,
        question_id=uuid4(),
        transcript="Um, so basically I was in a situation where I had to solve a problem. I implemented a solution and achieved great results.",
        duration_seconds=60,
    )
    response2 = InterviewResponse(
        session_id=session.id,
        question_id=uuid4(),
        transcript="The task was challenging. I took action by designing a new approach. The result was successful delivery.",
        duration_seconds=45,
    )
    test_session.add(response1)
    test_session.add(response2)
    await test_session.commit()

    # Calculate analytics
    analytics = await analytics_service.calculate_session_analytics(
        test_session, session.id, user.id
    )

    assert analytics is not None
    assert analytics.session_id == session.id
    assert analytics.user_id == user.id
    assert analytics.filler_word_count > 0
    assert analytics.speaking_pace_wpm > 0
    assert analytics.total_duration_seconds == 105.0  # 60 + 45
    assert 0 <= analytics.star_compliance_score <= 100
    assert 0 <= analytics.overall_confidence_score <= 100


@requires_db
@pytest.mark.asyncio
async def test_calculate_session_analytics_no_responses(
    prepare_database, test_session, analytics_service
):
    """Test analytics calculation with no responses raises error."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    session = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    with pytest.raises(ValueError, match="No responses found"):
        await analytics_service.calculate_session_analytics(test_session, session.id, user.id)


@requires_db
@pytest.mark.asyncio
async def test_calculate_session_analytics_already_exists(
    prepare_database, test_session, analytics_service
):
    """Test analytics calculation when analytics already exist raises error."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    session = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # Create existing analytics
    existing = InterviewAnalytics(
        user_id=user.id,
        session_id=session.id,
        filler_word_count=5,
        filler_words_per_minute=2.0,
        speaking_pace_wpm=130.0,
        total_duration_seconds=120.0,
        pause_count=3,
        avg_pause_duration=1.5,
        star_compliance_score=75.0,
        overall_confidence_score=80.0,
    )
    test_session.add(existing)
    await test_session.commit()

    with pytest.raises(ValueError, match="Analytics already exist"):
        await analytics_service.calculate_session_analytics(test_session, session.id, user.id)


@requires_db
@pytest.mark.asyncio
async def test_get_session_analytics(prepare_database, test_session, analytics_service):
    """Test retrieving session analytics."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    session = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    analytics = InterviewAnalytics(
        user_id=user.id,
        session_id=session.id,
        filler_word_count=5,
        filler_words_per_minute=2.0,
        speaking_pace_wpm=130.0,
        total_duration_seconds=120.0,
        pause_count=3,
        avg_pause_duration=1.5,
        star_compliance_score=75.0,
        overall_confidence_score=80.0,
    )
    test_session.add(analytics)
    await test_session.commit()

    retrieved = await analytics_service.get_session_analytics(test_session, session.id)

    assert retrieved is not None
    assert retrieved.session_id == session.id
    assert retrieved.filler_word_count == 5
    assert retrieved.speaking_pace_wpm == 130.0


@requires_db
@pytest.mark.asyncio
async def test_get_user_progress(prepare_database, test_session, analytics_service):
    """Test retrieving user progress over time."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create multiple sessions with analytics
    sessions_data = []
    for i in range(3):
        session = InterviewSession(
            user_id=user.id,
            interview_type=InterviewType.BEHAVIORAL,
        )
        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)

        analytics = InterviewAnalytics(
            user_id=user.id,
            session_id=session.id,
            filler_word_count=5 - i,  # Improving over time
            filler_words_per_minute=2.0 - (i * 0.3),
            speaking_pace_wpm=130.0 + (i * 5),
            total_duration_seconds=120.0,
            pause_count=3,
            avg_pause_duration=1.5,
            star_compliance_score=70.0 + (i * 5),  # Improving
            overall_confidence_score=75.0 + (i * 5),  # Improving
        )
        test_session.add(analytics)
        sessions_data.append((session, analytics))

    await test_session.commit()

    # Get progress
    progress = await analytics_service.get_user_progress(test_session, user.id)

    assert len(progress) == 3
    assert progress[0].session_id == sessions_data[0][0].id
    assert progress[2].star_compliance_score == 80.0  # Last session, improved


@requires_db
@pytest.mark.asyncio
async def test_get_analytics_summary(prepare_database, test_session, analytics_service):
    """Test retrieving analytics summary with averages and trends."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create 4 sessions to enable trend calculation
    for i in range(4):
        session = InterviewSession(
            user_id=user.id,
            interview_type=InterviewType.BEHAVIORAL,
        )
        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)

        analytics = InterviewAnalytics(
            user_id=user.id,
            session_id=session.id,
            filler_word_count=5,
            filler_words_per_minute=3.0 - (i * 0.5),  # Improving
            speaking_pace_wpm=130.0,
            total_duration_seconds=120.0,
            pause_count=3,
            avg_pause_duration=1.5,
            star_compliance_score=60.0 + (i * 10),  # Improving
            overall_confidence_score=70.0 + (i * 5),  # Improving
        )
        test_session.add(analytics)

    await test_session.commit()

    # Get summary
    summary = await analytics_service.get_analytics_summary(test_session, user.id)

    assert summary.total_sessions_analyzed == 4
    assert summary.avg_speaking_pace_wpm == 130.0
    assert summary.improvement_star_compliance is not None
    assert summary.improvement_star_compliance > 0  # Should show improvement
    assert summary.improvement_confidence is not None
    assert summary.improvement_confidence > 0  # Should show improvement
    assert summary.improvement_filler_words is not None
    assert summary.improvement_filler_words < 0  # Negative = improvement


@requires_db
@pytest.mark.asyncio
async def test_get_analytics_summary_no_data(prepare_database, test_session, analytics_service):
    """Test analytics summary with no data returns zero values."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    summary = await analytics_service.get_analytics_summary(test_session, user.id)

    assert summary.total_sessions_analyzed == 0
    assert summary.avg_filler_words_per_minute == 0.0
    assert summary.improvement_star_compliance is None
