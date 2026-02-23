"""Integration tests for analytics generation during feedback flow."""

from uuid import uuid4

import pytest

from app.models.analytics import InterviewAnalytics
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus, InterviewType
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.services.feedback_service import FeedbackService
from tests.conftest import requires_db


@requires_db
@pytest.mark.asyncio
async def test_analytics_generated_with_session_feedback(prepare_database, test_session):
    """Test that analytics are automatically generated when session feedback is created."""
    # Create user
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create question
    question = Question(
        content="Tell me about a time you solved a difficult problem",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    test_session.add(question)
    await test_session.commit()
    await test_session.refresh(question)

    # Create interview session
    session = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # Create responses with STAR-compliant transcripts
    response1 = InterviewResponse(
        session_id=session.id,
        question_id=question.id,
        transcript="""
        Um, so basically the situation was that our production system went down during peak hours.
        The task was to restore service as quickly as possible without losing data.
        I took action by analyzing the logs, identifying the root cause, and implementing a fix.
        The result was that we achieved 99.9% uptime for the rest of the quarter.
        """,
        duration_seconds=90,
    )
    response2 = InterviewResponse(
        session_id=session.id,
        question_id=question.id,
        transcript="""
        In another situation, I was working on optimizing database queries.
        The challenge was to reduce query time by at least 50%.
        I implemented query caching and database indexing strategies.
        As a result, we decreased response time by 70% and improved user satisfaction.
        """,
        duration_seconds=75,
    )
    test_session.add(response1)
    test_session.add(response2)
    await test_session.commit()

    # Generate session feedback (should also trigger analytics)
    feedback_service = FeedbackService()
    session_feedback = await feedback_service.generate_session_feedback(test_session, session.id)

    # Verify session feedback was created
    assert session_feedback is not None
    assert session_feedback.overall_score > 0

    # Verify analytics were also created
    from sqlmodel import select

    analytics_result = await test_session.exec(
        select(InterviewAnalytics).where(InterviewAnalytics.session_id == session.id)
    )
    analytics = analytics_result.first()

    assert analytics is not None
    assert analytics.session_id == session.id
    assert analytics.user_id == user.id
    assert analytics.filler_word_count > 0  # Should detect "um", "so", "basically"
    assert analytics.speaking_pace_wpm > 0
    assert analytics.total_duration_seconds == 165.0  # 90 + 75
    assert analytics.star_compliance_score > 0  # Should detect STAR components
    assert 0 <= analytics.overall_confidence_score <= 100


@requires_db
@pytest.mark.asyncio
async def test_analytics_not_duplicated(prepare_database, test_session):
    """Test that analytics are not duplicated if they already exist."""
    # Create user
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create session
    session = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # Create existing analytics
    existing_analytics = InterviewAnalytics(
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
    test_session.add(existing_analytics)
    await test_session.commit()

    # Try to generate analytics again
    from app.services.behavioral_analytics_service import BehavioralAnalyticsService

    analytics_service = BehavioralAnalyticsService()

    with pytest.raises(ValueError, match="Analytics already exist"):
        await analytics_service.calculate_session_analytics(test_session, session.id, user.id)


@requires_db
@pytest.mark.asyncio
async def test_filler_word_detection_accuracy(prepare_database, test_session):
    """Test that filler word detection is accurate."""
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
        status=InterviewStatus.COMPLETED,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # Create response with known filler words
    response = InterviewResponse(
        session_id=session.id,
        question_id=uuid4(),
        transcript="Um, like, you know, I think, uh, basically the solution was, like, actually pretty good, you know?",
        duration_seconds=60,
    )
    test_session.add(response)
    await test_session.commit()

    # Generate analytics
    from app.services.behavioral_analytics_service import BehavioralAnalyticsService

    analytics_service = BehavioralAnalyticsService()
    analytics = await analytics_service.calculate_session_analytics(
        test_session, session.id, user.id
    )

    # Should detect: um, like (2x), you know (2x), uh, basically, actually
    # Total: 8 filler words
    assert analytics.filler_word_count >= 7  # At least 7 of the 8


@requires_db
@pytest.mark.asyncio
async def test_star_compliance_scoring(prepare_database, test_session):
    """Test STAR compliance scoring accuracy."""
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
        status=InterviewStatus.COMPLETED,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # High STAR compliance response
    good_response = InterviewResponse(
        session_id=session.id,
        question_id=uuid4(),
        transcript="""
        The situation was that we had a critical production outage affecting thousands of users.
        My task was to identify the root cause and restore service within one hour.
        I took immediate action by coordinating with the team, analyzing system logs,
        and implementing a targeted fix to the database connection pool.
        The result was that we restored service in 45 minutes and prevented future outages
        by implementing better monitoring. We achieved a 99.95% uptime for the next quarter.
        """,
        duration_seconds=120,
    )
    test_session.add(good_response)
    await test_session.commit()

    # Generate analytics
    from app.services.behavioral_analytics_service import BehavioralAnalyticsService

    analytics_service = BehavioralAnalyticsService()
    analytics = await analytics_service.calculate_session_analytics(
        test_session, session.id, user.id
    )

    # Should score high for STAR compliance (all 4 components present)
    assert analytics.star_compliance_score >= 80.0
