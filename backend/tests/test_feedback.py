"""Tests for feedback generation service and API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel

from app.ai.content_analyzer import ContentMetrics
from app.db import SessionLocal, engine, get_session
from app.main import app
from app.models.feedback import ContentFeedback, SessionFeedback
from app.models.interview import (
    InterviewQuestion,
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    InterviewType,
    ProcessingStatus,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.services.feedback_service import FeedbackService


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


@pytest.fixture
def mock_content_metrics():
    """Mock ContentMetrics for testing."""
    return ContentMetrics(
        technical_accuracy=85.0,
        star_adherence=75.0,
        answer_structure=80.0,
        completeness=90.0,
        relevance=88.0,
        strengths=["Clear communication", "Good examples", "Structured response"],
        improvements=["Add more technical details", "Include metrics", "Expand on results"],
        detailed_feedback="Overall strong answer with good structure. Consider adding more specific technical details and quantifiable results.",
    )


# FeedbackService Unit Tests


@pytest.mark.asyncio
async def test_generate_feedback_success(session_override, mock_content_metrics):
    """Test successful feedback generation for a response."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first to satisfy foreign key constraint
    user = User(email="test@example.com", hashed_password=hash_password("password"))
    session_override.add(user)
    await session_override.commit()
    await session_override.refresh(user)

    # Create test data
    question = Question(
        content="Tell me about a time you solved a technical problem",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    session_override.add(interview)
    await session_override.commit()
    await session_override.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="I faced a challenging bug in production. I analyzed logs, identified the root cause, and implemented a fix that resolved the issue.",
        duration_seconds=120,
    )
    session_override.add(response)
    await session_override.commit()
    await session_override.refresh(response)

    # Mock the content analyzer
    with patch.object(
        FeedbackService, "__init__", lambda self: setattr(self, "content_analyzer", MagicMock())
    ):
        service = FeedbackService()
        service.content_analyzer.analyze = AsyncMock(return_value=mock_content_metrics)
        service.content_analyzer.calculate_overall_score = MagicMock(return_value=82.5)

        # Generate feedback
        feedback = await service.generate_feedback(session_override, response.id)

        # Assertions
        assert feedback is not None
        assert feedback.response_id == response.id
        assert feedback.technical_accuracy == 85.0
        assert feedback.star_adherence == 75.0
        assert feedback.answer_structure == 80.0
        assert feedback.completeness == 90.0
        assert feedback.relevance == 88.0
        assert feedback.overall_content_score == 82.5
        assert len(feedback.strengths) == 3
        assert len(feedback.improvements) == 3
        assert "strong answer" in feedback.detailed_feedback.lower()


@pytest.mark.asyncio
async def test_generate_feedback_no_transcript(session_override):
    """Test feedback generation fails when response has no transcript."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test2@example.com", hashed_password=hash_password("password"))
    session_override.add(user)
    await session_override.commit()
    await session_override.refresh(user)

    question = Question(
        content="What is polymorphism?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    session_override.add(interview)
    await session_override.commit()
    await session_override.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript=None,  # No transcript
        duration_seconds=60,
    )
    session_override.add(response)
    await session_override.commit()
    await session_override.refresh(response)

    service = FeedbackService()

    with pytest.raises(ValueError, match="no transcript"):
        await service.generate_feedback(session_override, response.id)


@pytest.mark.asyncio
async def test_generate_feedback_already_exists(session_override, mock_content_metrics):
    """Test feedback generation fails when feedback already exists."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test3@example.com", hashed_password=hash_password("password"))
    session_override.add(user)
    await session_override.commit()
    await session_override.refresh(user)

    question = Question(
        content="Design a URL shortener",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        status=InterviewStatus.IN_PROGRESS,
    )
    session_override.add(interview)
    await session_override.commit()
    await session_override.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="I would use consistent hashing and a distributed key-value store...",
        duration_seconds=300,
    )
    session_override.add(response)
    await session_override.commit()
    await session_override.refresh(response)

    # Create existing feedback
    existing_feedback = ContentFeedback(
        response_id=response.id,
        technical_accuracy=80.0,
        star_adherence=0.0,
        answer_structure=75.0,
        completeness=85.0,
        relevance=90.0,
        overall_content_score=82.0,
        strengths=["Good architecture"],
        improvements=["Add scalability discussion"],
        detailed_feedback="Solid design",
    )
    session_override.add(existing_feedback)
    await session_override.commit()

    service = FeedbackService()

    with pytest.raises(ValueError, match="already exists"):
        await service.generate_feedback(session_override, response.id)


@pytest.mark.asyncio
async def test_generate_session_feedback_success(session_override, mock_content_metrics):
    """Test successful session feedback generation."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test4@example.com", hashed_password=hash_password("password"))
    session_override.add(user)
    await session_override.commit()
    await session_override.refresh(user)

    question = Question(
        content="Tell me about your leadership experience",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    session_override.add(interview)
    await session_override.commit()
    await session_override.refresh(interview)

    # Create responses with transcripts
    response1 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="I led a team of 5 engineers to deliver a critical project on time.",
        duration_seconds=120,
    )
    response2 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Another example of my leadership was when I mentored junior developers.",
        duration_seconds=90,
    )
    session_override.add(response1)
    session_override.add(response2)
    await session_override.commit()
    await session_override.refresh(response1)
    await session_override.refresh(response2)

    # Mock the content analyzer
    with patch.object(
        FeedbackService, "__init__", lambda self: setattr(self, "content_analyzer", MagicMock())
    ):
        service = FeedbackService()
        service.content_analyzer.analyze = AsyncMock(return_value=mock_content_metrics)
        service.content_analyzer.calculate_overall_score = MagicMock(return_value=82.5)

        # Generate session feedback
        session_feedback = await service.generate_session_feedback(session_override, interview.id)

        # Assertions
        assert session_feedback is not None
        assert session_feedback.session_id == interview.id
        assert session_feedback.content_score > 0
        assert session_feedback.overall_score > 0
        assert len(session_feedback.top_strengths) > 0
        assert len(session_feedback.top_improvements) > 0

        # Check interview status updated
        await session_override.refresh(interview)
        assert interview.status == InterviewStatus.ANALYZED
        assert interview.overall_score is not None


@pytest.mark.asyncio
async def test_generate_session_feedback_no_responses(session_override):
    """Test session feedback generation fails when no responses exist."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test5@example.com", hashed_password=hash_password("password"))
    session_override.add(user)
    await session_override.commit()
    await session_override.refresh(user)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.COMPLETED,
    )
    session_override.add(interview)
    await session_override.commit()
    await session_override.refresh(interview)

    service = FeedbackService()

    with pytest.raises(ValueError, match="No responses found"):
        await service.generate_session_feedback(session_override, interview.id)


# API Endpoint Tests


@pytest.mark.asyncio
async def test_get_response_feedback_endpoint(client, session_override, mock_content_metrics):
    """Test GET /api/v1/feedback/response/{response_id} endpoint."""
    token = await register_and_login(client, email="feedback@example.com")

    # Create test data
    question = Question(
        content="What is dependency injection?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Link question to interview
    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    # Start interview and submit response
    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    response_data = {
        "question_id": str(question.id),
        "transcript": "Dependency injection is a design pattern where dependencies are provided to a class rather than the class creating them.",
        "duration_seconds": 60,
    }
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json=response_data,
        headers={"Authorization": token},
    )
    response_id = submit_resp.json()["id"]

    # Create feedback manually for testing
    feedback = ContentFeedback(
        response_id=response_id,
        technical_accuracy=90.0,
        star_adherence=0.0,
        answer_structure=85.0,
        completeness=88.0,
        relevance=92.0,
        overall_content_score=88.5,
        strengths=["Clear definition", "Accurate explanation"],
        improvements=["Add examples", "Discuss benefits"],
        detailed_feedback="Strong technical answer with clear explanation.",
    )
    session_override.add(feedback)
    await session_override.commit()

    # Test endpoint
    get_resp = await client.get(
        f"/api/v1/feedback/response/{response_id}",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["technical_accuracy"] == 90.0
    assert data["overall_content_score"] == 88.5
    assert len(data["strengths"]) == 2
    assert len(data["improvements"]) == 2


@pytest.mark.asyncio
async def test_get_response_feedback_not_found(client, session_override):
    """Test GET /api/v1/feedback/response/{response_id} returns 404 when no feedback exists."""
    token = await register_and_login(client, email="nofeedback@example.com")

    question = Question(
        content="Test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    response_id = submit_resp.json()["id"]

    # No feedback created yet
    get_resp = await client.get(
        f"/api/v1/feedback/response/{response_id}",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 404
    assert "not yet generated" in get_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_session_feedback_endpoint(client, session_override):
    """Test GET /api/v1/feedback/session/{session_id} endpoint."""
    token = await register_and_login(client, email="sessionfeedback@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Create session feedback manually
    session_feedback = SessionFeedback(
        session_id=interview_id,
        overall_score=85.0,
        audio_score=0.0,
        content_score=85.0,
        top_strengths=["Strong communication", "Good examples"],
        top_improvements=["Add more detail", "Include metrics"],
        recommended_practice_areas=["Technical depth"],
        next_question_ids=[],
    )
    session_override.add(session_feedback)
    await session_override.commit()

    # Test endpoint
    get_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["overall_score"] == 85.0
    assert data["content_score"] == 85.0
    assert len(data["top_strengths"]) == 2
    assert len(data["top_improvements"]) == 2


@pytest.mark.asyncio
async def test_generate_response_feedback_endpoint(client, session_override, mock_content_metrics):
    """Test POST /api/v1/feedback/generate/response/{response_id} endpoint."""
    token = await register_and_login(client, email="generate@example.com")

    question = Question(
        content="Explain REST API principles",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "REST stands for Representational State Transfer. It uses HTTP methods and is stateless.",
            "duration_seconds": 45,
        },
        headers={"Authorization": token},
    )
    response_id = submit_resp.json()["id"]

    # Mock the content analyzer
    with patch("app.services.feedback_service.ContentAnalyzer") as mock_analyzer_class:
        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(return_value=mock_content_metrics)
        mock_analyzer.calculate_overall_score = MagicMock(return_value=85.0)
        mock_analyzer_class.return_value = mock_analyzer

        # Generate feedback via API
        gen_resp = await client.post(
            f"/api/v1/feedback/generate/response/{response_id}",
            headers={"Authorization": token},
        )
        assert gen_resp.status_code == 201
        data = gen_resp.json()
        assert data["technical_accuracy"] == 85.0
        assert data["overall_content_score"] == 85.0


@pytest.mark.asyncio
async def test_feedback_authorization(client, session_override):
    """Test that users can only access their own feedback."""
    # User 1
    token1 = await register_and_login(client, email="user1@example.com")

    question = Question(
        content="Authorization test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token1},
    )
    interview_id = interview_resp.json()["id"]

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

    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token1},
    )
    response_id = submit_resp.json()["id"]

    # User 2 tries to access User 1's feedback
    token2 = await register_and_login(client, email="user2@example.com")
    get_resp = await client.get(
        f"/api/v1/feedback/response/{response_id}",
        headers={"Authorization": token2},
    )
    assert get_resp.status_code == 404  # Not found (unauthorized)


@pytest.mark.asyncio
async def test_get_session_processing_status_returns_counts_and_flags(client, session_override):
    """Test that processing status endpoint returns counts and flags."""
    token = await register_and_login(client, email="status@example.com")

    question = Question(
        content="Test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Create responses with different processing statuses
    response1 = InterviewResponse(
        session_id=interview_id,
        question_id=question.id,
        transcript="Test answer 1",
        duration_seconds=30,
        processing_status=ProcessingStatus.COMPLETED,
    )
    response2 = InterviewResponse(
        session_id=interview_id,
        question_id=question.id,
        transcript="Test answer 2",
        duration_seconds=30,
        processing_status=ProcessingStatus.TRANSCRIBING,
    )
    session_override.add(response1)
    session_override.add(response2)
    await session_override.commit()

    # Get processing status
    status_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/status",
        headers={"Authorization": token},
    )

    assert status_resp.status_code == 200
    data = status_resp.json()
    assert "status_counts" in data
    assert "total_responses" in data
    assert "has_session_feedback" in data
    assert "all_processed" in data
    assert "current_step" in data
    assert data["status_counts"]["completed"] == 1
    assert data["status_counts"]["transcribing"] == 1
    assert data["total_responses"] == 2
    assert data["all_processed"] is False


@pytest.mark.asyncio
async def test_get_session_processing_status_authorization(client, session_override):
    """Test that users cannot see another user's session status."""
    token1 = await register_and_login(client, email="user1_status@example.com")

    question = Question(
        content="Test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token1},
    )
    interview_id = interview_resp.json()["id"]

    # User 2 tries to access User 1's session status
    token2 = await register_and_login(client, email="user2_status@example.com")
    status_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/status",
        headers={"Authorization": token2},
    )
    assert status_resp.status_code == 404  # Not found (unauthorized)


@pytest.mark.asyncio
async def test_get_session_processing_status_handles_no_responses(client, session_override):
    """Test that processing status returns sensible defaults when no responses exist."""
    token = await register_and_login(client, email="no_responses@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Get processing status for session with no responses
    status_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/status",
        headers={"Authorization": token},
    )

    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["total_responses"] == 0
    assert data["all_processed"] is False
    assert data["has_session_feedback"] is False
    assert data["current_step"] == "idle"


# Additional API Endpoint Tests for Coverage


@pytest.mark.asyncio
async def test_get_session_feedback_not_found(client, session_override):
    """Test GET /api/v1/feedback/session/{session_id} returns 404 when no feedback exists."""
    token = await register_and_login(client, email="session_no_feedback@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # No session feedback created yet
    get_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 404
    assert "not yet generated" in get_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_all_session_feedbacks_endpoint(client, session_override):
    """Test GET /api/v1/feedback/session/{session_id}/all endpoint."""
    token = await register_and_login(client, email="all_feedbacks@example.com")

    question = Question(
        content="Test question for all feedbacks",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Submit response
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    response_id = submit_resp.json()["id"]

    # Create feedback for the response
    feedback = ContentFeedback(
        response_id=response_id,
        technical_accuracy=85.0,
        star_adherence=0.0,
        answer_structure=80.0,
        completeness=82.0,
        relevance=88.0,
        overall_content_score=83.0,
        strengths=["Good clarity"],
        improvements=["Add more detail"],
        detailed_feedback="Solid answer.",
    )
    session_override.add(feedback)
    await session_override.commit()

    # Get all feedbacks
    get_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/all",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["technical_accuracy"] == 85.0


@pytest.mark.asyncio
async def test_get_all_session_feedbacks_empty(client, session_override):
    """Test GET /api/v1/feedback/session/{session_id}/all returns empty list when no feedbacks."""
    token = await register_and_login(client, email="empty_feedbacks@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Get all feedbacks (should be empty)
    get_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/all",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_session_comparison_endpoint(client, session_override):
    """Test GET /api/v1/feedback/session/{session_id}/comparison endpoint."""
    token = await register_and_login(client, email="comparison@example.com")

    # Create first interview with feedback (for baseline)
    interview_resp1 = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id1 = interview_resp1.json()["id"]

    # Manually set the interview status and overall_score for baseline
    from sqlmodel import select
    result = await session_override.exec(
        select(InterviewSession).where(InterviewSession.id == interview_id1)
    )
    interview1 = result.first()
    interview1.status = InterviewStatus.ANALYZED
    interview1.overall_score = 75.0
    await session_override.commit()

    # Create second interview (the one we'll compare)
    interview_resp2 = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id2 = interview_resp2.json()["id"]

    # Create session feedback for the second interview
    session_feedback = SessionFeedback(
        session_id=interview_id2,
        overall_score=85.0,
        audio_score=0.0,
        content_score=85.0,
        top_strengths=["Great communication"],
        top_improvements=["Add metrics"],
        recommended_practice_areas=["Technical depth"],
        next_question_ids=[],
    )
    session_override.add(session_feedback)
    await session_override.commit()

    # Get comparison
    comp_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id2}/comparison",
        headers={"Authorization": token},
    )
    assert comp_resp.status_code == 200
    data = comp_resp.json()
    assert data["session_score"] == 85.0
    assert data["average_score"] == 75.0
    assert data["improvement_percent"] is not None
    assert data["sessions_compared"] == 1


@pytest.mark.asyncio
async def test_get_session_comparison_no_feedback(client, session_override):
    """Test GET /api/v1/feedback/session/{session_id}/comparison returns 404 when no feedback."""
    token = await register_and_login(client, email="no_comparison@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # No session feedback - should get 404
    comp_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/comparison",
        headers={"Authorization": token},
    )
    assert comp_resp.status_code == 404
    assert "not yet generated" in comp_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_session_comparison_no_previous_sessions(client, session_override):
    """Test comparison when user has no previous sessions for baseline."""
    token = await register_and_login(client, email="first_session@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Create session feedback
    session_feedback = SessionFeedback(
        session_id=interview_id,
        overall_score=80.0,
        audio_score=0.0,
        content_score=80.0,
        top_strengths=["Good"],
        top_improvements=["Better"],
        recommended_practice_areas=["Technical"],
        next_question_ids=[],
    )
    session_override.add(session_feedback)
    await session_override.commit()

    # Get comparison (no previous sessions)
    comp_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/comparison",
        headers={"Authorization": token},
    )
    assert comp_resp.status_code == 200
    data = comp_resp.json()
    assert data["session_score"] == 80.0
    assert data["average_score"] is None
    assert data["improvement_percent"] is None
    assert data["sessions_compared"] == 0


@pytest.mark.asyncio
async def test_generate_session_feedback_endpoint(client, session_override, mock_content_metrics):
    """Test POST /api/v1/feedback/generate/session/{session_id} endpoint."""
    token = await register_and_login(client, email="gen_session@example.com")

    question = Question(
        content="Test session feedback generation",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Submit response
    await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "I led a team of engineers to deliver a critical project.",
            "duration_seconds": 60,
        },
        headers={"Authorization": token},
    )

    # Mock the content analyzer
    with patch("app.services.feedback_service.ContentAnalyzer") as mock_analyzer_class:
        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(return_value=mock_content_metrics)
        mock_analyzer.calculate_overall_score = MagicMock(return_value=82.5)
        mock_analyzer_class.return_value = mock_analyzer

        # Generate session feedback via API
        gen_resp = await client.post(
            f"/api/v1/feedback/generate/session/{interview_id}",
            headers={"Authorization": token},
        )
        assert gen_resp.status_code == 201
        data = gen_resp.json()
        assert data["overall_score"] > 0
        assert data["content_score"] > 0
        assert len(data["top_strengths"]) > 0


@pytest.mark.asyncio
async def test_generate_session_feedback_no_responses(client, session_override):
    """Test generate session feedback returns 400 when no responses exist."""
    token = await register_and_login(client, email="gen_no_resp@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Try to generate session feedback without any responses
    gen_resp = await client.post(
        f"/api/v1/feedback/generate/session/{interview_id}",
        headers={"Authorization": token},
    )
    assert gen_resp.status_code == 400
    assert "no responses" in gen_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_response_feedback_no_transcript(client, session_override):
    """Test generate response feedback returns 400 when no transcript exists."""
    token = await register_and_login(client, email="gen_no_trans@example.com")

    question = Question(
        content="Test no transcript",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Submit response without transcript
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    response_id = submit_resp.json()["id"]

    # Try to generate feedback without transcript
    gen_resp = await client.post(
        f"/api/v1/feedback/generate/response/{response_id}",
        headers={"Authorization": token},
    )
    assert gen_resp.status_code == 400
    assert "no transcript" in gen_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_session_feedback_unauthorized_access(client, session_override):
    """Test that users cannot access another user's session feedback."""
    token1 = await register_and_login(client, email="owner_session@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token1},
    )
    interview_id = interview_resp.json()["id"]

    # User 2 tries to access User 1's session feedback
    token2 = await register_and_login(client, email="other_user_session@example.com")

    get_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}",
        headers={"Authorization": token2},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_all_feedbacks_unauthorized_access(client, session_override):
    """Test that users cannot access another user's all feedbacks."""
    token1 = await register_and_login(client, email="owner_all@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token1},
    )
    interview_id = interview_resp.json()["id"]

    # User 2 tries to access User 1's all feedbacks
    token2 = await register_and_login(client, email="other_user_all@example.com")

    get_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/all",
        headers={"Authorization": token2},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_comparison_unauthorized_access(client, session_override):
    """Test that users cannot access another user's comparison."""
    token1 = await register_and_login(client, email="owner_comp@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token1},
    )
    interview_id = interview_resp.json()["id"]

    # User 2 tries to access User 1's comparison
    token2 = await register_and_login(client, email="other_user_comp@example.com")

    comp_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/comparison",
        headers={"Authorization": token2},
    )
    assert comp_resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_session_feedback_already_exists(client, session_override, mock_content_metrics):
    """Test generate session feedback when feedback already exists."""
    token = await register_and_login(client, email="gen_already@example.com")

    question = Question(
        content="Test duplicate feedback generation",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    session_override.add(question)
    await session_override.commit()
    await session_override.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews/",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    session_override.add(interview_question)
    await session_override.commit()

    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # Submit response
    await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "I successfully led a team project.",
            "duration_seconds": 60,
        },
        headers={"Authorization": token},
    )

    # Mock the content analyzer
    with patch("app.services.feedback_service.ContentAnalyzer") as mock_analyzer_class:
        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(return_value=mock_content_metrics)
        mock_analyzer.calculate_overall_score = MagicMock(return_value=82.5)
        mock_analyzer_class.return_value = mock_analyzer

        # Generate session feedback first time
        gen_resp1 = await client.post(
            f"/api/v1/feedback/generate/session/{interview_id}",
            headers={"Authorization": token},
        )
        assert gen_resp1.status_code == 201

        # Try to generate again (should fail or return existing)
        gen_resp2 = await client.post(
            f"/api/v1/feedback/generate/session/{interview_id}",
            headers={"Authorization": token},
        )
        # Service may return existing or raise error - check it handles gracefully
        assert gen_resp2.status_code in [200, 201, 400]


@pytest.mark.asyncio
async def test_generate_session_feedback_invalid_session(client, session_override):
    """Test generate session feedback with invalid session ID returns 404."""
    from uuid import uuid4

    token = await register_and_login(client, email="gen_invalid@example.com")

    # Use a non-existent session ID
    fake_session_id = uuid4()

    gen_resp = await client.post(
        f"/api/v1/feedback/generate/session/{fake_session_id}",
        headers={"Authorization": token},
    )
    assert gen_resp.status_code == 404
    assert "not found" in gen_resp.json()["detail"].lower()
