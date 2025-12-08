"""Tests for answer preparation endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel, select

from app.db import SessionLocal, engine, get_session
from app.main import app
from app.models.preparation import (
    AnswerPreparation,
    DeliveryAttempt,
    PreparationQnA,
    PreparationStage,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import SubscriptionTier, User


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


async def register_and_login_pro(client: AsyncClient, session_override, email: str = "user@example.com") -> str:
    """Register Pro tier user and return bearer token."""
    from app.models.user import SubscriptionTier, User

    await client.post("/api/v1/users/register", json={"email": email, "password": "password123"})
    resp = await client.post("/api/v1/users/login", json={"email": email, "password": "password123"})
    token = resp.json()["access_token"]

    # Upgrade to Pro tier for preparation access
    result = await session_override.exec(select(User).where(User.email == email))
    user = result.first()
    if user:
        user.subscription_tier = SubscriptionTier.PRO
        await session_override.commit()

    return f"Bearer {token}"


async def register_and_login_free(client: AsyncClient, email: str = "user@example.com") -> str:
    """Register Free tier user and return bearer token."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "password123"})
    resp = await client.post("/api/v1/users/login", json={"email": email, "password": "password123"})
    token = resp.json()["access_token"]
    return f"Bearer {token}"


@pytest.mark.asyncio
async def test_start_preparation_requires_pro_tier(client, session_override):
    """Test that preparation requires Pro/Premium tier."""
    # Register as Free tier user
    token = await register_and_login_free(client, email="free@example.com")

    # Create a question
    question = Question(
        content="Tell me about a time you handled a conflict",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    # Try to start preparation
    response = await client.post(
        "/api/v1/preparation/start",
        headers={"Authorization": token},
        json={"question_id": str(question.id)},
    )

    assert response.status_code == 402  # Payment Required
    assert "upgrade" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_preparation_success(client, session_override):
    """Test successful preparation start."""
    token = await register_and_login_pro(client, session_override, email="pro@example.com")

    # Create a question
    question = Question(
        content="Tell me about a challenging project",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    # Start preparation
    response = await client.post(
        "/api/v1/preparation/start",
        headers={"Authorization": token},
        json={"question_id": str(question.id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert "preparation_id" in data
    assert data["stage"] == "detective"


@pytest.mark.asyncio
async def test_get_detective_question(client, session_override):
    """Test getting detective question."""
    token = await register_and_login_pro(client, session_override, email="detective@example.com")

    # Create question and preparation
    question = Question(
        content="Describe a time you led a team",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    # Get user ID
    from app.models.user import User
    result = await session_override.exec(select(User).where(User.email == "detective@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DETECTIVE,
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Get detective question
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/detective/question",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert data["order"] == 1
    assert isinstance(data["is_complete"], bool)


@pytest.mark.asyncio
async def test_submit_detective_answer(client, session_override):
    """Test submitting detective answer."""
    token = await register_and_login_pro(client, session_override, email="answer@example.com")

    # Create question and preparation
    question = Question(
        content="Tell me about yourself",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User
    result = await session_override.exec(select(User).where(User.email == "answer@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DETECTIVE,
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Create a question first
    qna = PreparationQnA(
        preparation_id=preparation.id,
        question="What project did you work on?",
        answer="",
        order=1,
    )
    session_override.add(qna)
    await session_override.commit()

    # Submit answer
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/detective/answer",
        headers={"Authorization": token},
        json={"answer": "I worked on a microservices migration project"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "stage" in data
    assert isinstance(data["is_complete"], bool)


@pytest.mark.asyncio
async def test_generate_draft(client, session_override):
    """Test generating draft answer."""
    token = await register_and_login_pro(client, session_override, email="draft@example.com")

    # Create question and preparation with Q&A
    question = Question(
        content="Tell me about a time you solved a difficult problem",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User
    result = await session_override.exec(select(User).where(User.email == "draft@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DRAFT,
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Add some Q&A
    qna1 = PreparationQnA(
        preparation_id=preparation.id,
        question="What was the problem?",
        answer="System was crashing under load",
        order=1,
    )
    qna2 = PreparationQnA(
        preparation_id=preparation.id,
        question="How did you solve it?",
        answer="Implemented caching and load balancing",
        order=2,
    )
    session_override.add(qna1)
    session_override.add(qna2)
    await session_override.commit()

    # Generate draft
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/generate-draft",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "draft_answer" in data
    assert len(data["draft_answer"]) > 0
    assert data["stage"] == "practice"


@pytest.mark.asyncio
async def test_get_draft(client, session_override):
    """Test getting draft answer."""
    token = await register_and_login_pro(client, session_override, email="getdraft@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User
    result = await session_override.exec(select(User).where(User.email == "getdraft@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="**Situation**: Test situation\n**Task**: Test task\n**Action**: Test action\n**Result**: Test result",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Get draft
    response = await client.get(
        f"/api/v1/preparation/{preparation.id}/draft",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["draft_answer"] == preparation.draft_answer
    assert "STAR" in data["draft_answer"] or "Situation" in data["draft_answer"]


# Practice Endpoints Tests


@pytest.mark.asyncio
async def test_start_practice_success(client, session_override):
    """Test starting a practice session."""
    token = await register_and_login_pro(client, session_override, email="practice@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question for practice",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(select(User).where(User.email == "practice@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft answer for practice",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Start practice
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/practice/start",
        headers={"Authorization": token},
    )

    assert response.status_code == 201
    data = response.json()
    assert "attempt_id" in data
    assert data["stage"] == "practice"

    # Verify attempt was created
    attempt_result = await session_override.exec(
        select(DeliveryAttempt).where(DeliveryAttempt.preparation_id == preparation.id)
    )
    attempt = attempt_result.first()
    assert attempt is not None
    assert attempt.id == UUID(data["attempt_id"])


@pytest.mark.asyncio
async def test_start_practice_requires_draft(client, session_override):
    """Test that starting practice requires a draft."""
    token = await register_and_login_pro(client, session_override, email="nodraft@example.com")

    # Create question and preparation without draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(select(User).where(User.email == "nodraft@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DRAFT,
        draft_answer=None,  # No draft
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Try to start practice
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/practice/start",
        headers={"Authorization": token},
    )

    assert response.status_code == 400
    assert "draft" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_practice_requires_pro_tier(client, session_override):
    """Test that practice requires Pro/Premium tier."""
    token = await register_and_login_free(client, email="freepractice@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(
        select(User).where(User.email == "freepractice@example.com")
    )
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Try to start practice
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/practice/start",
        headers={"Authorization": token},
    )

    assert response.status_code == 402  # Payment Required


@pytest.mark.asyncio
async def test_submit_practice_success(client, session_override):
    """Test submitting a practice attempt with audio."""
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock, patch

    token = await register_and_login_pro(client, session_override, email="submit@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(select(User).where(User.email == "submit@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft answer",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Create a practice attempt
    attempt = DeliveryAttempt(
        preparation_id=preparation.id,
    )
    session_override.add(attempt)
    await session_override.commit()
    await session_override.refresh(attempt)

    # Create a mock audio file
    audio_dir = Path("uploads/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_file = audio_dir / "test_audio.webm"
    audio_file.write_bytes(b"fake audio data")
    audio_url = f"/uploads/audio/{audio_file.name}"

    # Mock transcription
    with patch("app.api.preparation.Transcriber") as MockTranscriber:
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe = AsyncMock(
            return_value=MagicMock(text="This is a test transcript of my practice delivery.")
        )
        MockTranscriber.return_value = mock_transcriber

        # Submit practice
        response = await client.post(
            f"/api/v1/preparation/{preparation.id}/practice/submit",
            headers={"Authorization": token},
            json={"audio_url": audio_url},
        )

        assert response.status_code == 200
        data = response.json()
        assert "attempt_id" in data
        assert "transcript" in data
        assert data["transcript"] == "This is a test transcript of my practice delivery."
        assert data["stage"] == "practice"

        # Verify attempt was updated
        await session_override.refresh(attempt)
        assert attempt.audio_url == audio_url
        assert attempt.transcript == "This is a test transcript of my practice delivery."

    # Cleanup
    audio_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_submit_practice_creates_attempt_if_missing(client, session_override):
    """Test that submit creates an attempt if none exists."""
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock, patch

    token = await register_and_login_pro(client, session_override, email="autoattempt@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(
        select(User).where(User.email == "autoattempt@example.com")
    )
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Create mock audio file
    audio_dir = Path("uploads/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_file = audio_dir / "test_auto.webm"
    audio_file.write_bytes(b"fake audio")
    audio_url = f"/uploads/audio/{audio_file.name}"

    # Mock transcription
    with patch("app.api.preparation.Transcriber") as MockTranscriber:
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe = AsyncMock(
            return_value=MagicMock(text="Auto created attempt transcript.")
        )
        MockTranscriber.return_value = mock_transcriber

        # Submit without creating attempt first
        response = await client.post(
            f"/api/v1/preparation/{preparation.id}/practice/submit",
            headers={"Authorization": token},
            json={"audio_url": audio_url},
        )

        assert response.status_code == 200
        data = response.json()
        assert "attempt_id" in data

        # Verify attempt was created
        attempt_result = await session_override.exec(
            select(DeliveryAttempt).where(DeliveryAttempt.preparation_id == preparation.id)
        )
        attempt = attempt_result.first()
        assert attempt is not None
        assert attempt.audio_url == audio_url
        assert attempt.transcript == "Auto created attempt transcript."

    # Cleanup
    audio_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_submit_practice_audio_not_found(client, session_override):
    """Test that submitting with invalid audio URL returns error."""
    token = await register_and_login_pro(client, session_override, email="invalidaudio@example.com")

    # Create question and preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(
        select(User).where(User.email == "invalidaudio@example.com")
    )
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Try to submit with non-existent audio URL
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/practice/submit",
        headers={"Authorization": token},
        json={"audio_url": "/uploads/audio/nonexistent.webm"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_attempts_success(client, session_override):
    """Test getting all delivery attempts for a preparation."""
    token = await register_and_login_pro(client, session_override, email="attempts@example.com")

    # Create question and preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(select(User).where(User.email == "attempts@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Create multiple attempts
    attempt1 = DeliveryAttempt(
        preparation_id=preparation.id,
        audio_url="/uploads/audio/attempt1.webm",
        transcript="First practice attempt",
    )
    attempt2 = DeliveryAttempt(
        preparation_id=preparation.id,
        audio_url="/uploads/audio/attempt2.webm",
        transcript="Second practice attempt",
    )
    session_override.add(attempt1)
    session_override.add(attempt2)
    await session_override.commit()

    # Get attempts
    response = await client.get(
        f"/api/v1/preparation/{preparation.id}/attempts",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "attempts" in data
    assert len(data["attempts"]) == 2
    # Should be ordered newest first
    assert data["attempts"][0]["transcript"] == "Second practice attempt"
    assert data["attempts"][1]["transcript"] == "First practice attempt"


@pytest.mark.asyncio
async def test_get_attempts_empty(client, session_override):
    """Test getting attempts when none exist."""
    token = await register_and_login_pro(client, session_override, email="noattempts@example.com")

    # Create question and preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(
        select(User).where(User.email == "noattempts@example.com")
    )
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # Get attempts
    response = await client.get(
        f"/api/v1/preparation/{preparation.id}/attempts",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "attempts" in data
    assert len(data["attempts"]) == 0


@pytest.mark.asyncio
async def test_get_attempts_unauthorized(client, session_override):
    """Test that users cannot access other users' attempts."""
    token1 = await register_and_login_pro(client, session_override, email="user1@example.com")
    token2 = await register_and_login_pro(client, session_override, email="user2@example.com")

    # User 1 creates preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    from app.models.user import User

    result = await session_override.exec(select(User).where(User.email == "user1@example.com"))
    user1 = result.first()

    preparation = AnswerPreparation(
        user_id=user1.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    session_override.add(preparation)
    await session_override.commit()
    await session_override.refresh(preparation)

    # User 2 tries to access User 1's attempts
    response = await client.get(
        f"/api/v1/preparation/{preparation.id}/attempts",
        headers={"Authorization": token2},
    )

    assert response.status_code == 404
