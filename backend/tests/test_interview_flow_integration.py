"""Integration tests for full interview flow."""


import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel

from app.db import SessionLocal, engine, get_session
from app.main import app


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

    # Seed questions for the interview
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Behavioral question {i+1}",
                "category": "behavioral",
                "difficulty": "medium",
            },
            headers={"Authorization": token},
        )

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

    # Seed questions for interviews
    for i in range(5):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Behavioral question {i+1}",
                "category": "behavioral",
                "difficulty": "medium",
            },
            headers={"Authorization": token},
        )

    # Create 3 interviews (should succeed)
    for _ in range(3):
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

    # Seed questions for the interview
    for i in range(2):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Behavioral question {i+1}",
                "category": "behavioral",
                "difficulty": "medium",
            },
            headers={"Authorization": token},
        )

    # Create and start interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        headers={"Authorization": token},
        json={"interview_type": "behavioral", "question_count": 1},
    )
    assert create_resp.status_code == 201
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


@pytest.mark.asyncio
async def test_company_targeted_interview(client, session_override):
    """Test that target_company filters questions by company_tags."""
    token = await register_and_login(client)

    # Seed questions: 2 for Google, 1 for Amazon, 2 general (no company tags)
    google_questions = []
    for i in range(2):
        resp = await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Google behavioral question {i+1}",
                "category": "behavioral",
                "difficulty": "medium",
                "company_tags": ["google"],
            },
            headers={"Authorization": token},
        )
        google_questions.append(resp.json()["id"])

    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Amazon behavioral question",
            "category": "behavioral",
            "difficulty": "medium",
            "company_tags": ["amazon"],
        },
        headers={"Authorization": token},
    )

    general_questions = []
    for i in range(2):
        resp = await client.post(
            "/api/v1/questions/",
            json={
                "content": f"General behavioral question {i+1}",
                "category": "behavioral",
                "difficulty": "medium",
                "company_tags": [],
            },
            headers={"Authorization": token},
        )
        general_questions.append(resp.json()["id"])

    # Create interview targeting Google
    create_resp = await client.post(
        "/api/v1/interviews/",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 2,
            "target_company": "google",
        },
    )
    assert create_resp.status_code == 201
    interview_id = create_resp.json()["id"]
    assert create_resp.json()["target_company"] == "google"

    # Start interview (assigns questions)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200

    # Get questions - should be the 2 Google questions
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200
    questions = questions_resp.json()
    assert len(questions) == 2

    # All questions should be from Google
    question_ids = [q["id"] for q in questions]
    for qid in question_ids:
        assert qid in google_questions


@pytest.mark.asyncio
async def test_company_targeted_interview_fallback(client, session_override):
    """Test fallback to general pool when not enough company-specific questions."""
    token = await register_and_login(client)

    # Seed questions: 1 for Google, 2 general
    google_resp = await client.post(
        "/api/v1/questions/",
        json={
            "content": "Google behavioral question",
            "category": "behavioral",
            "difficulty": "medium",
            "company_tags": ["google"],
        },
        headers={"Authorization": token},
    )
    google_question_id = google_resp.json()["id"]

    general_questions = []
    for i in range(2):
        resp = await client.post(
            "/api/v1/questions/",
            json={
                "content": f"General behavioral question {i+1}",
                "category": "behavioral",
                "difficulty": "medium",
                "company_tags": [],
            },
            headers={"Authorization": token},
        )
        general_questions.append(resp.json()["id"])

    # Request 3 questions targeting Google (only 1 exists)
    create_resp = await client.post(
        "/api/v1/interviews/",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 3,
            "target_company": "google",
        },
    )
    assert create_resp.status_code == 201
    interview_id = create_resp.json()["id"]

    # Start interview (assigns questions)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200

    # Get questions - should be 3 (1 Google + 2 general)
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200
    questions = questions_resp.json()
    assert len(questions) == 3

    # Verify mix of company-specific and general questions
    question_ids = [q["id"] for q in questions]
    assert google_question_id in question_ids


@pytest.mark.asyncio
async def test_interview_without_target_company(client, session_override):
    """Test interview without target_company uses general question pool."""
    token = await register_and_login(client)

    # Seed questions: 1 for Google, 2 general
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Google behavioral question",
            "category": "behavioral",
            "difficulty": "medium",
            "company_tags": ["google"],
        },
        headers={"Authorization": token},
    )

    for i in range(2):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"General behavioral question {i+1}",
                "category": "behavioral",
                "difficulty": "medium",
                "company_tags": [],
            },
            headers={"Authorization": token},
        )

    # Create interview without target_company
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
    assert create_resp.json().get("target_company") is None

    # Start interview (assigns questions)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200

    # Get questions - should be 2 from general pool (any questions)
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200
    questions = questions_resp.json()
    assert len(questions) == 2

