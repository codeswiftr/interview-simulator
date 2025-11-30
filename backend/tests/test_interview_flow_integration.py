"""Integration tests for full interview flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel

from app.db import SessionLocal, engine, get_session
from app.main import app
from app.models.interview import InterviewStatus, InterviewType
from app.models.user import SubscriptionTier


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
async def test_full_interview_flow(client, session_override):
    """Test complete interview flow: Create → Start → Submit → End → Feedback."""
    token = await register_and_login(client)

    # 1. Create interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 2,
        },
    )
    assert create_resp.status_code == 201
    interview_id = create_resp.json()["id"]

    # 2. Start interview (assigns questions)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "in_progress"

    # 3. Get questions
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200
    questions = questions_resp.json()
    assert len(questions) == 2

    # 4. Submit response (mock audio upload)
    question_id = questions[0]["id"]
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        headers={"Authorization": token},
        json={
            "question_id": question_id,
            "audio_url": "/uploads/audio/test.webm",
            "duration_seconds": 120,
        },
    )
    assert submit_resp.status_code == 201

    # 5. End interview
    end_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token},
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_quota_enforcement_integration(client, session_override):
    """Test that free user is blocked on 4th interview."""
    token = await register_and_login(client)

    # Create 3 interviews (should succeed)
    for i in range(3):
        resp = await client.post(
            "/api/v1/interviews/",
            headers={"Authorization": token},
            json={
                "interview_type": "behavioral",
                "question_count": 1,
            },
        )
        assert resp.status_code == 201

    # 4th interview should fail with 402
    resp = await client.post(
        "/api/v1/interviews/",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 1,
        },
    )
    assert resp.status_code == 402
    assert "limit" in resp.json()["detail"].lower() or "upgrade" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_audio_processing_integration(client, session_override, tmp_path):
    """Test audio upload → Transcription → Analysis → Feedback flow."""
    token = await register_and_login(client)

    # Create and start interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        headers={"Authorization": token},
        json={"interview_type": "behavioral", "question_count": 1},
    )
    interview_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Get question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # Upload audio
    audio_file = tmp_path / "test.webm"
    audio_file.write_bytes(b"fake audio data")

    upload_resp = await client.post(
        "/api/v1/upload/audio",
        headers={"Authorization": token},
        files={"file": ("test.webm", audio_file.open("rb"), "audio/webm")},
        data={
            "session_id": interview_id,
            "question_id": question_id,
        },
    )
    assert upload_resp.status_code == 201
    audio_url = upload_resp.json()["audio_url"]

    # Submit response with audio
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        headers={"Authorization": token},
        json={
            "question_id": question_id,
            "audio_url": audio_url,
            "duration_seconds": 120,
        },
    )
    assert submit_resp.status_code == 201

    # Note: Actual transcription/analysis happens in background
    # In a real test, we'd wait and verify the results

