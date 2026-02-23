"""Tests for industry-specific question features."""

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.data.seed_industry_questions import seed_industry_questions
from app.models.question import Difficulty, Industry, Question, QuestionCategory, Role
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_question_has_industry_and_role_fields(db_session: AsyncSession):
    """Test that Question model has industry and role fields with defaults."""
    question = Question(
        content="Test question about software engineering",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    assert question.industry == Industry.GENERAL
    assert question.role == Role.GENERAL


@pytest.mark.asyncio
async def test_create_question_with_industry_and_role(client: AsyncClient):
    """Test creating a question with specific industry and role via API."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/questions",
        headers={"Authorization": token},
        json={
            "content": "How do you handle PCI compliance in payment systems?",
            "category": "technical",
            "difficulty": "hard",
            "industry": "fintech",
            "role": "software_engineer",
            "company_tags": ["Stripe", "Square"],
            "topic_tags": ["compliance", "security"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["industry"] == "fintech"
    assert data["role"] == "software_engineer"


@pytest.mark.asyncio
async def test_list_questions_filter_by_industry(client: AsyncClient, db_session: AsyncSession):
    """Test filtering questions by industry."""
    # Create questions with different industries
    questions = [
        Question(
            content="SaaS multi-tenancy question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.SAAS,
            role=Role.SOFTWARE_ENGINEER,
        ),
        Question(
            content="Fintech payment question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.FINTECH,
            role=Role.SOFTWARE_ENGINEER,
        ),
        Question(
            content="General question",
            category=QuestionCategory.BEHAVIORAL,
            industry=Industry.GENERAL,
            role=Role.GENERAL,
        ),
    ]
    for q in questions:
        db_session.add(q)
    await db_session.commit()

    # Filter by SaaS industry
    response = await client.get("/api/v1/questions?industry=saas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["industry"] == "saas"


@pytest.mark.asyncio
async def test_list_questions_filter_by_role(client: AsyncClient, db_session: AsyncSession):
    """Test filtering questions by role."""
    # Create questions with different roles
    questions = [
        Question(
            content="Engineering manager question",
            category=QuestionCategory.BEHAVIORAL,
            industry=Industry.GENERAL,
            role=Role.ENGINEERING_MANAGER,
        ),
        Question(
            content="Software engineer question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.GENERAL,
            role=Role.SOFTWARE_ENGINEER,
        ),
        Question(
            content="Data engineer question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.GENERAL,
            role=Role.DATA_ENGINEER,
        ),
    ]
    for q in questions:
        db_session.add(q)
    await db_session.commit()

    # Filter by engineering manager role
    response = await client.get("/api/v1/questions?role=engineering_manager")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "engineering_manager"


@pytest.mark.asyncio
async def test_list_questions_filter_by_industry_and_role(
    client: AsyncClient, db_session: AsyncSession
):
    """Test filtering questions by both industry and role."""
    # Create questions with different industry/role combinations
    questions = [
        Question(
            content="Fintech software engineer question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.FINTECH,
            role=Role.SOFTWARE_ENGINEER,
        ),
        Question(
            content="Fintech data engineer question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.FINTECH,
            role=Role.DATA_ENGINEER,
        ),
        Question(
            content="Healthcare software engineer question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.HEALTHCARE,
            role=Role.SOFTWARE_ENGINEER,
        ),
    ]
    for q in questions:
        db_session.add(q)
    await db_session.commit()

    # Filter by fintech AND software_engineer
    response = await client.get("/api/v1/questions?industry=fintech&role=software_engineer")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["industry"] == "fintech"
    assert data[0]["role"] == "software_engineer"


@pytest.mark.asyncio
async def test_get_random_question_filter_by_industry(
    client: AsyncClient, db_session: AsyncSession
):
    """Test getting random question filtered by industry."""
    # Create questions with different industries
    for i in range(5):
        db_session.add(
            Question(
                content=f"Healthcare question {i}",
                category=QuestionCategory.BEHAVIORAL,
                industry=Industry.HEALTHCARE,
                role=Role.SOFTWARE_ENGINEER,
            )
        )
    for i in range(5):
        db_session.add(
            Question(
                content=f"Gaming question {i}",
                category=QuestionCategory.TECHNICAL,
                industry=Industry.GAMING,
                role=Role.SOFTWARE_ENGINEER,
            )
        )
    await db_session.commit()

    # Get random healthcare question
    response = await client.get("/api/v1/questions/random?industry=healthcare")
    assert response.status_code == 200
    data = response.json()
    assert data["industry"] == "healthcare"
    assert "Healthcare question" in data["content"]


@pytest.mark.asyncio
async def test_get_random_question_filter_by_role(client: AsyncClient, db_session: AsyncSession):
    """Test getting random question filtered by role."""
    # Create questions with different roles
    for i in range(3):
        db_session.add(
            Question(
                content=f"DevOps question {i}",
                category=QuestionCategory.TECHNICAL,
                industry=Industry.GENERAL,
                role=Role.DEVOPS,
            )
        )
    for i in range(3):
        db_session.add(
            Question(
                content=f"PM question {i}",
                category=QuestionCategory.BEHAVIORAL,
                industry=Industry.GENERAL,
                role=Role.PRODUCT_MANAGER,
            )
        )
    await db_session.commit()

    # Get random DevOps question
    response = await client.get("/api/v1/questions/random?role=devops")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "devops"
    assert "DevOps question" in data["content"]


@pytest.mark.asyncio
async def test_get_random_question_filter_by_industry_and_role(
    client: AsyncClient, db_session: AsyncSession
):
    """Test getting random question filtered by both industry and role."""
    # Create specific industry+role combinations
    db_session.add(
        Question(
            content="E-commerce product manager question",
            category=QuestionCategory.BEHAVIORAL,
            industry=Industry.ECOMMERCE,
            role=Role.PRODUCT_MANAGER,
        )
    )
    db_session.add(
        Question(
            content="E-commerce software engineer question",
            category=QuestionCategory.TECHNICAL,
            industry=Industry.ECOMMERCE,
            role=Role.SOFTWARE_ENGINEER,
        )
    )
    await db_session.commit()

    # Get random e-commerce PM question
    response = await client.get("/api/v1/questions/random?industry=ecommerce&role=product_manager")
    assert response.status_code == 200
    data = response.json()
    assert data["industry"] == "ecommerce"
    assert data["role"] == "product_manager"
    assert "product manager" in data["content"].lower()


@pytest.mark.asyncio
async def test_seed_industry_questions_idempotent(db_session: AsyncSession):
    """Test that seed_industry_questions is idempotent and doesn't create duplicates."""
    # First seed
    await seed_industry_questions(db_session, auto_commit=False)

    result1 = await db_session.exec(select(Question))
    count1 = len(result1.all())

    # Second seed (should be idempotent)
    await seed_industry_questions(db_session, auto_commit=False)

    result2 = await db_session.exec(select(Question))
    count2 = len(result2.all())

    # Count should be the same (no duplicates created)
    assert count1 == count2
    # Should have 100 industry questions
    assert count1 == 100


@pytest.mark.asyncio
async def test_seed_industry_questions_content(db_session: AsyncSession):
    """Test that seeded questions have proper industry/role assignments."""
    await seed_industry_questions(db_session, auto_commit=False)
    await db_session.flush()  # Flush to make changes visible in transaction
    db_session.expire_all()  # Expire all cached objects to force reload

    # Check total count first
    result = await db_session.exec(select(Question))
    all_questions = result.all()
    assert len(all_questions) == 100, f"Expected 100 questions, got {len(all_questions)}"

    # Check SaaS questions
    result = await db_session.exec(select(Question).where(Question.industry == Industry.SAAS))
    saas_questions = result.all()
    assert len(saas_questions) == 20, f"Expected 20 SaaS questions, got {len(saas_questions)}"

    # Check Fintech questions
    result = await db_session.exec(select(Question).where(Question.industry == Industry.FINTECH))
    fintech_questions = result.all()
    assert len(fintech_questions) == 20

    # Check Healthcare questions
    result = await db_session.exec(select(Question).where(Question.industry == Industry.HEALTHCARE))
    healthcare_questions = result.all()
    assert len(healthcare_questions) == 20

    # Check Gaming questions
    result = await db_session.exec(select(Question).where(Question.industry == Industry.GAMING))
    gaming_questions = result.all()
    assert len(gaming_questions) == 20

    # Check E-commerce questions
    result = await db_session.exec(select(Question).where(Question.industry == Industry.ECOMMERCE))
    ecommerce_questions = result.all()
    assert len(ecommerce_questions) == 20


@pytest.mark.asyncio
async def test_existing_questions_default_to_general(db_session: AsyncSession):
    """Test that existing questions without industry/role default to GENERAL."""
    # Create question without specifying industry/role (simulates existing data)
    question = Question(
        content="Legacy question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Should default to GENERAL for both
    assert question.industry == Industry.GENERAL
    assert question.role == Role.GENERAL


@pytest.mark.asyncio
async def test_combined_filters_industry_role_category_difficulty(
    client: AsyncClient, db_session: AsyncSession
):
    """Test combining industry, role, category, and difficulty filters."""
    # Create a specific question
    question = Question(
        content="Hard fintech behavioral question for engineering managers",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        industry=Industry.FINTECH,
        role=Role.ENGINEERING_MANAGER,
    )
    db_session.add(question)

    # Add some noise
    db_session.add(
        Question(
            content="Easy fintech behavioral",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.EASY,
            industry=Industry.FINTECH,
            role=Role.ENGINEERING_MANAGER,
        )
    )
    db_session.add(
        Question(
            content="Hard fintech technical",
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.HARD,
            industry=Industry.FINTECH,
            role=Role.ENGINEERING_MANAGER,
        )
    )
    await db_session.commit()

    # Query with all filters
    response = await client.get(
        "/api/v1/questions?"
        "industry=fintech&"
        "role=engineering_manager&"
        "category=behavioral&"
        "difficulty=hard"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Hard fintech behavioral question for engineering managers"
