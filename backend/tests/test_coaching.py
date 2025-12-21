"""Tests for coaching hint generation endpoint."""

import pytest
from httpx import AsyncClient

# Import register_and_login from conftest.py
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_coaching_hint_endpoint_requires_auth(client: AsyncClient):
    """Test that coaching hint endpoint requires authentication."""
    response = await client.post(
        "/api/v1/coaching/hint",
        json={
            "question": "Tell me about a time you handled a conflict",
            "question_type": "behavioral",
            "transcript": "I once had a conflict with a teammate",
        },
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_coaching_hint_endpoint_returns_hint(client: AsyncClient):
    """Test that coaching hint endpoint returns a contextual hint."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/coaching/hint",
        headers={"Authorization": token},
        json={
            "question": "Tell me about a time you handled a conflict",
            "question_type": "behavioral",
            "transcript": "I once had a conflict with a teammate",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "hint" in data
    assert isinstance(data["hint"], str)
    assert len(data["hint"]) > 0

@pytest.mark.asyncio
async def test_coaching_hint_validates_question_type(client: AsyncClient):
    """Test that coaching hint endpoint validates question_type."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/coaching/hint",
        headers={"Authorization": token},
        json={
            "question": "What is a hash table?",
            "question_type": "invalid_type",
            "transcript": "A hash table is a data structure",
        },
    )
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_coaching_hint_requires_question(client: AsyncClient):
    """Test that coaching hint endpoint requires question field."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/coaching/hint",
        headers={"Authorization": token},
        json={
            "question_type": "behavioral",
            "transcript": "Some answer",
        },
    )
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_coaching_hint_handles_empty_transcript(client: AsyncClient):
    """Test that coaching hint works with empty transcript."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/coaching/hint",
        headers={"Authorization": token},
        json={
            "question": "Tell me about yourself",
            "question_type": "behavioral",
            "transcript": "",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "hint" in data

@pytest.mark.asyncio
async def test_coaching_hint_stream_endpoint_requires_auth(client: AsyncClient):
    """Test that streaming coaching hint endpoint requires authentication."""
    response = await client.post(
        "/api/v1/coaching/hint/stream",
        json={
            "question": "Tell me about a time you handled a conflict",
            "question_type": "behavioral",
            "transcript": "I once had a conflict with a teammate",
        },
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_coaching_hint_stream_endpoint_returns_stream(client: AsyncClient):
    """Test that streaming coaching hint endpoint returns SSE stream."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/coaching/hint/stream",
        headers={"Authorization": token},
        json={
            "question": "Tell me about a time you handled a conflict",
            "question_type": "behavioral",
            "transcript": "I once had a conflict with a teammate",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Read stream chunks
    chunks = []
    async for chunk in response.aiter_bytes():
        if chunk:
            chunks.append(chunk.decode("utf-8"))

    # Should have at least one chunk
    assert len(chunks) > 0

    # Last chunk should have done=True
    last_chunk = chunks[-1]
    assert "done" in last_chunk or "data:" in last_chunk

@pytest.mark.asyncio
async def test_coaching_hint_stream_validates_question_type(client: AsyncClient):
    """Test that streaming endpoint validates question_type."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/coaching/hint/stream",
        headers={"Authorization": token},
        json={
            "question": "What is a hash table?",
            "question_type": "invalid_type",
            "transcript": "A hash table is a data structure",
        },
    )
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_coaching_hint_rate_limiting(client: AsyncClient):
    """Test that rate limiting is enforced for coaching hints."""
    token = await register_and_login(client)

    # Make 5 requests (the limit)
    for i in range(5):
        response = await client.post(
            "/api/v1/coaching/hint",
            headers={"Authorization": token},
            json={
                "question": f"Question {i}",
                "question_type": "behavioral",
                "transcript": f"Answer {i}",
            },
        )
        assert response.status_code == 200

    # 6th request should be rate limited
    response = await client.post(
        "/api/v1/coaching/hint",
        headers={"Authorization": token},
        json={
            "question": "Question 6",
            "question_type": "behavioral",
            "transcript": "Answer 6",
        },
    )
    assert response.status_code == 429  # Too Many Requests
    assert "rate limit" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_coaching_hint_stream_rate_limiting(client: AsyncClient):
    """Test that rate limiting is enforced for streaming hints."""
    token = await register_and_login(client)

    # Make 5 requests (the limit)
    for i in range(5):
        response = await client.post(
            "/api/v1/coaching/hint/stream",
            headers={"Authorization": token},
            json={
                "question": f"Question {i}",
                "question_type": "behavioral",
                "transcript": f"Answer {i}",
            },
        )
        assert response.status_code == 200

    # 6th request should be rate limited
    response = await client.post(
        "/api/v1/coaching/hint/stream",
        headers={"Authorization": token},
        json={
            "question": "Question 6",
            "question_type": "behavioral",
            "transcript": "Answer 6",
        },
    )
    assert response.status_code == 429  # Too Many Requests
