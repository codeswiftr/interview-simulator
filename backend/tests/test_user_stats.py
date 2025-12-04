"""Tests for user stats and progress endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel

from app.db import SessionLocal, engine, get_session
from app.main import app
from app.models.feedback import SessionFeedback
from app.models.interview import InterviewSession, InterviewStatus, InterviewType
from app.models.user import User
from app.security import hash_password


@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    """Create tables once for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_db(prepare_db):
    """Truncate tables between tests."""
    async with engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))
    yield


@pytest.fixture
async def session_override():
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def client(session_override):
    async def _override():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_and_login(client: AsyncClient, email: str = "user@example.com") -> str:
    """Register user and return bearer token."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "password123"})
    resp = await client.post("/api/v1/users/login", json={"email": email, "password": "password123"})
    token = resp.json()["access_token"]
    return f"Bearer {token}"


@pytest.mark.asyncio
async def test_get_my_stats_returns_counts_and_average_score(client, session_override):
    """Test that user stats endpoint returns counts and average score."""
    token = await register_and_login(client, email="stats@example.com")
    
    # Get user ID
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]
    
    # Create some interview sessions
    from sqlmodel import select
    result = await session_override.exec(select(User).where(User.id == user_id))
    user = result.first()
    
    session1 = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
        overall_score=80.0,
        duration_seconds=300,
    )
    session2 = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.ANALYZED,
        overall_score=90.0,
        duration_seconds=600,
    )
    session3 = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        status=InterviewStatus.IN_PROGRESS,
    )
    session_override.add(session1)
    session_override.add(session2)
    session_override.add(session3)
    await session_override.commit()
    
    # Get stats
    stats_resp = await client.get("/api/v1/users/me/stats", headers={"Authorization": token})
    
    assert stats_resp.status_code == 200
    data = stats_resp.json()
    assert data["total_sessions"] == 3
    assert data["completed_sessions"] == 2
    assert data["average_score"] == 85.0  # (80 + 90) / 2
    assert data["total_practice_time_seconds"] == 900  # 300 + 600


@pytest.mark.asyncio
async def test_get_my_progress_returns_trend_and_recommendations(client, session_override):
    """Test that user progress endpoint returns trend data and practice recommendations."""
    token = await register_and_login(client, email="progress@example.com")
    
    # Get user ID
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]
    
    # Create completed sessions with feedback
    from sqlmodel import select
    result = await session_override.exec(select(User).where(User.id == user_id))
    user = result.first()
    
    session1 = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.ANALYZED,
    )
    session2 = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.ANALYZED,
    )
    session_override.add(session1)
    session_override.add(session2)
    await session_override.commit()
    await session_override.refresh(session1)
    await session_override.refresh(session2)
    
    # Create session feedbacks
    feedback1 = SessionFeedback(
        session_id=session1.id,
        overall_score=75.0,
        content_score=80.0,
        audio_score=70.0,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=["Technical accuracy", "Answer structure"],
    )
    feedback2 = SessionFeedback(
        session_id=session2.id,
        overall_score=85.0,
        content_score=90.0,
        audio_score=80.0,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=["Technical accuracy", "Completeness"],
    )
    session_override.add(feedback1)
    session_override.add(feedback2)
    await session_override.commit()
    
    # Get progress
    progress_resp = await client.get("/api/v1/users/me/progress", headers={"Authorization": token})
    
    assert progress_resp.status_code == 200
    data = progress_resp.json()
    assert "score_trend" in data
    assert "recommended_practice_areas" in data
    assert len(data["score_trend"]) == 2
    assert "Technical accuracy" in data["recommended_practice_areas"]
    assert data["average_audio_score"] == 75.0  # (70 + 80) / 2
    assert data["average_content_score"] == 85.0  # (80 + 90) / 2


@pytest.mark.asyncio
async def test_progress_endpoints_require_auth(client):
    """Test that progress endpoints require authentication."""
    stats_resp = await client.get("/api/v1/users/me/stats")
    assert stats_resp.status_code == 401

    progress_resp = await client.get("/api/v1/users/me/progress")
    assert progress_resp.status_code == 401

    readiness_resp = await client.get("/api/v1/users/me/readiness-score")
    assert readiness_resp.status_code == 401


@pytest.mark.asyncio
async def test_readiness_score_returns_null_when_no_sessions(client, session_override):
    """Test that readiness score returns null when user has no completed sessions."""
    token = await register_and_login(client, email="readiness_empty@example.com")

    resp = await client.get("/api/v1/users/me/readiness-score", headers={"Authorization": token})

    assert resp.status_code == 200
    data = resp.json()
    assert data["readiness_score"] is None
    assert data["sessions_used"] == 0
    assert data["improvement_trend"] is None
    assert "message" in data


@pytest.mark.asyncio
async def test_readiness_score_calculates_from_last_5_sessions(client, session_override):
    """Test that readiness score calculates average from last 5 completed sessions."""
    token = await register_and_login(client, email="readiness_calc@example.com")

    # Get user ID
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    from sqlmodel import select
    result = await session_override.exec(select(User).where(User.id == user_id))
    user = result.first()

    # Create 7 sessions (only last 5 should be used)
    scores = [60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]  # Will use 70, 75, 80, 85, 90
    for i, score in enumerate(scores):
        session = InterviewSession(
            user_id=user.id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
            overall_score=score,
        )
        session_override.add(session)
    await session_override.commit()

    resp = await client.get("/api/v1/users/me/readiness-score", headers={"Authorization": token})

    assert resp.status_code == 200
    data = resp.json()
    # Last 5 sessions: 70, 75, 80, 85, 90 -> average = 80
    assert data["readiness_score"] == 80.0
    assert data["sessions_used"] == 5


@pytest.mark.asyncio
async def test_readiness_score_improvement_trend(client, session_override):
    """Test that improvement trend shows difference between newer and older sessions."""
    token = await register_and_login(client, email="readiness_trend@example.com")

    # Get user ID
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    from sqlmodel import select
    result = await session_override.exec(select(User).where(User.id == user_id))
    user = result.first()

    # Create 4 sessions with improving trend (oldest to newest)
    # Sessions created in order: 70, 70, 90, 90
    # When ordered by created_at desc: [90, 90, 70, 70]
    # Newer sessions (first 2): avg = 90
    # Older sessions (last 2): avg = 70
    # Trend should be 90 - 70 = 20
    scores = [70.0, 70.0, 90.0, 90.0]  # Created in this order (oldest to newest)
    for score in scores:
        session = InterviewSession(
            user_id=user.id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
            overall_score=score,
        )
        session_override.add(session)
        await session_override.commit()  # Commit each to ensure different created_at

    resp = await client.get("/api/v1/users/me/readiness-score", headers={"Authorization": token})

    assert resp.status_code == 200
    data = resp.json()
    assert data["sessions_used"] == 4
    assert data["improvement_trend"] == 20.0  # 90 - 70

