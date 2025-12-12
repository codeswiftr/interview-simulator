"""Tests for video upload and analysis pipeline."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel, select

from app.db import SessionLocal, engine, get_session
from app.main import app
from app.config import settings
from app.models.feedback import VideoFeedback
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.video_service import VideoService
from app.ai.video_analyzer import VideoMetrics


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


@pytest.fixture(autouse=True)
def enable_video_feature_flag():
    """Enable video features for tests."""
    previous = settings.video_features_enabled
    settings.video_features_enabled = True
    yield
    settings.video_features_enabled = previous


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


async def register_and_login(client: AsyncClient, email: str = "video@example.com") -> str:
    """Register user and return bearer token."""
    await client.post(
        "/api/v1/users/register",
        json={"email": email, "password": "password123"},
    )
    resp = await client.post(
        "/api/v1/users/login",
        json={"email": email, "password": "password123"},
    )
    token = resp.json()["access_token"]
    return f"Bearer {token}"


@pytest.mark.asyncio
async def test_upload_video_updates_response_and_saves_file(client, session_override, tmp_path):
    """Uploading a video should persist file and update the response video_url."""
    token = await register_and_login(client)

    # Build interview context
    user_query = select(User).where(User.email == "video@example.com")
    user = (await session_override.exec(user_query)).first()
    question = Question(
        content="Explain how HTTP works.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    session_override.add_all([question, interview])
    await session_override.commit()
    await session_override.refresh(question)
    await session_override.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript=None,
        duration_seconds=0,
    )
    session_override.add(response)
    await session_override.commit()
    await session_override.refresh(response)

    video_bytes = BytesIO(b"fake-video-data")
    files = {"file": ("answer.webm", video_bytes, "video/webm")}
    data = {"response_id": str(response.id)}

    resp = await client.post(
        "/api/v1/upload/video",
        files=files,
        data=data,
        headers={"Authorization": token},
    )

    assert resp.status_code == 201
    payload = resp.json()
    assert payload["video_url"].startswith("/uploads/video/")
    assert payload["filename"].endswith(".webm")

    # Response should be updated with video_url
    await session_override.refresh(response)
    assert response.video_url == payload["video_url"]

    stored_path = Path(payload["video_url"].lstrip("/"))
    if not stored_path.exists():
        stored_path = Path("backend") / stored_path
    assert stored_path.exists()


@pytest.mark.asyncio
async def test_upload_video_rejects_invalid_extension(client):
    """Invalid video extensions should be rejected."""
    token = await register_and_login(client, email="video2@example.com")
    # Create response for the user
    async with SessionLocal() as session:
        user = (await session.exec(select(User).where(User.email == "video2@example.com"))).first()
        question = Question(
            content="Tell me about yourself.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.EASY,
        )
        interview = InterviewSession(
            user_id=user.id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.IN_PROGRESS,
        )
        session.add_all([question, interview])
        await session.commit()
        await session.refresh(question)
        await session.refresh(interview)

        response = InterviewResponse(
            session_id=interview.id,
            question_id=question.id,
            transcript=None,
            duration_seconds=0,
        )
        session.add(response)
        await session.commit()
        await session.refresh(response)

        files = {"file": ("answer.txt", BytesIO(b"not-video"), "text/plain")}
        data = {"response_id": str(response.id)}
        resp = await client.post(
            "/api/v1/upload/video",
            files=files,
            data=data,
            headers={"Authorization": token},
        )
        assert resp.status_code == 400
        assert "File type not allowed" in resp.text


@pytest.mark.asyncio
async def test_process_response_video_saves_feedback(session_override, tmp_path):
    """VideoService should persist feedback when analysis succeeds."""
    user = User(email="processor@example.com", hashed_password=hash_password("password"))
    session_override.add(user)
    await session_override.commit()
    await session_override.refresh(user)

    question = Question(
        content="Describe a complex system you built.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
    )
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        status=InterviewStatus.IN_PROGRESS,
    )
    session_override.add_all([question, interview])
    await session_override.commit()
    await session_override.refresh(question)
    await session_override.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript=None,
        duration_seconds=0,
        video_url="/uploads/video/sample.webm",
    )
    session_override.add(response)
    await session_override.commit()
    await session_override.refresh(response)

    video_file = tmp_path / "sample.webm"
    video_file.write_bytes(b"video")

    metrics = VideoMetrics(
        confidence_score=0.7,
        nervousness_score=0.2,
        engagement_score=0.6,
        eye_contact_percentage=0.5,
        looking_away_count=1,
        fidget_count=0,
        hand_gesture_frequency=0.3,
        processing_duration_ms=10,
        frame_count=5,
    )

    with patch(
        "app.services.video_service.VideoAnalyzer.analyze",
        new=AsyncMock(return_value=metrics),
    ):
        service = VideoService()
        feedback = await service.process_response_video(
            session_override, response.id, str(video_file)
        )

    assert isinstance(feedback, VideoFeedback)
    assert feedback.confidence_score == metrics.confidence_score
    assert feedback.eye_contact_percentage == metrics.eye_contact_percentage

    # Ensure record is persisted
    result = await session_override.exec(
        select(VideoFeedback).where(VideoFeedback.response_id == response.id)
    )
    saved_feedback = result.first()
    assert saved_feedback is not None
    assert saved_feedback.processing_duration_ms == metrics.processing_duration_ms
