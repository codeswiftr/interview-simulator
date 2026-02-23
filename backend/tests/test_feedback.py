"""Tests for feedback generation service and API endpoints.

Uses shared fixtures from conftest.py for database setup and client.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.ai.content_analyzer import ContentMetrics
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

# Import register_and_login from conftest.py
from tests.conftest import register_and_login


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
async def test_generate_feedback_success(db_session, mock_content_metrics):
    """Test successful feedback generation for a response."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first to satisfy foreign key constraint
    user = User(email="test@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create test data
    question = Question(
        content="Tell me about a time you solved a technical problem",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="I faced a challenging bug in production. I analyzed logs, identified the root cause, and implemented a fix that resolved the issue.",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    # Mock the content analyzer (the only external dependency)
    with patch("app.services.feedback_service.ContentAnalyzer") as MockAnalyzer:
        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(return_value=mock_content_metrics)
        mock_analyzer.calculate_overall_score = MagicMock(return_value=82.5)
        MockAnalyzer.return_value = mock_analyzer

        service = FeedbackService()

        # Generate feedback
        feedback = await service.generate_feedback(db_session, response.id)

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
async def test_generate_feedback_no_transcript(db_session):
    """Test feedback generation fails when response has no transcript."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test2@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    question = Question(
        content="What is polymorphism?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript=None,  # No transcript
        duration_seconds=60,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    service = FeedbackService()

    with pytest.raises(ValueError, match="no transcript"):
        await service.generate_feedback(db_session, response.id)


@pytest.mark.asyncio
async def test_generate_feedback_already_exists(db_session, mock_content_metrics):
    """Test feedback generation fails when feedback already exists."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test3@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    question = Question(
        content="Design a URL shortener",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="I would use consistent hashing and a distributed key-value store...",
        duration_seconds=300,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

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
    db_session.add(existing_feedback)
    await db_session.commit()

    service = FeedbackService()

    with pytest.raises(ValueError, match="already exists"):
        await service.generate_feedback(db_session, response.id)


@pytest.mark.asyncio
async def test_generate_session_feedback_success(db_session, mock_content_metrics):
    """Test successful session feedback generation."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test4@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    question = Question(
        content="Tell me about your leadership experience",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

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
    db_session.add(response1)
    db_session.add(response2)
    await db_session.commit()
    await db_session.refresh(response1)
    await db_session.refresh(response2)

    # Mock the content analyzer (the only external dependency)
    with patch("app.services.feedback_service.ContentAnalyzer") as MockAnalyzer:
        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(return_value=mock_content_metrics)
        mock_analyzer.calculate_overall_score = MagicMock(return_value=82.5)
        MockAnalyzer.return_value = mock_analyzer

        service = FeedbackService()

        # Generate session feedback
        session_feedback = await service.generate_session_feedback(db_session, interview.id)

        # Assertions
        assert session_feedback is not None
        assert session_feedback.session_id == interview.id
        assert session_feedback.content_score > 0
        assert session_feedback.overall_score > 0
        assert len(session_feedback.top_strengths) > 0
        assert len(session_feedback.top_improvements) > 0

        # Check interview status updated
        await db_session.refresh(interview)
        assert interview.status == InterviewStatus.ANALYZED
        assert interview.overall_score is not None


@pytest.mark.asyncio
async def test_generate_session_feedback_no_responses(db_session):
    """Test session feedback generation fails when no responses exist."""
    from app.models.user import User
    from app.security import hash_password

    # Create user first
    user = User(email="test5@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    service = FeedbackService()

    with pytest.raises(ValueError, match="No responses found"):
        await service.generate_session_feedback(db_session, interview.id)


# API Endpoint Tests


@pytest.mark.asyncio
async def test_get_response_feedback_endpoint(client, db_session, mock_content_metrics):
    """Test GET /api/v1/feedback/response/{response_id} endpoint."""
    token = await register_and_login(client, email="feedback@example.com")

    # Create test data
    question = Question(
        content="What is dependency injection?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews",
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
    db_session.add(interview_question)
    await db_session.commit()

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
    db_session.add(feedback)
    await db_session.commit()

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
async def test_get_response_feedback_not_found(client, db_session):
    """Test GET /api/v1/feedback/response/{response_id} returns 404 when no feedback exists."""
    token = await register_and_login(client, email="nofeedback@example.com")

    # Create a technical question that can be assigned
    question = Question(
        content="Test technical question for feedback test",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    # Create interview with question_count=1
    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (this assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned questions
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200, f"Get questions failed: {questions_resp.json()}"
    questions = questions_resp.json()
    assert len(questions) > 0, "Interview should have assigned questions"
    question_id = questions[0]["id"]

    # Submit a response using the assigned question
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"
    response_id = submit_resp.json()["id"]

    # No feedback created yet
    get_resp = await client.get(
        f"/api/v1/feedback/response/{response_id}",
        headers={"Authorization": token},
    )
    assert get_resp.status_code == 404
    assert "not yet generated" in get_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_session_feedback_endpoint(client, db_session):
    """Test GET /api/v1/feedback/session/{session_id} endpoint."""
    token = await register_and_login(client, email="sessionfeedback@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
    db_session.add(session_feedback)
    await db_session.commit()

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
async def test_generate_response_feedback_endpoint(client, db_session, mock_content_metrics):
    """Test POST /api/v1/feedback/generate/response/{response_id} endpoint."""
    token = await register_and_login(client, email="generate@example.com")

    # Create a technical question that can be assigned
    question = Question(
        content="Explain REST API principles",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    # Create interview with question_count=1
    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    assert questions_resp.status_code == 200
    question_id = questions_resp.json()[0]["id"]

    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "transcript": "REST stands for Representational State Transfer. It uses HTTP methods and is stateless.",
            "duration_seconds": 45,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"
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
async def test_generate_response_feedback_ai_failure(client, db_session):
    """Test POST /feedback/generate/response/{id} returns 400 when analysis fails."""
    token = await register_and_login(client, email="ai_failure@example.com")

    # Create a system design question that can be assigned
    question = Question(
        content="Explain CAP theorem",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "system_design", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "transcript": "Some answer that will cause AI failure",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"
    response_id = submit_resp.json()["id"]

    # Patch FeedbackService.generate_feedback to simulate analysis failure
    with patch("app.api.feedback.FeedbackService") as MockService:
        instance = MockService.return_value
        instance.generate_feedback = AsyncMock(side_effect=ValueError("AI analysis failed"))

        gen_resp = await client.post(
            f"/api/v1/feedback/generate/response/{response_id}",
            headers={"Authorization": token},
        )

    assert gen_resp.status_code == 400
    assert (
        "failed" in gen_resp.json()["detail"].lower() or "ai" in gen_resp.json()["detail"].lower()
    )


@pytest.mark.asyncio
async def test_feedback_authorization(client, db_session):
    """Test that users can only access their own feedback."""
    # User 1
    token1 = await register_and_login(client, email="user1@example.com")

    # Create a question that can be assigned
    question = Question(
        content="Authorization test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical", "question_count": 1},
        headers={"Authorization": token1},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token1},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token1},
    )
    question_id = questions_resp.json()[0]["id"]

    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token1},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"
    response_id = submit_resp.json()["id"]

    # User 2 tries to access User 1's feedback
    token2 = await register_and_login(client, email="user2@example.com")
    get_resp = await client.get(
        f"/api/v1/feedback/response/{response_id}",
        headers={"Authorization": token2},
    )
    assert get_resp.status_code == 404  # Not found (unauthorized)

    # User 2 also cannot generate feedback for User 1's response
    gen_resp = await client.post(
        f"/api/v1/feedback/generate/response/{response_id}",
        headers={"Authorization": token2},
    )
    assert gen_resp.status_code == 404  # Not found (unauthorized)


@pytest.mark.asyncio
async def test_get_session_processing_status_returns_counts_and_flags(client, db_session):
    """Test that processing status endpoint returns counts and flags."""
    token = await register_and_login(client, email="status@example.com")

    question = Question(
        content="Test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    db_session.add(interview_question)
    await db_session.commit()

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
    db_session.add(response1)
    db_session.add(response2)
    await db_session.commit()

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
async def test_get_session_processing_status_authorization(client, db_session):
    """Test that users cannot see another user's session status."""
    token1 = await register_and_login(client, email="user1_status@example.com")

    question = Question(
        content="Test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_get_session_processing_status_handles_no_responses(client, db_session):
    """Test that processing status returns sensible defaults when no responses exist."""
    token = await register_and_login(client, email="no_responses@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_get_session_feedback_not_found(client, db_session):
    """Test GET /api/v1/feedback/session/{session_id} returns 404 when no feedback exists."""
    token = await register_and_login(client, email="session_no_feedback@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_get_all_session_feedbacks_endpoint(client, db_session):
    """Test GET /api/v1/feedback/session/{session_id}/all endpoint."""
    token = await register_and_login(client, email="all_feedbacks@example.com")

    # Create a question that can be assigned
    question = Question(
        content="Test question for all feedbacks",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # Submit response
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "transcript": "Test answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"
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
    db_session.add(feedback)
    await db_session.commit()

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
async def test_get_all_session_feedbacks_empty(client, db_session):
    """Test GET /api/v1/feedback/session/{session_id}/all returns empty list when no feedbacks."""
    token = await register_and_login(client, email="empty_feedbacks@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_get_session_processing_status_with_feedback(client, db_session):
    """Test GET /api/v1/feedback/session/{id}/status returns correct counts."""
    token = await register_and_login(client, email="status@example.com")

    # Create interview
    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Create question and link to interview
    question = Question(
        content="Status question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview_question = InterviewQuestion(
        session_id=interview_id,
        question_id=question.id,
        order=1,
    )
    db_session.add(interview_question)
    await db_session.commit()

    # Start interview and submit two responses
    await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )

    # First response fully processed
    resp1 = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "First answer",
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    r1_id = resp1.json()["id"]

    # Second response pending
    resp2 = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": str(question.id),
            "transcript": "Second answer",
            "duration_seconds": 40,
        },
        headers={"Authorization": token},
    )
    resp2.json()["id"]

    # Manually create feedback for first response and session
    content_fb = ContentFeedback(
        response_id=r1_id,
        technical_accuracy=80.0,
        star_adherence=0.0,
        answer_structure=75.0,
        completeness=70.0,
        relevance=82.0,
        overall_content_score=76.0,
        strengths=["Good content"],
        improvements=["More detail"],
        detailed_feedback="Good answer overall.",
    )
    session_fb = SessionFeedback(
        session_id=interview_id,
        overall_score=78.0,
        content_score=76.0,
        audio_score=80.0,
        top_strengths=["Clear communication"],
        top_improvements=["Add examples"],
        summary="Solid session.",
    )
    db_session.add(content_fb)
    db_session.add(session_fb)
    await db_session.commit()

    status_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/status",
        headers={"Authorization": token},
    )
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["total_responses"] == 2
    assert isinstance(data["status_counts"], dict)
    # Both responses should initially be pending
    assert data["status_counts"].get("pending", 0) == 2


@pytest.mark.asyncio
async def test_get_session_processing_status_empty(client, db_session):
    """Test status endpoint when there are no responses yet."""
    token = await register_and_login(client, email="status_empty@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical"},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    status_resp = await client.get(
        f"/api/v1/feedback/session/{interview_id}/status",
        headers={"Authorization": token},
    )
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["total_responses"] == 0
    assert isinstance(data["status_counts"], dict)


@pytest.mark.asyncio
async def test_get_session_comparison_endpoint(client, db_session):
    """Test GET /api/v1/feedback/session/{session_id}/comparison endpoint."""
    token = await register_and_login(client, email="comparison@example.com")

    # Create first interview with feedback (for baseline)
    interview_resp1 = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "behavioral"},
        headers={"Authorization": token},
    )
    interview_id1 = interview_resp1.json()["id"]

    # Manually set the interview status and overall_score for baseline
    from sqlmodel import select

    result = await db_session.exec(
        select(InterviewSession).where(InterviewSession.id == interview_id1)
    )
    interview1 = result.first()
    interview1.status = InterviewStatus.ANALYZED
    interview1.overall_score = 75.0
    await db_session.commit()

    # Create second interview (the one we'll compare)
    interview_resp2 = await client.post(
        "/api/v1/interviews",
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
    db_session.add(session_feedback)
    await db_session.commit()

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
async def test_get_session_comparison_no_feedback(client, db_session):
    """Test GET /api/v1/feedback/session/{session_id}/comparison returns 404 when no feedback."""
    token = await register_and_login(client, email="no_comparison@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_get_session_comparison_no_previous_sessions(client, db_session):
    """Test comparison when user has no previous sessions for baseline."""
    token = await register_and_login(client, email="first_session@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
    db_session.add(session_feedback)
    await db_session.commit()

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
async def test_generate_session_feedback_endpoint(client, db_session, mock_content_metrics):
    """Test POST /api/v1/feedback/generate/session/{session_id} endpoint."""
    token = await register_and_login(client, email="gen_session@example.com")

    # Create a behavioral question that can be assigned
    question = Question(
        content="Test session feedback generation",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "behavioral", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # Submit response
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "transcript": "I led a team of engineers to deliver a critical project.",
            "duration_seconds": 60,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"

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
async def test_generate_session_feedback_no_responses_api(client, db_session):
    """Test generate session feedback returns 400 when no responses exist."""
    token = await register_and_login(client, email="gen_no_resp@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_generate_response_feedback_no_transcript(client, db_session):
    """Test generate response feedback returns 400 when no transcript exists."""
    token = await register_and_login(client, email="gen_no_trans@example.com")

    # Create a question that can be assigned
    question = Question(
        content="Test no transcript",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "technical", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # Submit response without transcript
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "duration_seconds": 30,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"
    response_id = submit_resp.json()["id"]

    # Try to generate feedback without transcript
    gen_resp = await client.post(
        f"/api/v1/feedback/generate/response/{response_id}",
        headers={"Authorization": token},
    )
    assert gen_resp.status_code == 400
    assert "no transcript" in gen_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_session_feedback_unauthorized_access(client, db_session):
    """Test that users cannot access another user's session feedback."""
    token1 = await register_and_login(client, email="owner_session@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_all_feedbacks_unauthorized_access(client, db_session):
    """Test that users cannot access another user's all feedbacks."""
    token1 = await register_and_login(client, email="owner_all@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_comparison_unauthorized_access(client, db_session):
    """Test that users cannot access another user's comparison."""
    token1 = await register_and_login(client, email="owner_comp@example.com")

    interview_resp = await client.post(
        "/api/v1/interviews",
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
async def test_generate_session_feedback_already_exists(client, db_session, mock_content_metrics):
    """Test generate session feedback when feedback already exists."""
    token = await register_and_login(client, email="gen_already@example.com")

    # Create a behavioral question that can be assigned
    question = Question(
        content="Test duplicate feedback generation",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()

    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"interview_type": "behavioral", "question_count": 1},
        headers={"Authorization": token},
    )
    interview_id = interview_resp.json()["id"]

    # Start interview (assigns questions automatically)
    start_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start",
        headers={"Authorization": token},
    )
    assert start_resp.status_code == 200, f"Start failed: {start_resp.json()}"

    # Get the assigned question
    questions_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/questions",
        headers={"Authorization": token},
    )
    question_id = questions_resp.json()[0]["id"]

    # Submit response
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/responses",
        json={
            "question_id": question_id,
            "transcript": "I successfully led a team project.",
            "duration_seconds": 60,
        },
        headers={"Authorization": token},
    )
    assert submit_resp.status_code == 201, f"Submit failed: {submit_resp.json()}"

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
async def test_generate_session_feedback_invalid_session(client, db_session):
    """Test generate session feedback with invalid session ID returns 404."""

    token = await register_and_login(client, email="gen_invalid@example.com")

    # Use a non-existent session ID
    fake_session_id = uuid4()

    gen_resp = await client.post(
        f"/api/v1/feedback/generate/session/{fake_session_id}",
        headers={"Authorization": token},
    )
    assert gen_resp.status_code == 404
    assert "not found" in gen_resp.json()["detail"].lower()


# Additional FeedbackService Error Path Tests for Coverage


@pytest.mark.asyncio
async def test_generate_feedback_response_not_found(db_session):
    """Test FeedbackService.generate_feedback raises ValueError for non-existent response."""
    service = FeedbackService()
    fake_response_id = uuid4()

    with pytest.raises(ValueError, match="not found"):
        await service.generate_feedback(db_session, fake_response_id)


# Note: test_generate_feedback_question_not_found skipped
# Testing this requires complex mocking due to foreign key constraints
# The error path is covered by integration tests


@pytest.mark.asyncio
async def test_generate_session_feedback_session_not_found(db_session):
    """Test FeedbackService.generate_session_feedback raises ValueError for non-existent session."""
    service = FeedbackService()
    fake_session_id = uuid4()

    with pytest.raises(ValueError, match="not found"):
        await service.generate_session_feedback(db_session, fake_session_id)


@pytest.mark.asyncio
async def test_feedback_service_generate_session_feedback_already_exists(
    db_session, mock_content_metrics
):
    """Test FeedbackService.generate_session_feedback raises ValueError when feedback exists."""
    from app.models.user import User
    from app.security import hash_password

    # Create user
    user = User(email="session_exists@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create interview
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Create existing session feedback
    existing_feedback = SessionFeedback(
        session_id=interview.id,
        overall_score=85.0,
        audio_score=80.0,
        content_score=90.0,
        top_strengths=["Good"],
        top_improvements=["Better"],
        recommended_practice_areas=["Practice"],
    )
    db_session.add(existing_feedback)
    await db_session.commit()

    service = FeedbackService()
    with pytest.raises(ValueError, match="already exists"):
        await service.generate_session_feedback(db_session, interview.id)


@pytest.mark.asyncio
async def test_generate_session_feedback_no_feedback_generated(db_session):
    """Test FeedbackService.generate_session_feedback raises ValueError when no feedback can be generated."""
    from app.models.user import User
    from app.security import hash_password

    # Create user
    user = User(email="no_feedback@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create question
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create interview with response but no transcript (can't generate feedback)
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Create response without transcript
    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript=None,  # No transcript
        duration_seconds=60,
    )
    db_session.add(response)
    await db_session.commit()

    service = FeedbackService()
    with pytest.raises(ValueError, match="No feedback could be generated"):
        await service.generate_session_feedback(db_session, interview.id)


@pytest.mark.asyncio
async def test_get_processing_summary(db_session):
    """Test FeedbackService.get_processing_summary returns correct status counts."""
    from app.models.user import User
    from app.security import hash_password

    # Create user
    user = User(email="processing@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create question
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create interview
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Create responses with different processing statuses
    response1 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Response 1",
        processing_status=ProcessingStatus.COMPLETED,
    )
    response2 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Response 2",
        processing_status=ProcessingStatus.PENDING,
    )
    response3 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Response 3",
        processing_status=ProcessingStatus.FAILED,
    )
    db_session.add(response1)
    db_session.add(response2)
    db_session.add(response3)
    await db_session.commit()

    service = FeedbackService()
    summary = await service.get_processing_summary(db_session, interview.id)

    assert summary["total_responses"] == 3
    assert summary["status_counts"]["completed"] == 1
    assert summary["status_counts"]["pending"] == 1
    assert summary["status_counts"]["failed"] == 1
    assert summary["all_processed"] is False
    assert summary["has_session_feedback"] is False
    assert "current_step" in summary


@pytest.mark.asyncio
async def test_get_user_progress_summary(db_session, mock_content_metrics):
    """Test FeedbackService.get_user_progress_summary returns progress metrics."""
    from app.models.user import User
    from app.security import hash_password

    # Create user
    user = User(email="progress@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create completed interviews with feedback
    interview1 = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    interview2 = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(interview1)
    db_session.add(interview2)
    await db_session.commit()
    await db_session.refresh(interview1)
    await db_session.refresh(interview2)

    # Create session feedbacks
    feedback1 = SessionFeedback(
        session_id=interview1.id,
        overall_score=85.0,
        audio_score=80.0,
        content_score=90.0,
        top_strengths=["Good"],
        top_improvements=["Better"],
        recommended_practice_areas=["Technical accuracy"],
    )
    feedback2 = SessionFeedback(
        session_id=interview2.id,
        overall_score=75.0,
        audio_score=70.0,
        content_score=80.0,
        top_strengths=["Clear"],
        top_improvements=["More detail"],
        recommended_practice_areas=["Answer structure"],
    )
    db_session.add(feedback1)
    db_session.add(feedback2)
    await db_session.commit()

    service = FeedbackService()
    progress = await service.get_user_progress(db_session, user.id)

    assert "recommended_practice_areas" in progress
    assert "average_audio_score" in progress
    assert "average_content_score" in progress
    assert progress["average_audio_score"] == 75.0
    assert progress["average_content_score"] == 85.0
    assert len(progress["recommended_practice_areas"]) > 0


@pytest.mark.asyncio
async def test_get_user_progress_summary_no_sessions(db_session):
    """Test FeedbackService.get_user_progress returns empty metrics for new user."""
    from app.models.user import User
    from app.security import hash_password

    # Create user with no sessions
    user = User(email="new_user@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = FeedbackService()
    progress = await service.get_user_progress(db_session, user.id)

    assert progress["recommended_practice_areas"] == []
    assert progress["average_audio_score"] is None
    assert progress["average_content_score"] is None


# InterviewService Unit Tests for Coverage


@pytest.mark.asyncio
async def test_interview_service_assign_specific_question_inactive_fails(db_session):
    """Test InterviewService.assign_specific_question raises ValueError for inactive question."""
    from app.models.user import User
    from app.security import hash_password
    from app.services.interview_service import InterviewService

    # Create user
    user = User(email="service_test@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create inactive question
    question = Question(
        content="Inactive question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=False,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create interview
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    service = InterviewService()
    with pytest.raises(ValueError, match="not found or is inactive"):
        await service.assign_specific_question(db_session, interview, question.id)


@pytest.mark.asyncio
async def test_interview_service_assign_specific_question_nonexistent_fails(db_session):
    """Test InterviewService.assign_specific_question raises ValueError for non-existent question."""
    from uuid import uuid4

    from app.models.user import User
    from app.security import hash_password
    from app.services.interview_service import InterviewService

    # Create user
    user = User(email="service_test2@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create interview
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    service = InterviewService()
    fake_question_id = uuid4()
    with pytest.raises(ValueError, match="not found or is inactive"):
        await service.assign_specific_question(db_session, interview, fake_question_id)


@pytest.mark.asyncio
async def test_interview_service_assign_specific_question_success(db_session):
    """Test InterviewService.assign_specific_question successfully assigns question."""
    from app.models.user import User
    from app.security import hash_password
    from app.services.interview_service import InterviewService

    # Create user
    user = User(email="service_test3@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create active question
    question = Question(
        content="Active question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create interview
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    service = InterviewService()
    interview_question = await service.assign_specific_question(db_session, interview, question.id)

    assert interview_question is not None
    assert interview_question.session_id == interview.id
    assert interview_question.question_id == question.id
    assert interview_question.order == 1
    assert interview_question.time_limit_seconds == 180


@pytest.mark.asyncio
async def test_interview_service_has_assigned_questions(db_session):
    """Test InterviewService.has_assigned_questions returns correct boolean."""
    from app.models.user import User
    from app.security import hash_password
    from app.services.interview_service import InterviewService

    # Create user
    user = User(email="has_questions@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create question
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create interview
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    service = InterviewService()

    # Initially no questions assigned
    has_questions = await service.has_assigned_questions(db_session, interview.id)
    assert has_questions is False

    # Assign question
    await service.assign_specific_question(db_session, interview, question.id)

    # Now should have questions
    has_questions = await service.has_assigned_questions(db_session, interview.id)
    assert has_questions is True


@pytest.mark.asyncio
async def test_interview_service_get_interview_questions(db_session):
    """Test InterviewService.get_interview_questions returns questions in order."""
    from app.models.user import User
    from app.security import hash_password
    from app.services.interview_service import InterviewService

    # Create user
    user = User(email="get_questions@example.com", hashed_password=hash_password("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create questions
    question1 = Question(
        content="Question 1",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    question2 = Question(
        content="Question 2",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question1)
    db_session.add(question2)
    await db_session.commit()
    await db_session.refresh(question1)
    await db_session.refresh(question2)

    # Create interview
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    service = InterviewService()

    # Assign questions manually to control order
    interview_question1 = InterviewQuestion(
        session_id=interview.id,
        question_id=question1.id,
        order=1,
    )
    interview_question2 = InterviewQuestion(
        session_id=interview.id,
        question_id=question2.id,
        order=2,
    )
    db_session.add(interview_question1)
    db_session.add(interview_question2)
    await db_session.commit()

    # Get questions - should be in order
    questions = await service.get_interview_questions(db_session, interview.id)
    assert len(questions) == 2
    assert questions[0].id == question1.id
    assert questions[1].id == question2.id
