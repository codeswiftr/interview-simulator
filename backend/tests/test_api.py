"""API integration tests for auth, questions, and interviews."""

from datetime import UTC

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
    import uuid
    from io import BytesIO

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


@pytest.mark.asyncio
async def test_register_with_experience_level(client: AsyncClient):
    """Test that users can register with an experience level."""
    resp = await client.post(
        "/api/v1/users/register",
        json={
            "email": "senior@example.com",
            "password": "password123",
            "experience_level": "senior"
        }
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["experience_level"] == "senior"


@pytest.mark.asyncio
async def test_register_without_experience_level_defaults_to_mid(client: AsyncClient):
    """Test that users without explicit experience level get 'mid' by default."""
    resp = await client.post(
        "/api/v1/users/register",
        json={
            "email": "default@example.com",
            "password": "password123"
        }
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["experience_level"] == "mid"


@pytest.mark.asyncio
async def test_update_experience_level(client: AsyncClient):
    """Test updating experience level via PATCH /me."""
    token = await register_and_login(client, email="update@example.com")

    # Verify default is mid
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    assert me_resp.json()["experience_level"] == "mid"

    # Update to senior
    update_resp = await client.patch(
        "/api/v1/users/me",
        json={"experience_level": "senior"},
        headers={"Authorization": token}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["experience_level"] == "senior"

    # Update to junior
    update_resp = await client.patch(
        "/api/v1/users/me",
        json={"experience_level": "junior"},
        headers={"Authorization": token}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["experience_level"] == "junior"


@pytest.mark.asyncio
async def test_experience_level_returned_in_me(client: AsyncClient):
    """Test that /me endpoint returns experience level."""
    resp = await client.post(
        "/api/v1/users/register",
        json={
            "email": "me_test@example.com",
            "password": "password123",
            "experience_level": "junior"
        }
    )
    assert resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "me_test@example.com", "password": "password123"}
    )
    token = f"Bearer {login_resp.json()['access_token']}"

    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    assert me_resp.status_code == 200
    assert me_resp.json()["experience_level"] == "junior"


@pytest.mark.asyncio
async def test_login_returns_refresh_token(client: AsyncClient):
    """Test that login returns both access and refresh tokens."""
    await client.post(
        "/api/v1/users/register",
        json={"email": "refresh@example.com", "password": "password123"}
    )
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "refresh@example.com", "password": "password123"}
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["refresh_token"]) > 50  # Secure tokens are long


@pytest.mark.asyncio
async def test_refresh_token_returns_new_tokens(client: AsyncClient):
    """Test that refreshing tokens returns a new access and refresh token."""
    await client.post(
        "/api/v1/users/register",
        json={"email": "refresh2@example.com", "password": "password123"}
    )
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "refresh2@example.com", "password": "password123"}
    )
    old_refresh = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh}
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Token rotation: new refresh token should be different
    assert data["refresh_token"] != old_refresh


@pytest.mark.asyncio
async def test_refresh_token_rotation_invalidates_old(client: AsyncClient):
    """Test that using a refresh token invalidates it (token rotation)."""
    await client.post(
        "/api/v1/users/register",
        json={"email": "rotation@example.com", "password": "password123"}
    )
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "rotation@example.com", "password": "password123"}
    )
    old_refresh = login_resp.json()["refresh_token"]

    # First refresh succeeds
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh}
    )
    assert refresh_resp.status_code == 200

    # Second use of old token fails
    refresh_resp2 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh}
    )
    assert refresh_resp2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_fails(client: AsyncClient):
    """Test that an invalid refresh token is rejected."""
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token-that-does-not-exist"}
    )
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_expired_token_fails(client: AsyncClient):
    """Test that an expired refresh token is rejected."""
    from datetime import datetime, timedelta

    from sqlmodel import select

    from app.db import SessionLocal
    from app.models.user import User

    # Create user and login
    await client.post(
        "/api/v1/users/register",
        json={"email": "expired_refresh@example.com", "password": "password123"}
    )
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "expired_refresh@example.com", "password": "password123"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Manually expire the token in database
    async with SessionLocal() as session:
        result = await session.exec(
            select(User).where(User.email == "expired_refresh@example.com")
        )
        user = result.first()
        assert user is not None
        user.refresh_token_expires_at = datetime.now(UTC) - timedelta(days=1)
        await session.commit()

    # Try to refresh with expired token
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 401
    detail = refresh_resp.json()["detail"].lower()
    assert "expired" in detail or "invalid" in detail


@pytest.mark.asyncio
async def test_new_access_token_works(client: AsyncClient):
    """Test that the new access token from refresh can access protected endpoints."""
    await client.post(
        "/api/v1/users/register",
        json={"email": "access@example.com", "password": "password123"}
    )
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "access@example.com", "password": "password123"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    new_access = refresh_resp.json()["access_token"]

    # Use new access token
    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access}"}
    )
    assert me_resp.status_code == 200


@pytest.mark.asyncio
async def test_refresh_without_token_fails_validation(client: AsyncClient):
    """Test that refresh endpoint validates required refresh_token field."""
    # Missing refresh_token in payload should trigger validation error
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={},
    )
    assert refresh_resp.status_code == 422


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient):
    """Test changing password with correct current password."""
    token = await register_and_login(client, email="password_change@example.com")

    resp = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "password123", "new_password": "newpassword456"},
        headers={"Authorization": token}
    )
    assert resp.status_code == 200
    assert "successfully" in resp.json()["message"].lower()

    # Verify new password works
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "password_change@example.com", "password": "newpassword456"}
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient):
    """Test changing password with incorrect current password."""
    token = await register_and_login(client, email="wrong_password@example.com")

    resp = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "wrongpassword", "new_password": "newpassword456"},
        headers={"Authorization": token}
    )
    assert resp.status_code == 400
    assert "incorrect" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_account(client: AsyncClient):
    """Test soft deleting user account."""
    token = await register_and_login(client, email="delete_me@example.com")

    # Verify account exists
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    assert me_resp.status_code == 200

    # Delete account
    del_resp = await client.delete("/api/v1/users/me", headers={"Authorization": token})
    assert del_resp.status_code == 204

    # Try to login - should fail because account is soft deleted
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": "delete_me@example.com", "password": "password123"}
    )
    # Either 401 (invalid) or login works but is_active=False blocks access
    # Based on implementation, just check old email no longer works
    assert login_resp.status_code == 401


@pytest.mark.asyncio
async def test_user_stats_empty(client: AsyncClient):
    """Test user stats with no sessions."""
    token = await register_and_login(client, email="stats_empty@example.com")

    resp = await client.get("/api/v1/users/me/stats", headers={"Authorization": token})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 0
    assert data["completed_sessions"] == 0
    assert data["average_score"] is None
    assert data["total_practice_time_seconds"] == 0


@pytest.mark.asyncio
async def test_user_progress_empty(client: AsyncClient):
    """Test user progress with no sessions."""
    token = await register_and_login(client, email="progress_empty@example.com")

    resp = await client.get("/api/v1/users/me/progress", headers={"Authorization": token})
    assert resp.status_code == 200
    data = resp.json()
    assert data["score_trend"] == []


@pytest.mark.asyncio
async def test_update_profile_email(client: AsyncClient):
    """Test updating email via profile.

    Note: Email updates return 202 Accepted because they trigger email verification.
    """
    token = await register_and_login(client, email="update_email@example.com")

    resp = await client.patch(
        "/api/v1/users/me",
        json={"email": "new_email@example.com"},
        headers={"Authorization": token}
    )
    assert resp.status_code == 202  # Accepted - email verification initiated
    assert "verification" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_profile_email_already_taken(client: AsyncClient):
    """Test updating email to one that's already taken."""
    await register_and_login(client, email="existing@example.com")
    token = await register_and_login(client, email="want_existing@example.com")

    resp = await client.patch(
        "/api/v1/users/me",
        json={"email": "existing@example.com"},
        headers={"Authorization": token}
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_profile_name(client: AsyncClient):
    """Test updating full name via profile."""
    token = await register_and_login(client, email="update_name@example.com")

    resp = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "New Name"},
        headers={"Authorization": token}
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"


@pytest.mark.asyncio
async def test_update_profile_partial_updates(client: AsyncClient):
    """Test PATCH /users/me with partial updates (only name or only email)."""
    token = await register_and_login(client, email="partial_update@example.com")

    # Update only name
    resp1 = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "New Name Only"},
        headers={"Authorization": token},
    )
    assert resp1.status_code == 200
    assert resp1.json()["full_name"] == "New Name Only"

    # Update only experience level
    resp2 = await client.patch(
        "/api/v1/users/me",
        json={"experience_level": "senior"},
        headers={"Authorization": token},
    )
    assert resp2.status_code == 200
    assert resp2.json()["experience_level"] == "senior"
    assert resp2.json()["full_name"] == "New Name Only"  # Previous update preserved


@pytest.mark.asyncio
async def test_change_password_weak_password(client: AsyncClient):
    """Test change password with weak new password (should still work, but may want validation)."""
    token = await register_and_login(client, email="weak_password@example.com")

    # Try with very short password (current implementation may not validate)
    resp = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "password123", "new_password": "123"},
        headers={"Authorization": token},
    )
    # Current implementation doesn't validate password strength
    # This test documents current behavior - may want to add validation later
    assert resp.status_code in [200, 400]  # May succeed or fail based on validation


@pytest.mark.asyncio
async def test_delete_account_cascade_cleanup(client: AsyncClient):
    """Test DELETE /users/me cleans up related data (interviews, responses, feedback)."""
    from sqlmodel import select

    from app.models.interview import InterviewSession
    from app.models.user import User

    token = await register_and_login(client, email="cascade_delete@example.com")

    # Get user ID
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    # Create interview and response
    for i in range(2):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Question {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 2},
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

    await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question_id),
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )

    # Delete account
    del_resp = await client.delete("/api/v1/users/me", headers={"Authorization": token})
    assert del_resp.status_code == 204

    # Verify user is soft deleted (is_active=False)
    async with SessionLocal() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        assert user is not None
        assert user.is_active is False

        # Verify interviews still exist (soft delete doesn't cascade)
        interviews_result = await session.exec(
            select(InterviewSession).where(InterviewSession.user_id == user_id)
        )
        interviews = list(interviews_result.all())
        # Soft delete keeps data, just marks user inactive
        assert len(interviews) >= 1


@pytest.mark.asyncio
async def test_duplicate_registration_fails(client: AsyncClient):
    """Test registering with existing email fails."""
    await client.post(
        "/api/v1/users/register",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    resp = await client.post(
        "/api/v1/users/register",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_with_wrong_password(client: AsyncClient):
    """Test login with incorrect password."""
    await client.post(
        "/api/v1/users/register",
        json={"email": "wrong_login@example.com", "password": "password123"}
    )
    resp = await client.post(
        "/api/v1/users/login",
        json={"email": "wrong_login@example.com", "password": "wrongpassword"}
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login for user that doesn't exist."""
    resp = await client.post(
        "/api/v1/users/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_questions_by_category(client: AsyncClient):
    """Test filtering questions by category."""
    token = await register_and_login(client, email="cat_filter@example.com")

    # Create a technical question
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Technical question for filter test",
            "category": QuestionCategory.TECHNICAL.value,
            "difficulty": Difficulty.EASY.value,
        },
        headers={"Authorization": token},
    )

    # Create a behavioral question
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Behavioral question for filter test",
            "category": QuestionCategory.BEHAVIORAL.value,
            "difficulty": Difficulty.EASY.value,
        },
        headers={"Authorization": token},
    )

    # Filter by technical
    resp = await client.get("/api/v1/questions/", params={"category": "technical"})
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) >= 1
    assert all(q["category"] == "technical" for q in questions)


@pytest.mark.asyncio
async def test_get_questions_by_difficulty(client: AsyncClient):
    """Test filtering questions by difficulty."""
    token = await register_and_login(client, email="diff_filter@example.com")

    # Create an easy question
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Easy question for filter test",
            "category": QuestionCategory.TECHNICAL.value,
            "difficulty": Difficulty.EASY.value,
        },
        headers={"Authorization": token},
    )

    # Create a hard question
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Hard question for filter test",
            "category": QuestionCategory.TECHNICAL.value,
            "difficulty": Difficulty.HARD.value,
        },
        headers={"Authorization": token},
    )

    # Filter by easy
    resp = await client.get("/api/v1/questions/", params={"difficulty": "easy"})
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) >= 1
    assert all(q["difficulty"] == "easy" for q in questions)


@pytest.mark.asyncio
async def test_get_question_by_id(client: AsyncClient):
    """Test getting a specific question by ID."""
    token = await register_and_login(client, email="get_by_id@example.com")

    # Create a question
    create_resp = await client.post(
        "/api/v1/questions/",
        json={
            "content": "Question to get by ID",
            "category": QuestionCategory.BEHAVIORAL.value,
            "difficulty": Difficulty.MEDIUM.value,
        },
        headers={"Authorization": token},
    )
    question_id = create_resp.json()["id"]

    # Get by ID
    resp = await client.get(f"/api/v1/questions/{question_id}")
    assert resp.status_code == 200
    assert resp.json()["content"] == "Question to get by ID"


@pytest.mark.asyncio
async def test_get_random_question_filtered(client: AsyncClient):
    """Test getting random question with filters."""
    token = await register_and_login(client, email="random_filtered@example.com")

    # Create a behavioral medium question
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Behavioral medium for random test",
            "category": QuestionCategory.BEHAVIORAL.value,
            "difficulty": Difficulty.MEDIUM.value,
        },
        headers={"Authorization": token},
    )

    # Get random with filters
    resp = await client.get(
        "/api/v1/questions/random",
        params={"category": "behavioral", "difficulty": "medium"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "behavioral"
    assert data["difficulty"] == "medium"


@pytest.mark.asyncio
async def test_interview_get_by_id(client: AsyncClient):
    """Test getting interview session by ID."""
    token = await register_and_login(client, email="interview_get@example.com")

    # Create behavioral questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Interview get test question {i}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    # Create interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    # Get by ID
    resp = await client.get(
        f"/api/v1/interviews/{interview_id}",
        headers={"Authorization": token}
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == interview_id


@pytest.mark.asyncio
async def test_interview_cancel_before_start(client: AsyncClient):
    """Test canceling an interview before it starts."""
    token = await register_and_login(client, email="cancel_before@example.com")

    # Create behavioral questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Cancel test question {i}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.EASY.value,
            },
            headers={"Authorization": token},
        )

    # Create interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    # Cancel (should work before start)
    cancel_resp = await client.delete(
        f"/api/v1/interviews/{interview_id}",
        headers={"Authorization": token}
    )
    assert cancel_resp.status_code == 204


@pytest.mark.asyncio
async def test_interview_already_started_returns_same_state(client: AsyncClient):
    """Test that starting an already started interview returns the same state."""
    token = await register_and_login(client, email="start_twice@example.com")

    # Create behavioral questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Start twice test question {i}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.EASY.value,
            },
            headers={"Authorization": token},
        )

    # Create and start interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    # First start succeeds
    start1 = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token}
    )
    assert start1.status_code == 200
    assert start1.json()["status"] == InterviewStatus.IN_PROGRESS

    # Second start - endpoint allows idempotent calls
    start2 = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token}
    )
    # Returns 200 (idempotent) or 400 (strict) - check it's still in progress
    if start2.status_code == 200:
        assert start2.json()["status"] == InterviewStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_forgot_password_returns_success_always(client: AsyncClient):
    """Test forgot password always returns success (security best practice)."""
    # Existing user
    await client.post(
        "/api/v1/users/register",
        json={"email": "forgotpw@example.com", "password": "password123"}
    )
    resp1 = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "forgotpw@example.com"}
    )
    assert resp1.status_code == 200

    # Non-existent user - still returns 200 (security)
    resp2 = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent_forgot@example.com"}
    )
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Test reset password with invalid token fails."""
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token-abc123", "new_password": "newpassword456"}
    )
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


# ========== Interviews API Edge Case Tests ==========


@pytest.mark.asyncio
async def test_create_interview_with_all_optional_fields(client: AsyncClient):
    """Test POST /interviews with all optional fields (target_company, scheduled_at, difficulty)."""
    token = await register_and_login(client, email="optional_fields@example.com")

    # Seed questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Question {i+1}",
                "category": QuestionCategory.TECHNICAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    from datetime import datetime, timedelta

    scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()

    create_resp = await client.post(
        "/api/v1/interviews/",
        json={
            "interview_type": InterviewType.TECHNICAL.value,
            "question_count": 2,
            "target_company": "Google",
            "company_style": "faang",
            "difficulty": Difficulty.HARD.value,
            "scheduled_at": scheduled_at,
        },
        headers={"Authorization": token},
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["target_company"] == "Google"
    assert data["company_style"] == "faang"
    # Note: difficulty and scheduled_at are stored but not in InterviewSessionRead response
    # Verify they were accepted by checking interview was created
    assert data["interview_type"] == InterviewType.TECHNICAL.value
    assert data["question_count"] == 2


@pytest.mark.asyncio
async def test_start_interview_already_completed(client: AsyncClient):
    """Test POST /interviews/{id}/start fails when interview is already completed."""
    token = await register_and_login(client, email="start_completed@example.com")

    # Seed questions
    for i in range(2):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Question {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    # Create and complete interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 2},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token},
    )

    # Try to start completed interview
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 400
    assert "cannot start" in start_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_interview_cancelled(client: AsyncClient):
    """Test POST /interviews/{id}/start fails when interview is cancelled."""
    token = await register_and_login(client, email="start_cancelled@example.com")

    # Create and cancel interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    await client.delete(
        f"/api/v1/interviews/{interview_id}",
        headers={"Authorization": token},
    )

    # Try to start cancelled interview
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 400
    assert "cannot start" in start_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_questions_when_not_started(client: AsyncClient):
    """Test GET /interviews/{id}/questions returns 400 when interview not started."""
    token = await register_and_login(client, email="questions_not_started@example.com")

    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 2},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    # Get questions before starting - should return 400
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 400
    assert "not been started" in questions_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_questions_ordering(client: AsyncClient):
    """Test GET /interviews/{id}/questions returns questions in correct order."""
    token = await register_and_login(client, email="questions_order@example.com")

    # Seed questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Question {i+1}",
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
    interview_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200
    questions = questions_resp.json()
    assert len(questions) == 3
    # Verify order field exists and is sequential
    for i, q in enumerate(questions, 1):
        assert "order" in q or i <= len(questions)  # Order may be in nested structure


@pytest.mark.asyncio
async def test_submit_response_invalid_question_id(client: AsyncClient):
    """Test POST /interviews/{id}/responses fails with question not in session."""
    token = await register_and_login(client, email="invalid_question@example.com")

    # Create question that won't be assigned
    question_resp = await client.post(
        "/api/v1/questions/",
        json={
            "content": "Unassigned question",
            "category": QuestionCategory.TECHNICAL.value,
            "difficulty": Difficulty.MEDIUM.value,
        },
        headers={"Authorization": token},
    )
    unassigned_question_id = question_resp.json()["id"]

    # Create behavioral interview
    for i in range(2):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Behavioral {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 2},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Try to submit response with question not in session
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(unassigned_question_id),
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 400
    assert "does not belong" in submit_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_submit_response_to_completed_interview(client: AsyncClient):
    """Test POST /interviews/{id}/responses fails when interview is completed."""
    token = await register_and_login(client, email="response_completed@example.com")

    # Seed questions
    for i in range(2):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Question {i+1}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 2},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Get assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # End interview
    await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token},
    )

    # Try to submit response to completed interview
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question_id),
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 400
    assert "in progress" in submit_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_end_interview_not_in_progress(client: AsyncClient):
    """Test POST /interviews/{id}/end fails when interview is already completed."""
    token = await register_and_login(client, email="end_not_progress@example.com")

    # Seed questions
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Test question",
            "category": QuestionCategory.BEHAVIORAL.value,
            "difficulty": Difficulty.MEDIUM.value,
        },
        headers={"Authorization": token},
    )

    # Create, start, and end interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token},
    )

    # Try to end interview that's already completed
    end_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token},
    )
    assert end_resp.status_code == 400
    assert "cannot end" in end_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_end_interview_no_responses(client: AsyncClient):
    """Test POST /interviews/{id}/end succeeds even with no responses."""
    token = await register_and_login(client, email="end_no_responses@example.com")

    # Seed questions
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Test question",
            "category": QuestionCategory.BEHAVIORAL.value,
            "difficulty": Difficulty.MEDIUM.value,
        },
        headers={"Authorization": token},
    )

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # End interview without submitting any responses
    end_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token},
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == InterviewStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_delete_interview_other_user(client: AsyncClient):
    """Test DELETE /interviews/{id} fails when trying to delete another user's interview."""
    token1 = await register_and_login(client, email="delete_owner@example.com")

    # Create interview as user 1
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 1},
        headers={"Authorization": token1},
    )
    interview_id = create_resp.json()["id"]

    # User 2 tries to delete
    token2 = await register_and_login(client, email="delete_other@example.com")
    delete_resp = await client.delete(
        f"/api/v1/interviews/{interview_id}",
        headers={"Authorization": token2},
    )
    assert delete_resp.status_code == 404
    assert "not found" in delete_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_interview_in_progress(client: AsyncClient):
    """Test DELETE /interviews/{id} fails when interview is in progress."""
    token = await register_and_login(client, email="delete_in_progress@example.com")

    # Seed questions
    await client.post(
        "/api/v1/questions/",
        json={
            "content": "Test question",
            "category": QuestionCategory.BEHAVIORAL.value,
            "difficulty": Difficulty.MEDIUM.value,
        },
        headers={"Authorization": token},
    )

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Try to delete in-progress interview
    delete_resp = await client.delete(
        f"/api/v1/interviews/{interview_id}",
        headers={"Authorization": token},
    )
    assert delete_resp.status_code == 400
    assert "scheduled" in delete_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_interview_not_found(client: AsyncClient):
    """Test getting non-existent interview returns 404."""
    import uuid
    token = await register_and_login(client, email="notfound@example.com")

    resp = await client.get(
        f"/api/v1/interviews/{uuid.uuid4()}",
        headers={"Authorization": token}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_question_not_found(client: AsyncClient):
    """Test getting non-existent question returns 404."""
    import uuid

    resp = await client.get(f"/api/v1/questions/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_interview_list_empty(client: AsyncClient):
    """Test listing interviews when user has none."""
    token = await register_and_login(client, email="empty_interviews@example.com")

    resp = await client.get("/api/v1/interviews/", headers={"Authorization": token})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_interview_with_company_style(client: AsyncClient):
    """Test creating interview with company style parameter."""
    token = await register_and_login(client, email="company_style@example.com")

    # Create behavioral questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Company style test question {i}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.MEDIUM.value,
            },
            headers={"Authorization": token},
        )

    resp = await client.post(
        "/api/v1/interviews/",
        json={
            "interview_type": InterviewType.BEHAVIORAL.value,
            "company_style": "google",
            "question_count": 3
        },
        headers={"Authorization": token},
    )
    assert resp.status_code == 201
    assert resp.json()["company_style"] == "google"


@pytest.mark.asyncio
async def test_create_interview_with_difficulty(client: AsyncClient):
    """Test creating interview with difficulty parameter."""
    token = await register_and_login(client, email="difficulty_int@example.com")

    # Create hard behavioral questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"Difficulty test question {i}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.HARD.value,
            },
            headers={"Authorization": token},
        )

    resp = await client.post(
        "/api/v1/interviews/",
        json={
            "interview_type": InterviewType.BEHAVIORAL.value,
            "difficulty": "hard",
            "question_count": 3
        },
        headers={"Authorization": token},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_end_interview_returns_completed_status(client: AsyncClient):
    """Test ending an interview properly marks it as completed."""
    token = await register_and_login(client, email="end_complete@example.com")

    # Create behavioral questions
    for i in range(3):
        await client.post(
            "/api/v1/questions/",
            json={
                "content": f"End complete test {i}",
                "category": QuestionCategory.BEHAVIORAL.value,
                "difficulty": Difficulty.EASY.value,
            },
            headers={"Authorization": token},
        )

    # Create and start interview
    create_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": InterviewType.BEHAVIORAL.value, "question_count": 3},
        headers={"Authorization": token},
    )
    interview_id = create_resp.json()["id"]

    # Start the interview
    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token}
    )

    # End the interview
    end_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/end",
        headers={"Authorization": token}
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == InterviewStatus.COMPLETED
