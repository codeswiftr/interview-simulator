"""Tests for analytics API endpoints."""

import pytest
from uuid import uuid4
from unittest.mock import patch

from httpx import AsyncClient

from app.models.analytics import InterviewAnalytics
from app.models.interview import InterviewResponse, InterviewSession, InterviewType, InterviewStatus
from app.models.user import User

from tests.conftest import requires_db


TEST_SECRET = "test-secret-key-minimum-32-characters-long"
TEST_ALGORITHM = "HS256"


@pytest.fixture(autouse=True)
def mock_jwt_config():
    """Mock JWT configuration for all tests."""
    with patch("app.security.get_jwt_secret_key", return_value=TEST_SECRET):
        with patch("app.security.get_jwt_algorithm", return_value=TEST_ALGORITHM):
            yield


def create_test_token(user_id: str) -> str:
    """Create a test JWT token."""
    import jwt
    from datetime import datetime, timedelta, UTC

    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@requires_db
@pytest.mark.asyncio
async def test_get_session_analytics(prepare_database, test_session, client: AsyncClient):
    """Test GET /api/v1/analytics/sessions/{session_id}."""
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
        status=InterviewStatus.COMPLETED,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # Create analytics
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

    # Get analytics
    token = create_test_token(user.id)
    response = await client.get(
        f"/api/v1/analytics/sessions/{session.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == str(session.id)
    assert data["filler_word_count"] == 5
    assert data["speaking_pace_wpm"] == 130.0
    assert data["star_compliance_score"] == 75.0
    assert data["overall_confidence_score"] == 80.0


@requires_db
@pytest.mark.asyncio
async def test_get_session_analytics_unauthorized(prepare_database, test_session, client: AsyncClient):
    """Test GET /api/v1/analytics/sessions/{session_id} without auth fails."""
    session_id = uuid4()

    response = await client.get(f"/api/v1/analytics/sessions/{session_id}")

    assert response.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_get_session_analytics_not_found(prepare_database, test_session, client: AsyncClient):
    """Test GET /api/v1/analytics/sessions/{session_id} for non-existent session."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    token = create_test_token(user.id)
    fake_session_id = uuid4()

    response = await client.get(
        f"/api/v1/analytics/sessions/{fake_session_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@requires_db
@pytest.mark.asyncio
async def test_get_session_analytics_no_analytics(prepare_database, test_session, client: AsyncClient):
    """Test GET /api/v1/analytics/sessions/{session_id} when analytics not generated."""
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

    token = create_test_token(user.id)
    response = await client.get(
        f"/api/v1/analytics/sessions/{session.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "not yet generated" in response.json()["detail"]


@requires_db
@pytest.mark.asyncio
async def test_get_user_progress(prepare_database, test_session, client: AsyncClient):
    """Test GET /api/v1/analytics/progress."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create multiple sessions with analytics
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
            filler_word_count=5,
            filler_words_per_minute=2.0,
            speaking_pace_wpm=130.0 + (i * 5),  # Improving
            total_duration_seconds=120.0,
            pause_count=3,
            avg_pause_duration=1.5,
            star_compliance_score=70.0 + (i * 5),  # Improving
            overall_confidence_score=75.0 + (i * 5),  # Improving
        )
        test_session.add(analytics)

    await test_session.commit()

    token = create_test_token(user.id)
    response = await client.get(
        "/api/v1/analytics/progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_sessions"] == 3
    assert len(data["data_points"]) == 3
    # Check improvement over time
    assert data["data_points"][0]["star_compliance_score"] == 70.0
    assert data["data_points"][2]["star_compliance_score"] == 80.0


@requires_db
@pytest.mark.asyncio
async def test_get_user_progress_empty(prepare_database, test_session, client: AsyncClient):
    """Test GET /api/v1/analytics/progress with no data."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    token = create_test_token(user.id)
    response = await client.get(
        "/api/v1/analytics/progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_sessions"] == 0
    assert data["data_points"] == []


@requires_db
@pytest.mark.asyncio
async def test_get_analytics_summary(prepare_database, test_session, client: AsyncClient):
    """Test GET /api/v1/analytics/summary."""
    user = User(
        email="test@example.com",
        hashed_password="hash",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create 4 sessions for trend calculation
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

    token = create_test_token(user.id)
    response = await client.get(
        "/api/v1/analytics/summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_sessions_analyzed"] == 4
    assert data["avg_speaking_pace_wpm"] == 130.0
    assert data["improvement_star_compliance"] is not None
    assert data["improvement_star_compliance"] > 0
    assert data["improvement_confidence"] is not None
    assert data["improvement_filler_words"] is not None


@requires_db
@pytest.mark.asyncio
async def test_generate_session_analytics(prepare_database, test_session, client: AsyncClient):
    """Test POST /api/v1/analytics/generate/{session_id}."""
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

    # Create response with transcript
    response = InterviewResponse(
        session_id=session.id,
        question_id=uuid4(),
        transcript="Um, so basically I was in a situation where I had to solve a problem. I implemented a solution and achieved great results.",
        duration_seconds=60,
    )
    test_session.add(response)
    await test_session.commit()

    token = create_test_token(user.id)
    api_response = await client.post(
        f"/api/v1/analytics/generate/{session.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert api_response.status_code == 201
    data = api_response.json()
    assert data["session_id"] == str(session.id)
    assert data["user_id"] == str(user.id)
    assert data["filler_word_count"] >= 0
    assert data["speaking_pace_wpm"] > 0
    assert 0 <= data["star_compliance_score"] <= 100
    assert 0 <= data["overall_confidence_score"] <= 100


@requires_db
@pytest.mark.asyncio
async def test_generate_session_analytics_no_responses(prepare_database, test_session, client: AsyncClient):
    """Test POST /api/v1/analytics/generate/{session_id} with no responses."""
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

    token = create_test_token(user.id)
    response = await client.post(
        f"/api/v1/analytics/generate/{session.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "No responses found" in response.json()["detail"]


@requires_db
@pytest.mark.asyncio
async def test_generate_session_analytics_unauthorized_access(prepare_database, test_session, client: AsyncClient):
    """Test POST /api/v1/analytics/generate/{session_id} for other user's session."""
    # Create two users
    user1 = User(
        email="user1@example.com",
        hashed_password="hash",
        full_name="User One",
    )
    user2 = User(
        email="user2@example.com",
        hashed_password="hash",
        full_name="User Two",
    )
    test_session.add(user1)
    test_session.add(user2)
    await test_session.commit()
    await test_session.refresh(user1)
    await test_session.refresh(user2)

    # Create session for user1
    session = InterviewSession(
        user_id=user1.id,
        interview_type=InterviewType.BEHAVIORAL,
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)

    # Try to access with user2's token
    token = create_test_token(user2.id)
    response = await client.post(
        f"/api/v1/analytics/generate/{session.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
