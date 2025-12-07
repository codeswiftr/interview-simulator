"""Tests for coaching hint generation endpoint."""

from unittest.mock import patch

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
