"""Tests for answer preparation endpoints."""

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.models.preparation import (
    AnswerPreparation,
    DeliveryAttempt,
    PreparationQnA,
    PreparationStage,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import SubscriptionTier, User


# Helper functions (not fixtures) for creating test users with dynamic emails
async def register_and_login_pro(
    client: AsyncClient, db_session, email: str = "user@example.com"
) -> str:
    """Register Pro tier user and return bearer token."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "SecureTest123!"})
    resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": "SecureTest123!"}
    )
    token = resp.json()["access_token"]

    # Upgrade to Pro tier for preparation access
    result = await db_session.exec(select(User).where(User.email == email))
    user = result.first()
    if user:
        user.subscription_tier = SubscriptionTier.PRO
        await db_session.commit()

    return f"Bearer {token}"


async def register_and_login_free(client: AsyncClient, email: str = "user@example.com") -> str:
    """Register Free tier user and return bearer token."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "SecureTest123!"})
    resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": "SecureTest123!"}
    )
    token = resp.json()["access_token"]
    return f"Bearer {token}"


@pytest.mark.asyncio
async def test_start_preparation_requires_pro_tier(client, db_session):
    """Test that preparation requires Pro/Premium tier."""
    # Register as Free tier user
    token = await register_and_login_free(client, email="free@example.com")

    # Create a question
    question = Question(
        content="Tell me about a time you handled a conflict",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Try to start preparation
    response = await client.post(
        "/api/v1/preparation/start",
        headers={"Authorization": token},
        json={"question_id": str(question.id)},
    )

    assert response.status_code == 402  # Payment Required
    assert "upgrade" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_preparations(client, db_session):
    """Test listing user's preparations."""
    token = await register_and_login_pro(client, db_session, email="list@example.com")

    # Create a question
    question = Question(
        content="Test question for listing",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create a preparation
    result = await db_session.exec(select(User).where(User.email == "list@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DRAFT,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # List preparations
    response = await client.get(
        "/api/v1/preparation",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "preparations" in data
    assert len(data["preparations"]) == 1
    assert data["preparations"][0]["id"] == str(preparation.id)
    assert data["preparations"][0]["question_content"] == "Test question for listing"


@pytest.mark.asyncio
async def test_start_preparation_success(client, db_session):
    """Test successful preparation start."""
    token = await register_and_login_pro(client, db_session, email="pro@example.com")

    # Create a question
    question = Question(
        content="Tell me about a challenging project",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

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
async def test_get_detective_question(client, db_session):
    """Test getting detective question."""
    token = await register_and_login_pro(client, db_session, email="detective@example.com")

    # Create question and preparation
    question = Question(
        content="Describe a time you led a team",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Get user ID
    result = await db_session.exec(select(User).where(User.email == "detective@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DETECTIVE,
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

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
async def test_submit_detective_answer(client, db_session):
    """Test submitting detective answer."""
    token = await register_and_login_pro(client, db_session, email="answer@example.com")

    # Create question and preparation
    question = Question(
        content="Tell me about yourself",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "answer@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DETECTIVE,
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Create a question first
    qna = PreparationQnA(
        preparation_id=preparation.id,
        question="What project did you work on?",
        answer="",
        order=1,
    )
    db_session.add(qna)
    await db_session.commit()

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
async def test_generate_draft(client, db_session):
    """Test generating draft answer."""
    token = await register_and_login_pro(client, db_session, email="draft@example.com")

    # Create question and preparation with Q&A
    question = Question(
        content="Tell me about a time you solved a difficult problem",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "draft@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DRAFT,
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

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
    db_session.add(qna1)
    db_session.add(qna2)
    await db_session.commit()

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
async def test_get_draft(client, db_session):
    """Test getting draft answer."""
    token = await register_and_login_pro(client, db_session, email="getdraft@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "getdraft@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="**Situation**: Test situation\n**Task**: Test task\n**Action**: Test action\n**Result**: Test result",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

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
async def test_start_practice_success(client, db_session):
    """Test starting a practice session."""
    token = await register_and_login_pro(client, db_session, email="practice@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question for practice",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "practice@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft answer for practice",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

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
    attempt_result = await db_session.exec(
        select(DeliveryAttempt).where(DeliveryAttempt.preparation_id == preparation.id)
    )
    attempt = attempt_result.first()
    assert attempt is not None
    assert attempt.id == UUID(data["attempt_id"])


@pytest.mark.asyncio
async def test_start_practice_requires_draft(client, db_session):
    """Test that starting practice requires a draft."""
    token = await register_and_login_pro(client, db_session, email="nodraft@example.com")

    # Create question and preparation without draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "nodraft@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.DRAFT,
        draft_answer=None,  # No draft
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Try to start practice
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/practice/start",
        headers={"Authorization": token},
    )

    assert response.status_code == 400
    assert "draft" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_practice_requires_pro_tier(client, db_session):
    """Test that practice requires Pro/Premium tier."""
    token = await register_and_login_free(client, email="freepractice@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "freepractice@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Try to start practice
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/practice/start",
        headers={"Authorization": token},
    )

    assert response.status_code == 402  # Payment Required


@pytest.mark.asyncio
async def test_submit_practice_success(client, db_session):
    """Test submitting a practice attempt with audio."""
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock, patch

    token = await register_and_login_pro(client, db_session, email="submit@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "submit@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft answer",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Create a practice attempt
    attempt = DeliveryAttempt(
        preparation_id=preparation.id,
    )
    db_session.add(attempt)
    await db_session.commit()
    await db_session.refresh(attempt)

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
        await db_session.refresh(attempt)
        assert attempt.audio_url == audio_url
        assert attempt.transcript == "This is a test transcript of my practice delivery."

    # Cleanup
    audio_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_submit_practice_creates_attempt_if_missing(client, db_session):
    """Test that submit creates an attempt if none exists."""
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock, patch

    token = await register_and_login_pro(client, db_session, email="autoattempt@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "autoattempt@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

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
        attempt_result = await db_session.exec(
            select(DeliveryAttempt).where(DeliveryAttempt.preparation_id == preparation.id)
        )
        attempt = attempt_result.first()
        assert attempt is not None
        assert attempt.audio_url == audio_url
        assert attempt.transcript == "Auto created attempt transcript."

    # Cleanup
    audio_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_submit_practice_audio_not_found(client, db_session):
    """Test that submitting with invalid audio URL returns error."""
    token = await register_and_login_pro(client, db_session, email="invalidaudio@example.com")

    # Create question and preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "invalidaudio@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Try to submit with non-existent audio URL
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/practice/submit",
        headers={"Authorization": token},
        json={"audio_url": "/uploads/audio/nonexistent.webm"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_attempts_success(client, db_session):
    """Test getting all delivery attempts for a preparation."""
    token = await register_and_login_pro(client, db_session, email="attempts@example.com")

    # Create question and preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "attempts@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

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
    db_session.add(attempt1)
    db_session.add(attempt2)
    await db_session.commit()

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
async def test_get_attempts_empty(client, db_session):
    """Test getting attempts when none exist."""
    token = await register_and_login_pro(client, db_session, email="noattempts@example.com")

    # Create question and preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "noattempts@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

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
async def test_get_attempts_unauthorized(client, db_session):
    """Test that users cannot access other users' attempts."""
    await register_and_login_pro(client, db_session, email="user1@example.com")
    token2 = await register_and_login_pro(client, db_session, email="user2@example.com")

    # User 1 creates preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "user1@example.com"))
    user1 = result.first()

    preparation = AnswerPreparation(
        user_id=user1.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # User 2 tries to access User 1's attempts
    response = await client.get(
        f"/api/v1/preparation/{preparation.id}/attempts",
        headers={"Authorization": token2},
    )

    assert response.status_code == 404


# Rating Endpoints Tests


@pytest.mark.asyncio
async def test_rate_delivery_success(client, db_session):
    """Test rating a delivery attempt."""
    from unittest.mock import AsyncMock, MagicMock, patch

    token = await register_and_login_pro(client, db_session, email="rate@example.com")

    # Create question and preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "rate@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="**Situation**: Test situation\n**Task**: Test task\n**Action**: Test action\n**Result**: Test result",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Create attempt with transcript
    attempt = DeliveryAttempt(
        preparation_id=preparation.id,
        transcript="I faced a test situation. My task was to handle it. I took specific actions. The result was positive.",
    )
    db_session.add(attempt)
    await db_session.commit()
    await db_session.refresh(attempt)

    # Mock rating service
    with patch("app.api.preparation.DeliveryRatingService") as MockRatingService:
        mock_service = MagicMock()
        mock_rating = MagicMock()
        mock_rating.delivery_score = 85.0
        mock_rating.content_coverage = 90.0
        mock_rating.key_points = 85.0
        mock_rating.flow_structure = 80.0
        mock_rating.strengths = ["Clear delivery", "Good structure", "Engaging"]
        mock_rating.improvements = ["Add more details", "Include metrics", "Smoother transitions"]
        mock_rating.comparison_feedback = "Your delivery captured the key points well."
        mock_service.rate_delivery = AsyncMock(return_value=mock_rating)
        MockRatingService.return_value = mock_service

        # Rate delivery
        response = await client.post(
            f"/api/v1/preparation/{preparation.id}/rate-delivery",
            headers={"Authorization": token},
            json={"attempt_id": str(attempt.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert "delivery_score" in data
        assert data["delivery_score"] == 85.0
        assert data["content_coverage"] == 90.0
        assert len(data["strengths"]) == 3
        assert len(data["improvements"]) == 3
        assert data["stage"] == "complete"

        # Verify attempt was updated
        await db_session.refresh(attempt)
        assert attempt.delivery_score == 85.0
        assert attempt.comparison_feedback is not None


@pytest.mark.asyncio
async def test_rate_delivery_no_transcript(client, db_session):
    """Test that rating fails if attempt has no transcript."""
    token = await register_and_login_pro(client, db_session, email="notranscript@example.com")

    # Create preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "notranscript@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Create attempt without transcript
    attempt = DeliveryAttempt(
        preparation_id=preparation.id,
        transcript=None,
    )
    db_session.add(attempt)
    await db_session.commit()
    await db_session.refresh(attempt)

    # Try to rate
    response = await client.post(
        f"/api/v1/preparation/{preparation.id}/rate-delivery",
        headers={"Authorization": token},
        json={"attempt_id": str(attempt.id)},
    )

    assert response.status_code == 400
    assert "transcript" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_comparison_success(client, db_session):
    """Test getting comparison view."""
    token = await register_and_login_pro(client, db_session, email="comparison@example.com")

    # Create preparation with draft
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "comparison@example.com"))
    user = result.first()

    preparation = AnswerPreparation(
        user_id=user.id,
        question_id=question.id,
        stage=PreparationStage.COMPLETE,
        draft_answer="**Situation**: Planned situation\n**Task**: Planned task\n**Action**: Planned action\n**Result**: Planned result",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    # Create rated attempt
    attempt = DeliveryAttempt(
        preparation_id=preparation.id,
        transcript="I handled a situation. I had a task. I took actions. The result was good.",
        delivery_score=85.0,
        comparison_feedback="Good delivery covering main points.",
    )
    db_session.add(attempt)
    await db_session.commit()
    await db_session.refresh(attempt)

    # Get comparison
    response = await client.get(
        f"/api/v1/preparation/{preparation.id}/comparison?attempt_id={attempt.id}",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["draft"] == preparation.draft_answer
    assert data["delivery"] == attempt.transcript
    assert data["delivery_score"] == 85.0
    assert data["comparison_feedback"] == "Good delivery covering main points."


@pytest.mark.asyncio
async def test_get_comparison_unauthorized(client, db_session):
    """Test that users cannot access other users' comparisons."""
    await register_and_login_pro(client, db_session, email="user1comp@example.com")
    token2 = await register_and_login_pro(client, db_session, email="user2comp@example.com")

    # User 1 creates preparation
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    result = await db_session.exec(select(User).where(User.email == "user1comp@example.com"))
    user1 = result.first()

    preparation = AnswerPreparation(
        user_id=user1.id,
        question_id=question.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="Test draft",
    )
    db_session.add(preparation)
    await db_session.commit()
    await db_session.refresh(preparation)

    attempt = DeliveryAttempt(
        preparation_id=preparation.id,
        transcript="Test delivery",
    )
    db_session.add(attempt)
    await db_session.commit()
    await db_session.refresh(attempt)

    # User 2 tries to access User 1's comparison
    response = await client.get(
        f"/api/v1/preparation/{preparation.id}/comparison?attempt_id={attempt.id}",
        headers={"Authorization": token2},
    )

    assert response.status_code == 404
