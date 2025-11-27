"""API integration tests for auth, questions, and interviews."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel

from app.db import SessionLocal, engine, get_session
from app.main import app
from app.models.interview import InterviewStatus, InterviewType
from app.models.question import Difficulty, QuestionCategory


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
async def test_auth_flow(client: AsyncClient):
    token = await register_and_login(client)
    resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_question_crud_and_random(client: AsyncClient):
    token = await register_and_login(client)
    create_resp = await client.post(
        "/api/v1/questions/",
        json={
            "content": "What is polymorphism?",
            "category": QuestionCategory.TECHNICAL.value,
            "difficulty": Difficulty.EASY.value,
            "company_tags": ["faang"],
            "topic_tags": ["oop"],
        },
        headers={"Authorization": token},
    )
    assert create_resp.status_code == 201
    question_id = create_resp.json()["id"]

    list_resp = await client.get("/api/v1/questions/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = await client.get(f"/api/v1/questions/{question_id}")
    assert get_resp.status_code == 200

    random_resp = await client.get("/api/v1/questions/random")
    assert random_resp.status_code == 200
    assert random_resp.json()["id"] == question_id


@pytest.mark.asyncio
async def test_interview_lifecycle(client: AsyncClient):
    token = await register_and_login(client, email="interview@example.com")

    # Seed enough behavioral questions for assignment
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Behavioral question {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    assert create_resp.status_code == 201
    interview_id = create_resp.json()["id"]

    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == InterviewStatus.IN_PROGRESS

    # Verify questions were assigned
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200
    assert len(questions_resp.json()) == 3

    end_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token},
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == InterviewStatus.COMPLETED
    assert end_resp.json()["duration_seconds"] >= 0

    list_resp = await client.get("/api/v1/interviews/", headers={"Authorization": token})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == interview_id

    cancel_resp = await client.delete(
        f"/api/v1/interviews/{interview_id}",
        headers={"Authorization": token},
    )
    # Cannot cancel after completion; expect 400
    assert cancel_resp.status_code == 400


@pytest.mark.asyncio
async def test_response_submission_and_retrieval(client: AsyncClient):
    """Test submitting and retrieving responses to interview questions."""
    token = await register_and_login(client, email="response@example.com")

    # Create a TECHNICAL question that won't be assigned to behavioral interview
    question_resp = await client.post(
        "/api/v1/questions/",
        json={
            "content": "Explain polymorphism in OOP",
            "category": QuestionCategory.TECHNICAL.value,  # Different category
            "difficulty": Difficulty.MEDIUM.value,
        },
        headers={"Authorization": token},
    )
    assert question_resp.status_code == 201
    unlinked_question_id = question_resp.json()["id"]

    # Create enough behavioral questions for the interview
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Tell me about a time {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    # Create an interview
    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    assert interview_resp.status_code == 201
    interview_id = interview_resp.json()["id"]

    # Cannot submit response when interview is not started
    response_data = {
        "question_id": unlinked_question_id,
        "transcript": "This is my answer to the question.",
        "duration_seconds": 120,
        "audio_url": "https://example.com/audio.mp3",
    }
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json=response_data,
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 400
    assert "in progress" in submit_resp.json()["detail"].lower()

    # Start the interview (this assigns behavioral questions)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200

    # Submit response should fail - technical question doesn't belong to behavioral interview
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json=response_data,
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 400
    assert "does not belong" in submit_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_response_with_linked_question(client: AsyncClient, session_override):
    """Test response submission with a properly linked question."""
    from app.models.interview import InterviewQuestion
    from app.models.question import Question

    token = await register_and_login(client, email="linked@example.com")

    # Create a question
    question = Question(
        content="Describe your leadership style",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    # Create an interview
    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 1},
        headers={"Authorization": token},
    )
    assert interview_resp.status_code == 201
    interview_id = interview_resp.json()["id"]

    # Link question to interview
    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
        time_limit_seconds=180,
    )
    session_override.add(interview_question)
    await session_override.commit()

    # Start interview
    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Submit response - should succeed
    response_data = {
        "question_id": str(question.id),
        "transcript": "I believe in servant leadership where I empower my team members.",
        "duration_seconds": 90,
        "audio_url": "https://example.com/audio.mp3",
    }
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json=response_data,
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201
    response_json = submit_resp.json()
    assert response_json["question_id"] == str(question.id)
    assert response_json["transcript"] == response_data["transcript"]
    assert response_json["duration_seconds"] == 90
    assert response_json["word_count"] == 11  # Word count calculated

    # Get all responses for the interview
    get_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/responses",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 200
    responses = get_resp.json()
    assert len(responses) == 1
    assert responses[0]["question_id"] == str(question.id)


@pytest.mark.asyncio
async def test_response_ownership_check(client: AsyncClient, session_override):
    """Test that users can only access their own interview responses."""
    from app.models.interview import InterviewQuestion
    from app.models.question import Question

    # User 1
    token1 = await register_and_login(client, email="user1@example.com")

    # Create question
    question = Question(
        content="System design question",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    # User 1 creates interview
    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.SYSTEM_DESIGN.value},
        headers={"Authorization": token1},
    )
    interview_id = interview_resp.json()["id"]

    # Link question and start
    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token1},
    )

    # User 1 submits response
    await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "My design approach...",
            "duration_seconds": 300,
        },
        headers={"Authorization": token1},
    )

    # User 2 tries to access User 1's responses
    token2 = await register_and_login(client, email="user2@example.com")
    get_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/responses",
        headers={"Authorization": token2},
    )
    assert get_resp.status_code == 404  # Interview not found for user 2


@pytest.mark.asyncio
async def test_audio_upload(client: AsyncClient, session_override):
    """Test audio file upload for interview responses."""
    from io import BytesIO

    token = await register_and_login(client, email="upload@example.com")

    # Create behavioral questions for the interview
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Upload test question {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.EASY.value,
            },
            headers={"Authorization": token},
        )

    # Create and start an interview
    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Get assigned questions
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # Create a fake audio file
    fake_audio = BytesIO(b"fake audio content for testing")
    fake_audio.name = "test.webm"

    # Upload audio
    upload_resp = await client.post(
        "/api/v1/upload/audio",
        files={"file": ("test.webm", fake_audio, "audio/webm")},
        data={"session_id": interview_id, "question_id": question_id},
        headers={"Authorization": token},
    )
    assert upload_resp.status_code == 201
    data = upload_resp.json()
    assert "audio_url" in data
    assert data["file_size_bytes"] == 30
    assert data["filename"].endswith(".webm")


@pytest.mark.asyncio
async def test_audio_upload_invalid_session(client: AsyncClient):
    """Test upload fails for non-existent session."""
    from io import BytesIO
    import uuid

    token = await register_and_login(client, email="invalid@example.com")

    fake_audio = BytesIO(b"test audio")

    # Try to upload to non-existent session
    upload_resp = await client.post(
        "/api/v1/upload/audio",
        files={"file": ("test.mp3", fake_audio, "audio/mpeg")},
        data={"session_id": str(uuid.uuid4()), "question_id": str(uuid.uuid4())},
        headers={"Authorization": token},
    )
    assert upload_resp.status_code == 404
    assert "not found" in upload_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_audio_upload_invalid_format(client: AsyncClient, session_override):
    """Test upload rejects invalid file formats."""
    from io import BytesIO

    token = await register_and_login(client, email="format@example.com")

    # Create questions and interview
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Format test question {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.EASY.value,
            },
            headers={"Authorization": token},
        )

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # Try to upload invalid format
    fake_file = BytesIO(b"not an audio file")
    upload_resp = await client.post(
        "/api/v1/upload/audio",
        files={"file": ("test.txt", fake_file, "text/plain")},
        data={"session_id": interview_id, "question_id": question_id},
        headers={"Authorization": token},
    )
    assert upload_resp.status_code == 400
    assert "not allowed" in upload_resp.json()["detail"].lower()
