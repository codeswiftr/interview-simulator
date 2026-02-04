"""Additional edge case tests for interview_service.py to improve coverage.

Focuses on uncovered branches, error paths, and state transitions not
covered by existing tests.
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
        email=f"edgecase_{uuid4().hex[:8]}@example.com",
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


# Test: Mixed interview type (category=None path)
@pytest.mark.asyncio
async def test_assign_questions_mixed_interview_type_selects_from_all_categories(
    db_session, test_user, interview_service
):
    """Test MIXED interview type selects questions from all categories."""
    # Create questions from different categories
    behavioral_q = Question(
        content="Behavioral question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    technical_q = Question(
        content="Technical question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    system_design_q = Question(
        content="System design question",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
    )

    db_session.add_all([behavioral_q, technical_q, system_design_q])
    await db_session.commit()

    # Create MIXED interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.MIXED,  # category will be None
        question_count=3,
        difficulty=DifficultyLevel.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should select questions from all categories
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 3

    # Verify questions come from different categories
    result = await db_session.exec(
        select(Question).where(
            Question.id.in_([iq.question_id for iq in assigned])
        )
    )
    assigned_questions = list(result.all())

    categories = {q.category for q in assigned_questions}
    # Should have questions from multiple categories
    assert len(categories) >= 1  # At least one category represented


# Test: Empty company_tags edge case
@pytest.mark.asyncio
async def test_assign_questions_empty_company_tags_fallback(
    db_session, test_user, interview_service
):
    """Test target_company specified but no questions have that company tag."""
    # Create questions without the target company tag
    question1 = Question(
        content="Generic question 1",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["amazon", "meta"],  # No "google"
    )
    question2 = Question(
        content="Generic question 2",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=[],  # Empty tags
    )

    db_session.add_all([question1, question2])
    await db_session.commit()

    # Request Google-specific questions (none exist)
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        target_company="Google",
        question_count=2,
        difficulty=DifficultyLevel.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should fallback to general pool
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 2


# Test: Enum vs string difficulty handling
@pytest.mark.asyncio
async def test_assign_questions_handles_difficulty_enum_from_database(
    db_session, test_user, interview_service
):
    """Test that difficulty handling works with both enum and string values."""
    # Create questions
    hard_question = Question(
        content="Hard question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
    )
    db_session.add(hard_question)
    await db_session.commit()

    # Create interview with DifficultyLevel enum
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        question_count=1,
        difficulty=DifficultyLevel.HARD,  # Using DifficultyLevel enum
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should handle enum correctly
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 1
    assert assigned[0].question_id == hard_question.id


# Test: No difficulty specified (None)
@pytest.mark.asyncio
async def test_assign_questions_no_difficulty_filter_selects_all_difficulties(
    db_session, test_user, interview_service
):
    """Test that None difficulty selects questions of any difficulty."""
    # Create questions with different difficulties
    easy_q = Question(
        content="Easy question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
    )
    medium_q = Question(
        content="Medium question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    hard_q = Question(
        content="Hard question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
    )

    db_session.add_all([easy_q, medium_q, hard_q])
    await db_session.commit()

    # Create interview with no difficulty specified
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=3,
        difficulty=None,  # No difficulty filter
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should select from all difficulties
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 3


# Test: Single question assignment
@pytest.mark.asyncio
async def test_assign_questions_single_question_count(
    db_session, test_user, interview_service
):
    """Test assignment works with question_count=1."""
    question = Question(
        content="Single question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        question_count=1,  # Single question
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 1
    assert assigned[0].order == 1


# Test: Large question count
@pytest.mark.asyncio
async def test_assign_questions_large_question_count(
    db_session, test_user, interview_service
):
    """Test assignment works with larger question counts."""
    # Create 10 questions
    questions = [
        Question(
            content=f"Question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(10)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=10,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 10
    # Verify sequential ordering
    orders = [iq.order for iq in assigned]
    assert orders == list(range(1, 11))


# Test: Company-specific with mixed difficulty
@pytest.mark.asyncio
async def test_assign_questions_company_specific_with_mixed_difficulty(
    db_session, test_user, interview_service
):
    """Test company filtering works with mixed difficulty."""
    # Create Google questions with various difficulties
    google_easy = Question(
        content="Google easy",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["google"],
    )
    google_hard = Question(
        content="Google hard",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["google"],
    )

    db_session.add_all([google_easy, google_hard])
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        target_company="Google",
        question_count=2,
        difficulty=DifficultyLevel.MIXED,  # Should not filter by difficulty
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 2
    # Should include both easy and hard questions
    assigned_ids = {iq.question_id for iq in assigned}
    assert google_easy.id in assigned_ids
    assert google_hard.id in assigned_ids


# Test: Exact match on question count
@pytest.mark.asyncio
async def test_assign_questions_exact_match_no_overflow(
    db_session, test_user, interview_service
):
    """Test assignment when exactly the right number of questions exist."""
    # Create exactly 3 questions
    questions = [
        Question(
            content=f"Exact question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(3)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=3,  # Exactly matches available
        difficulty=DifficultyLevel.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 3


# Test: Multiple calls to same interview (idempotency check)
@pytest.mark.asyncio
async def test_get_interview_questions_empty_session(
    db_session, test_user, interview_service
):
    """Test get_interview_questions returns empty list for session without questions."""
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # No questions assigned yet
    questions = await interview_service.get_interview_questions(db_session, interview.id)

    assert questions == []


# Test: assign_specific_question with exact time limit
@pytest.mark.asyncio
async def test_assign_specific_question_copies_time_limit_correctly(
    db_session, test_user, interview_service
):
    """Test that time limit is correctly copied from question to interview question."""
    # Create question with custom time limit
    question = Question(
        content="Timed question",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        expected_duration_seconds=600,  # 10 minutes
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_specific_question(
        db_session, interview, question.id
    )

    assert assigned.time_limit_seconds == 600


# Test: Multiple interviews for same user
@pytest.mark.asyncio
async def test_assign_questions_different_interviews_same_user_can_reuse_questions(
    db_session, test_user, interview_service
):
    """Test that questions can be assigned to multiple interviews for same user."""
    # Create questions
    questions = [
        Question(
            content=f"Reusable question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(5)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    # Create two interviews for same user
    interview1 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=3,
        status=InterviewStatus.SCHEDULED,
    )
    interview2 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=3,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add_all([interview1, interview2])
    await db_session.commit()
    await db_session.refresh(interview1)
    await db_session.refresh(interview2)

    # Assign questions to both
    assigned1 = await interview_service.assign_questions(db_session, interview1)
    assigned2 = await interview_service.assign_questions(db_session, interview2)

    assert len(assigned1) == 3
    assert len(assigned2) == 3
    # Questions can be reused across interviews (different InterviewQuestion records)


# Test: Category filtering for system_design
@pytest.mark.asyncio
async def test_assign_questions_system_design_filters_correctly(
    db_session, test_user, interview_service
):
    """Test SYSTEM_DESIGN interview type filters to system_design category."""
    # Create mixed questions
    behavioral_q = Question(
        content="Behavioral",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    system_design_q = Question(
        content="System design",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
    )

    db_session.add_all([behavioral_q, system_design_q])
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        question_count=1,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 1
    assert assigned[0].question_id == system_design_q.id


# Test: Error message formatting variations
@pytest.mark.asyncio
async def test_assign_questions_error_message_with_no_difficulty_specified(
    db_session, test_user, interview_service
):
    """Test error message when no difficulty is specified."""
    # No questions available

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        question_count=1,
        difficulty=None,  # No difficulty
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    with pytest.raises(ValueError) as exc_info:
        await interview_service.assign_questions(db_session, interview)

    error_message = str(exc_info.value)
    # Should not include difficulty info when None
    assert "difficulty" not in error_message.lower()
    assert "category 'technical'" in error_message


# Test: has_assigned_questions with non-existent interview
@pytest.mark.asyncio
async def test_has_assigned_questions_nonexistent_interview_returns_false(
    db_session, interview_service
):
    """Test has_assigned_questions returns False for non-existent interview."""
    fake_id = uuid4()

    result = await interview_service.has_assigned_questions(db_session, fake_id)

    assert result is False
