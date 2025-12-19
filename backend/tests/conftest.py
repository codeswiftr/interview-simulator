"""Shared test fixtures for interview-simulator tests.

This module provides common fixtures for database setup, user creation,
and session management across all test modules.

Note: Tests use PostgreSQL (same as production) due to ARRAY column types.
Set TEST_DATABASE_URL environment variable or have PostgreSQL running locally.
"""

import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# PostgreSQL required due to ARRAY column types in Question model
# Default to the FORGE local development database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://forge:forge_local@localhost:5432/interview_simulator_test"
    )
)

# Create test engine (only if tests actually need database)
_test_engine = None
_TestSessionLocal = None


def get_test_engine():
    """Lazy initialization of test engine."""
    global _test_engine, _TestSessionLocal
    if _test_engine is None:
        _test_engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            future=True,
            poolclass=NullPool,
        )
        _TestSessionLocal = async_sessionmaker(
            _test_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _test_engine, _TestSessionLocal


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Get test database engine."""
    engine, _ = get_test_engine()
    return engine


@pytest.fixture(scope="session")
async def prepare_database(test_engine):
    """Create all tables once for the test session.

    This fixture only runs when tests actually request database fixtures.
    """
    # Import all models to register them with SQLModel.metadata
    # This must happen before create_all() is called
    from app.models import feedback, interview, preparation, question, user  # noqa: F401
    from app.models.email_verification import EmailVerificationToken  # noqa: F401
    from app.models.password_reset import PasswordResetToken  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def clean_database(test_engine, prepare_database):
    """Clean database between tests that use database fixtures."""
    yield
    # Clean up after test
    async with test_engine.begin() as conn:
        # Use TRUNCATE with CASCADE for PostgreSQL
        for table in reversed(SQLModel.metadata.sorted_tables):
            try:
                await conn.execute(
                    text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE')
                )
            except Exception:
                # Fallback to DELETE for compatibility
                await conn.execute(text(f'DELETE FROM "{table.name}"'))


@pytest.fixture
async def db_session(clean_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.models.user import User
    from app.security import hash_password

    user = User(
        id=str(uuid4()),
        email=f"testuser_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("TestPassword123!"),
        experience_level="mid",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_question(db_session: AsyncSession):
    """Create a test question."""
    from app.models.question import Difficulty, Question, QuestionCategory

    question = Question(
        id=str(uuid4()),
        content="Tell me about a time you faced a challenging technical problem.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def test_interview(db_session: AsyncSession, test_user, test_question):
    """Create a test interview session."""
    from app.models.interview import (
        InterviewQuestion,
        InterviewSession,
        InterviewStatus,
        InterviewType,
    )

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=1,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Add question to interview
    interview_question = InterviewQuestion(
        id=str(uuid4()),
        session_id=interview.id,
        question_id=test_question.id,
        order=1,
        time_limit_seconds=test_question.expected_duration_seconds,
    )
    db_session.add(interview_question)
    await db_session.commit()

    return interview


@pytest.fixture
async def test_response(db_session: AsyncSession, test_interview, test_question):
    """Create a test interview response."""
    from app.models.interview import InterviewResponse

    response = InterviewResponse(
        id=str(uuid4()),
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="This is a test response transcript.",
        audio_url="/uploads/test_audio.webm",
        video_url="/uploads/test_video.webm",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)
    return response


@pytest.fixture
async def client(clean_database):
    """Provide an async HTTP client for API testing.

    This fixture creates an AsyncClient configured to test the FastAPI app,
    with database session dependency overridden to use the test database.
    """
    # Lazy import to avoid triggering app initialization before test db is set up
    from app.db import get_session
    from app.main import app

    _, TestSessionLocal = get_test_engine()

    async def _override_get_session():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_and_login(client: AsyncClient, email: str = "testuser@example.com", password: str = "TestPassword123!") -> str:
    """Register a user and return the bearer token.

    Args:
        client: The async HTTP client
        email: User email address
        password: User password

    Returns:
        Bearer token string (e.g., "Bearer eyJ...")
    """
    # Register user
    await client.post(
        "/api/v1/users/register",
        json={"email": email, "password": password}
    )
    # Login and get token
    resp = await client.post(
        "/api/v1/users/login",
        json={"email": email, "password": password}
    )
    token = resp.json().get("access_token", "")
    return f"Bearer {token}"
