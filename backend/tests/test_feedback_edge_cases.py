"""Edge case tests for feedback API endpoints to improve coverage."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel import SQLModel, select

from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User

# Import register_and_login from conftest.py
from tests.conftest import register_and_login

async def create_test_interview_with_response(db_session, user: User) -> tuple:
    """Create interview session with response for testing."""
    question = Question(
        content="Test question",
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

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Test answer with good structure and examples",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    return interview, response

# Session Feedback Tests

@pytest.mark.asyncio
async def test_get_session_feedback_nonexistent_session_fails(client):
    """Test GET /feedback/session/{id} with non-existent UUID returns 404."""
    token = await register_and_login(client)
    fake_id = uuid4()

    resp = await client.get(
        f"/api/v1/feedbacksession/{fake_id}",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_session_feedback_unauthorized_access_fails(client, db_session):
    """Test that users cannot access other users' session feedback."""
    # User 1 creates interview
    await register_and_login(client, "user1@example.com")
    result = await db_session.exec(
        select(User).where(User.email == "user1@example.com")
    )
    user1 = result.first()

    interview, _ = await create_test_interview_with_response(db_session, user1)

    # User 2 tries to access User 1's session feedback
    token2 = await register_and_login(client, "user2@example.com")

    resp = await client.get(
        f"/api/v1/feedbacksession/{interview.id}",
        headers={"Authorization": token2},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_session_feedback_no_feedback_generated(client, db_session):
    """Test GET /feedback/session/{id} when feedback not yet generated returns 404."""
    token = await register_and_login(client, "no_feedback@example.com")
    result = await db_session.exec(
        select(User).where(User.email == "no_feedback@example.com")
    )
    user = result.first()

    interview, _ = await create_test_interview_with_response(db_session, user)

    resp = await client.get(
        f"/api/v1/feedbacksession/{interview.id}",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404
    assert "not yet generated" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_all_session_feedbacks_empty_list(client, db_session):
    """Test GET /feedback/session/{id}/all returns empty list when no responses."""
    token = await register_and_login(client, "empty_session@example.com")
    result = await db_session.exec(
        select(User).where(User.email == "empty_session@example.com")
    )
    user = result.first()

    # Create interview without responses
    interview = InterviewSession(
        user_id=user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    resp = await client.get(
        f"/api/v1/feedbacksession/{interview.id}/all",
        headers={"Authorization": token},
    )
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.asyncio
async def test_get_all_session_feedbacks_unauthorized_fails(client, db_session):
    """Test GET /feedback/session/{id}/all with unauthorized user returns 404."""
    # User 1 creates interview
    await register_and_login(client, "owner@example.com")
    user1 = (
        await db_session.exec(select(User).where(User.email == "owner@example.com"))
    ).first()

    interview, _ = await create_test_interview_with_response(db_session, user1)

    # User 2 tries to access
    token2 = await register_and_login(client, "other@example.com")

    resp = await client.get(
        f"/api/v1/feedbacksession/{interview.id}/all",
        headers={"Authorization": token2},
    )
    assert resp.status_code == 404

# Response Feedback Tests

@pytest.mark.asyncio
async def test_get_response_feedback_nonexistent_response_fails(client):
    """Test GET /feedback/response/{id} with non-existent UUID returns 404."""
    token = await register_and_login(client)
    fake_id = uuid4()

    resp = await client.get(
        f"/api/v1/feedbackresponse/{fake_id}",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_response_feedback_unauthorized_access_fails(client, db_session):
    """Test that users cannot access other users' response feedback."""
    # User 1 creates response
    await register_and_login(client, "resp_owner@example.com")
    user1 = (
        await db_session.exec(
            select(User).where(User.email == "resp_owner@example.com")
        )
    ).first()

    _, response = await create_test_interview_with_response(db_session, user1)

    # User 2 tries to access
    token2 = await register_and_login(client, "resp_other@example.com")

    resp = await client.get(
        f"/api/v1/feedbackresponse/{response.id}",
        headers={"Authorization": token2},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_response_feedback_not_generated_fails(client, db_session):
    """Test GET /feedback/response/{id} when feedback not generated returns 404."""
    token = await register_and_login(client, "no_resp_feedback@example.com")
    user = (
        await db_session.exec(
            select(User).where(User.email == "no_resp_feedback@example.com")
        )
    ).first()

    _, response = await create_test_interview_with_response(db_session, user)

    resp = await client.get(
        f"/api/v1/feedbackresponse/{response.id}",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404
    assert "not yet generated" in resp.json()["detail"].lower()

# Generate Feedback Tests

@pytest.mark.asyncio
async def test_generate_response_feedback_unauthorized_fails(client, db_session):
    """Test POST /feedback/generate/response/{id} unauthorized access fails."""
    # User 1 creates response
    await register_and_login(client, "gen_owner@example.com")
    user1 = (
        await db_session.exec(
            select(User).where(User.email == "gen_owner@example.com")
        )
    ).first()

    _, response = await create_test_interview_with_response(db_session, user1)

    # User 2 tries to generate feedback
    token2 = await register_and_login(client, "gen_other@example.com")

    resp = await client.post(
        f"/api/v1/feedbackgenerate/response/{response.id}",
        headers={"Authorization": token2},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_generate_response_feedback_nonexistent_fails(client):
    """Test POST /feedback/generate/response/{id} with non-existent UUID fails."""
    token = await register_and_login(client)
    fake_id = uuid4()

    resp = await client.post(
        f"/api/v1/feedbackgenerate/response/{fake_id}",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_generate_session_feedback_unauthorized_fails(client, db_session):
    """Test POST /feedback/generate/session/{id} unauthorized access fails."""
    # User 1 creates interview
    await register_and_login(client, "session_gen_owner@example.com")
    user1 = (
        await db_session.exec(
            select(User).where(User.email == "session_gen_owner@example.com")
        )
    ).first()

    interview, _ = await create_test_interview_with_response(db_session, user1)

    # User 2 tries to generate
    token2 = await register_and_login(client, "session_gen_other@example.com")

    resp = await client.post(
        f"/api/v1/feedbackgenerate/session/{interview.id}",
        headers={"Authorization": token2},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_generate_session_feedback_nonexistent_fails(client):
    """Test POST /feedback/generate/session/{id} with non-existent UUID fails."""
    token = await register_and_login(client)
    fake_id = uuid4()

    resp = await client.post(
        f"/api/v1/feedbackgenerate/session/{fake_id}",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404

# Session Processing Status Tests

@pytest.mark.asyncio
async def test_get_session_processing_status_unauthorized_fails(client, db_session):
    """Test GET /feedback/session/{id}/status unauthorized access fails."""
    # User 1 creates interview
    await register_and_login(client, "status_owner@example.com")
    user1 = (
        await db_session.exec(
            select(User).where(User.email == "status_owner@example.com")
        )
    ).first()

    interview, _ = await create_test_interview_with_response(db_session, user1)

    # User 2 tries to access status
    token2 = await register_and_login(client, "status_other@example.com")

    resp = await client.get(
        f"/api/v1/feedbacksession/{interview.id}/status",
        headers={"Authorization": token2},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_session_processing_status_nonexistent_fails(client):
    """Test GET /feedback/session/{id}/status with non-existent UUID fails."""
    token = await register_and_login(client)
    fake_id = uuid4()

    resp = await client.get(
        f"/api/v1/feedbacksession/{fake_id}/status",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404

# Session Comparison Tests

@pytest.mark.asyncio
async def test_get_session_comparison_unauthorized_fails(client, db_session):
    """Test GET /feedback/session/{id}/comparison unauthorized access fails."""
    # User 1 creates interview
    await register_and_login(client, "comp_owner@example.com")
    user1 = (
        await db_session.exec(
            select(User).where(User.email == "comp_owner@example.com")
        )
    ).first()

    interview, _ = await create_test_interview_with_response(db_session, user1)

    # User 2 tries to access comparison
    token2 = await register_and_login(client, "comp_other@example.com")

    resp = await client.get(
        f"/api/v1/feedbacksession/{interview.id}/comparison",
        headers={"Authorization": token2},
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_session_comparison_no_feedback_fails(client, db_session):
    """Test GET /feedback/session/{id}/comparison without feedback returns 404."""
    token = await register_and_login(client, "comp_no_feedback@example.com")
    user = (
        await db_session.exec(
            select(User).where(User.email == "comp_no_feedback@example.com")
        )
    ).first()

    interview, _ = await create_test_interview_with_response(db_session, user)

    resp = await client.get(
        f"/api/v1/feedbacksession/{interview.id}/comparison",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404
    assert "not yet generated" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_session_comparison_nonexistent_session_fails(client):
    """Test GET /feedback/session/{id}/comparison with non-existent UUID fails."""
    token = await register_and_login(client)
    fake_id = uuid4()

    resp = await client.get(
        f"/api/v1/feedbacksession/{fake_id}/comparison",
        headers={"Authorization": token},
    )
    assert resp.status_code == 404
