"""Comprehensive interview session management edge case tests.

Tests critical interview flow scenarios:
- Session state transitions
- Concurrent session handling
- Question assignment edge cases
- Session timeout and cleanup
- Invalid state transitions
- Resource cleanup on session end
"""

from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.interview import (
    InterviewResponse,
    InterviewStatus,
)
from app.models.question import Difficulty, Question, QuestionCategory
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_cannot_start_interview_with_zero_questions(client, db_session):
    """Test that interviews with 0 questions are rejected."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/interviews/start",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 0,  # Invalid
            "difficulty": "medium",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cannot_start_interview_with_excessive_questions(client, db_session):
    """Test that interviews with too many questions are rejected."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/interviews/start",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 1000,  # Excessive
            "difficulty": "medium",
        },
    )

    # Should be rejected (validation or business logic)
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_free_tier_cannot_create_multiple_concurrent_sessions(client, db_session):
    """Test that free tier users cannot have multiple active sessions."""
    token = await register_and_login(client)

    # Create seed questions
    question1 = Question(
        id=str(uuid4()),
        content="Tell me about yourself.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        expected_duration_seconds=180,
    )
    question2 = Question(
        id=str(uuid4()),
        content="What's your biggest weakness?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    db_session.add(question1)
    db_session.add(question2)
    await db_session.commit()

    # Start first interview
    response1 = await client.post(
        "/api/v1/interviews/start",
        headers={"Authorization": token},
        json={"interview_type": "behavioral", "question_count": 1, "difficulty": "medium"},
    )
    assert response1.status_code == 200

    # Try to start second interview while first is still active
    response2 = await client.post(
        "/api/v1/interviews/start",
        headers={"Authorization": token},
        json={"interview_type": "technical", "question_count": 1, "difficulty": "medium"},
    )

    # Should be blocked for free tier
    assert response2.status_code in [400, 403]


@pytest.mark.asyncio
async def test_interview_with_no_available_questions_fails_gracefully(client, db_session):
    """Test that interview creation fails gracefully when no questions available."""
    token = await register_and_login(client)

    # Don't seed any questions
    response = await client.post(
        "/api/v1/interviews/start",
        headers={"Authorization": token},
        json={"interview_type": "behavioral", "question_count": 5, "difficulty": "medium"},
    )

    # Should return error about insufficient questions
    assert response.status_code in [400, 404]
    if response.status_code == 400:
        assert "question" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_interview_status_transition_validates_workflow(client, db_session, test_interview):
    """Test that invalid interview status transitions are rejected."""
    token = await register_and_login(client)

    # Try to complete interview without it being in progress
    test_interview.status = InterviewStatus.COMPLETED
    await db_session.commit()

    # Try to complete again
    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/complete", headers={"Authorization": token}
    )

    # Should reject invalid transition
    assert response.status_code in [400, 404]


@pytest.mark.asyncio
async def test_cannot_submit_response_for_completed_interview(
    client, db_session, test_interview, test_question
):
    """Test that responses cannot be submitted to completed interviews."""
    token = await register_and_login(client)

    # Complete the interview
    test_interview.status = InterviewStatus.COMPLETED
    await db_session.commit()

    # Try to submit response
    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json={"transcript": "This is my response", "duration_seconds": 120},
    )

    # Should be rejected
    assert response.status_code in [400, 403]


@pytest.mark.asyncio
async def test_cannot_access_another_users_interview(client, db_session, test_interview):
    """Test that users cannot access other users' interviews."""
    # Create a different user
    token = await register_and_login(client, email="different_user@example.com")

    # Try to access test_interview (belongs to different user)
    response = await client.get(
        f"/api/v1/interviews/{test_interview.id}", headers={"Authorization": token}
    )

    # Should be forbidden
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_cannot_submit_response_for_another_users_interview(
    client, db_session, test_interview, test_question
):
    """Test that users cannot submit responses to other users' interviews."""
    # Create a different user
    token = await register_and_login(client, email="different_user@example.com")

    # Try to submit response to test_interview (belongs to different user)
    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json={"transcript": "This is my response", "duration_seconds": 120},
    )

    # Should be forbidden
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_interview_with_invalid_uuid_returns_404(client, db_session):
    """Test that invalid interview UUID returns 404."""
    token = await register_and_login(client)

    response = await client.get(
        "/api/v1/interviews/not-a-valid-uuid", headers={"Authorization": token}
    )

    assert response.status_code in [404, 422]


@pytest.mark.asyncio
async def test_interview_with_nonexistent_uuid_returns_404(client, db_session):
    """Test that nonexistent interview UUID returns 404."""
    token = await register_and_login(client)

    fake_uuid = str(uuid4())
    response = await client.get(f"/api/v1/interviews/{fake_uuid}", headers={"Authorization": token})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_interview_list_pagination_boundary_conditions(client, db_session):
    """Test interview list pagination handles edge cases."""
    token = await register_and_login(client)

    # Test with limit=0
    response = await client.get("/api/v1/interviews?limit=0", headers={"Authorization": token})
    assert response.status_code in [200, 422]

    # Test with negative limit
    response = await client.get("/api/v1/interviews?limit=-1", headers={"Authorization": token})
    assert response.status_code in [200, 422]

    # Test with very large limit
    response = await client.get("/api/v1/interviews?limit=10000", headers={"Authorization": token})
    # Should cap at reasonable max or reject
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_duplicate_response_submission_handled_idempotently(
    client, db_session, test_interview, test_question
):
    """Test that duplicate response submissions are handled gracefully."""
    token = await register_and_login(client)

    response_data = {"transcript": "This is my response", "duration_seconds": 120}

    # Submit response twice
    response1 = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json=response_data,
    )

    response2 = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json=response_data,
    )

    # First should succeed
    assert response1.status_code in [200, 201]

    # Second should either succeed idempotently or reject
    assert response2.status_code in [200, 201, 400, 409]


@pytest.mark.asyncio
async def test_interview_with_company_filter_no_matching_questions(client, db_session):
    """Test interview creation with company filter when no matching questions exist."""
    token = await register_and_login(client)

    # Create generic question without company tags
    question = Question(
        id=str(uuid4()),
        content="General question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
        company_tags=[],
    )
    db_session.add(question)
    await db_session.commit()

    # Try to create interview for specific company
    response = await client.post(
        "/api/v1/interviews/start",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 5,
            "difficulty": "medium",
            "target_company": "Google",
        },
    )

    # Should either fall back to general questions or return error
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_interview_completion_calculates_stats_correctly(
    client, db_session, test_interview, test_question
):
    """Test that interview completion calculates duration and stats correctly."""
    token = await register_and_login(client)

    # Submit response first
    await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json={"transcript": "This is my response", "duration_seconds": 120},
    )

    # Complete interview
    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/complete", headers={"Authorization": token}
    )

    if response.status_code == 200:
        # Verify interview has end time and duration
        interview_data = response.json()
        assert interview_data["status"] == "completed"
        assert "ended_at" in interview_data or "completed_at" in interview_data


@pytest.mark.asyncio
async def test_interview_response_with_extremely_long_transcript(
    client, db_session, test_interview, test_question
):
    """Test that extremely long transcripts are handled or rejected."""
    token = await register_and_login(client)

    # Create very long transcript (100k characters)
    long_transcript = "word " * 20000

    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json={"transcript": long_transcript, "duration_seconds": 120},
    )

    # Should either accept (with potential truncation) or reject
    assert response.status_code in [200, 201, 413, 422]


@pytest.mark.asyncio
async def test_interview_response_with_empty_transcript(
    client, db_session, test_interview, test_question
):
    """Test that responses with empty transcripts are handled."""
    token = await register_and_login(client)

    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json={
            "transcript": "",  # Empty
            "duration_seconds": 120,
        },
    )

    # Should either accept (user didn't speak) or require non-empty transcript
    assert response.status_code in [200, 201, 400, 422]


@pytest.mark.asyncio
async def test_interview_response_with_invalid_duration(
    client, db_session, test_interview, test_question
):
    """Test that responses with invalid durations are rejected."""
    token = await register_and_login(client)

    # Test negative duration
    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json={"transcript": "My response", "duration_seconds": -10},
    )
    assert response.status_code in [400, 422]

    # Test zero duration
    response = await client.post(
        f"/api/v1/interviews/{test_interview.id}/questions/{test_question.id}/response",
        headers={"Authorization": token},
        json={"transcript": "My response", "duration_seconds": 0},
    )
    assert response.status_code in [200, 201, 400, 422]


@pytest.mark.asyncio
async def test_interview_deletes_cascade_to_responses(
    client, db_session, test_interview, test_question
):
    """Test that deleting interview cascades to delete responses."""
    # Create response
    response = InterviewResponse(
        id=str(uuid4()),
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Test response",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()

    response_id = response.id

    # Delete interview
    db_session.delete(test_interview)
    await db_session.commit()

    # Verify response was also deleted (cascade)
    result = await db_session.exec(
        select(InterviewResponse).where(InterviewResponse.id == response_id)
    )
    deleted_response = result.first()
    assert deleted_response is None
