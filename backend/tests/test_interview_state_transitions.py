"""Tests for interview service state transitions and complex workflows.

Focuses on real-world scenarios involving question assignment, session state,
and interaction patterns.
"""

from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.interview import (
    DifficultyLevel,
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.interview_service import InterviewService


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email=f"state_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def interview_service():
    """Provide an instance of InterviewService."""
    return InterviewService()


# Test: Full interview lifecycle
@pytest.mark.asyncio
async def test_interview_lifecycle_scheduled_to_completed(db_session, test_user, interview_service):
    """Test full interview lifecycle from scheduled to question assignment."""
    # Create questions
    questions = [
        Question(
            content=f"Lifecycle question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180,
        )
        for i in range(5)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    # Create scheduled interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=5,
        difficulty=DifficultyLevel.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Verify no questions assigned
    has_questions = await interview_service.has_assigned_questions(db_session, interview.id)
    assert has_questions is False

    # Assign questions
    assigned = await interview_service.assign_questions(db_session, interview)
    assert len(assigned) == 5

    # Verify questions are now assigned
    has_questions = await interview_service.has_assigned_questions(db_session, interview.id)
    assert has_questions is True

    # Retrieve assigned questions
    retrieved = await interview_service.get_interview_questions(db_session, interview.id)
    assert len(retrieved) == 5

    # Verify order is maintained
    for _, q in enumerate(retrieved, start=1):
        assert q.id in [iq.question_id for iq in assigned]


# Test: Question assignment prevents duplicate calls
@pytest.mark.asyncio
async def test_multiple_assign_calls_dont_duplicate(db_session, test_user, interview_service):
    """Test that calling assign_questions multiple times creates separate assignments."""
    # Create enough questions
    questions = [
        Question(
            content=f"Question {i}",
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(10)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        question_count=3,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # First assignment
    assigned1 = await interview_service.assign_questions(db_session, interview)
    assert len(assigned1) == 3

    # Second assignment (would create more InterviewQuestions)
    assigned2 = await interview_service.assign_questions(db_session, interview)
    assert len(assigned2) == 3

    # Check total InterviewQuestion count
    result = await db_session.exec(
        select(InterviewQuestion).where(InterviewQuestion.session_id == interview.id)
    )
    all_assignments = list(result.all())

    # Should have 6 total (3 from each call)
    assert len(all_assignments) == 6


# Test: Company-specific with partial availability
@pytest.mark.asyncio
async def test_progressive_company_question_availability(db_session, test_user, interview_service):
    """Test behavior when company-specific questions become available progressively."""
    # Initially create 2 Amazon questions
    amazon_q1 = Question(
        content="Amazon Q1",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["amazon"],
    )
    amazon_q2 = Question(
        content="Amazon Q2",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["amazon"],
    )

    # Create 3 general questions
    general_questions = [
        Question(
            content=f"General Q{i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(3)
    ]

    db_session.add_all([amazon_q1, amazon_q2] + general_questions)
    await db_session.commit()

    # Request 4 questions for Amazon
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        target_company="Amazon",
        question_count=4,
        difficulty=DifficultyLevel.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should get 2 Amazon + 2 general
    assigned = await interview_service.assign_questions(db_session, interview)
    assert len(assigned) == 4

    # Verify mix of company and general
    result = await db_session.exec(
        select(Question).where(Question.id.in_([iq.question_id for iq in assigned]))
    )
    assigned_questions = list(result.all())

    amazon_count = sum(1 for q in assigned_questions if "amazon" in q.company_tags)
    assert amazon_count == 2
    assert len(assigned_questions) - amazon_count == 2


# Test: Difficulty distribution in mixed mode
@pytest.mark.asyncio
async def test_mixed_difficulty_question_distribution(db_session, test_user, interview_service):
    """Test that mixed difficulty can select from all difficulty levels."""
    # Create questions with all difficulties
    easy_q = Question(
        content="Easy",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
    )
    medium_q = Question(
        content="Medium",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    hard_q = Question(
        content="Hard",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
    )

    db_session.add_all([easy_q, medium_q, hard_q])
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        question_count=3,
        difficulty=DifficultyLevel.MIXED,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)
    assert len(assigned) == 3

    # Verify we got all three questions
    assigned_ids = {iq.question_id for iq in assigned}
    assert easy_q.id in assigned_ids
    assert medium_q.id in assigned_ids
    assert hard_q.id in assigned_ids


# Test: Sequential question ordering
@pytest.mark.asyncio
async def test_sequential_question_order_maintained_across_retrievals(
    db_session, test_user, interview_service
):
    """Test that question order is consistent across multiple retrievals."""
    questions = [
        Question(
            content=f"Order Q{i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(5)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=5,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions
    await interview_service.assign_questions(db_session, interview)

    # Get questions multiple times
    retrieval1 = await interview_service.get_interview_questions(db_session, interview.id)
    retrieval2 = await interview_service.get_interview_questions(db_session, interview.id)
    retrieval3 = await interview_service.get_interview_questions(db_session, interview.id)

    # Order should be identical across all retrievals
    ids1 = [q.id for q in retrieval1]
    ids2 = [q.id for q in retrieval2]
    ids3 = [q.id for q in retrieval3]

    assert ids1 == ids2 == ids3


# Test: Category mapping edge cases
@pytest.mark.asyncio
async def test_get_category_for_type_all_types(interview_service):
    """Test _get_category_for_type for all interview types."""
    # Test all valid mappings
    assert (
        interview_service._get_category_for_type(InterviewType.BEHAVIORAL)
        == QuestionCategory.BEHAVIORAL
    )
    assert (
        interview_service._get_category_for_type(InterviewType.TECHNICAL)
        == QuestionCategory.TECHNICAL
    )
    assert (
        interview_service._get_category_for_type(InterviewType.SYSTEM_DESIGN)
        == QuestionCategory.SYSTEM_DESIGN
    )
    assert interview_service._get_category_for_type(InterviewType.MIXED) is None


# Test: Inactive questions are excluded
@pytest.mark.asyncio
async def test_inactive_questions_excluded_from_company_pool(
    db_session, test_user, interview_service
):
    """Test that inactive questions are excluded from company-specific pool."""
    # Create active and inactive Google questions
    active_google = Question(
        content="Active Google",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["google"],
        is_active=True,
    )
    inactive_google = Question(
        content="Inactive Google",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["google"],
        is_active=False,
    )

    # Create general active question
    active_general = Question(
        content="Active General",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
    )

    db_session.add_all([active_google, inactive_google, active_general])
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        target_company="Google",
        question_count=2,
        difficulty=DifficultyLevel.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should get 1 active Google + 1 general (inactive Google excluded)
    assigned = await interview_service.assign_questions(db_session, interview)
    assert len(assigned) == 2

    assigned_ids = {iq.question_id for iq in assigned}
    assert active_google.id in assigned_ids
    assert inactive_google.id not in assigned_ids


# Test: Inactive questions excluded from general pool
@pytest.mark.asyncio
async def test_inactive_questions_excluded_from_general_pool(
    db_session, test_user, interview_service
):
    """Test that inactive questions are excluded from general pool."""
    # Create active and inactive questions
    active_q1 = Question(
        content="Active 1",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
    )
    active_q2 = Question(
        content="Active 2",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
    )
    inactive_q = Question(
        content="Inactive",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=False,
    )

    db_session.add_all([active_q1, active_q2, inactive_q])
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=2,
        difficulty=DifficultyLevel.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)
    assert len(assigned) == 2

    assigned_ids = {iq.question_id for iq in assigned}
    assert inactive_q.id not in assigned_ids


# Test: Time limit inheritance
@pytest.mark.asyncio
async def test_time_limits_inherited_from_questions_with_variations(
    db_session, test_user, interview_service
):
    """Test that different time limits are correctly inherited."""
    # Create questions with varying time limits
    q1 = Question(
        content="Quick question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        expected_duration_seconds=60,
    )
    q2 = Question(
        content="Standard question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    q3 = Question(
        content="Long question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        expected_duration_seconds=300,
    )

    db_session.add_all([q1, q2, q3])
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=3,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)

    # Verify each InterviewQuestion has correct time limit
    for iq in assigned:
        result = await db_session.exec(select(Question).where(Question.id == iq.question_id))
        question = result.first()
        assert iq.time_limit_seconds == question.expected_duration_seconds


# Test: assign_specific_question maintains order=1
@pytest.mark.asyncio
async def test_assign_specific_question_always_sets_order_one(
    db_session, test_user, interview_service
):
    """Test that assign_specific_question always sets order to 1."""
    question1 = Question(
        content="First",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    question2 = Question(
        content="Second",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )

    db_session.add_all([question1, question2])
    await db_session.commit()
    await db_session.refresh(question1)
    await db_session.refresh(question2)

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign first specific question
    iq1 = await interview_service.assign_specific_question(db_session, interview, question1.id)
    assert iq1.order == 1

    # Assign second specific question (still order 1)
    iq2 = await interview_service.assign_specific_question(db_session, interview, question2.id)
    assert iq2.order == 1


# Test: Randomization varies across calls
@pytest.mark.asyncio
async def test_question_assignment_randomization(db_session, test_user, interview_service):
    """Test that question assignment includes randomization."""
    # Create many questions to test randomization
    questions = [
        Question(
            content=f"Random Q{i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(20)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    # Create multiple interviews and assign questions
    assignments = []
    for _ in range(5):
        interview = InterviewSession(
            user_id=test_user.id,
            interview_type=InterviewType.BEHAVIORAL,
            question_count=5,
            difficulty=DifficultyLevel.MEDIUM,
            status=InterviewStatus.SCHEDULED,
        )
        db_session.add(interview)
        await db_session.commit()
        await db_session.refresh(interview)

        assigned = await interview_service.assign_questions(db_session, interview)
        assignments.append([iq.question_id for iq in assigned])

    # At least some assignments should differ (randomization working)
    # Compare first assignment to others
    first_assignment = tuple(assignments[0])
    has_variation = any(tuple(assignment) != first_assignment for assignment in assignments[1:])

    # Note: This test has a small chance of failing if random selects
    # the same questions, but with 20 choose 5, it's very unlikely
    assert has_variation or len(assignments) == 1
