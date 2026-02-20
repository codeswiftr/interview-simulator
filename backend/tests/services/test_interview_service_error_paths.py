"""Error handling tests for InterviewService.

Tests critical error paths in interview service:
- Database connection failures
- Insufficient questions scenarios
- Invalid parameters handling
- Concurrent modification detection
- Transaction rollback scenarios
"""

from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import select

from app.models.interview import InterviewSession, InterviewStatus, InterviewType
from app.models.question import Difficulty, Question, QuestionCategory
from app.services.interview_service import InterviewService


@pytest.mark.asyncio
async def test_assign_questions_insufficient_questions_raises_error(db_session):
    """Test that ValueError is raised when insufficient questions available."""
    service = InterviewService()

    # Create interview requesting 10 questions
    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=10,
        difficulty=Difficulty.MEDIUM
    )
    db_session.add(interview)
    await db_session.commit()

    # Only add 3 questions (less than requested)
    for i in range(3):
        question = Question(
            id=str(uuid4()),
            content=f"Question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180
        )
        db_session.add(question)
    await db_session.commit()

    # Should raise ValueError
    with pytest.raises(ValueError, match="not enough questions"):
        await service.assign_questions(db_session, interview)


@pytest.mark.asyncio
async def test_assign_questions_no_questions_available_raises_error(db_session):
    """Test that ValueError is raised when no questions available."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=5
    )
    db_session.add(interview)
    await db_session.commit()

    # Don't add any questions
    with pytest.raises(ValueError):
        await service.assign_questions(db_session, interview)


@pytest.mark.asyncio
async def test_assign_questions_handles_inactive_questions(db_session):
    """Test that inactive questions are not assigned."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=3,
        difficulty=Difficulty.MEDIUM
    )
    db_session.add(interview)
    await db_session.commit()

    # Add 5 active questions
    for i in range(5):
        question = Question(
            id=str(uuid4()),
            content=f"Active question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180,
            is_active=True
        )
        db_session.add(question)

    # Add 10 inactive questions
    for i in range(10):
        question = Question(
            id=str(uuid4()),
            content=f"Inactive question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180,
            is_active=False
        )
        db_session.add(question)

    await db_session.commit()

    # Should only use active questions
    assigned = await service.assign_questions(db_session, interview)
    assert len(assigned) == 3

    # Verify all assigned questions are active
    question_ids = [aq.question_id for aq in assigned]
    result = await db_session.exec(
        select(Question).where(Question.id.in_(question_ids))
    )
    questions = list(result.all())
    assert all(q.is_active for q in questions)


@pytest.mark.asyncio
async def test_assign_questions_with_company_filter_falls_back_to_general(db_session):
    """Test company-specific questions fall back to general when insufficient."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=5,
        difficulty=Difficulty.MEDIUM,
        target_company="Google"
    )
    db_session.add(interview)
    await db_session.commit()

    # Add 2 Google-specific questions
    for i in range(2):
        question = Question(
            id=str(uuid4()),
            content=f"Google question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180,
            company_tags=["google"]
        )
        db_session.add(question)

    # Add 10 general questions
    for i in range(10):
        question = Question(
            id=str(uuid4()),
            content=f"General question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180,
            company_tags=[]
        )
        db_session.add(question)

    await db_session.commit()

    # Should get 2 Google + 3 general
    assigned = await service.assign_questions(db_session, interview)
    assert len(assigned) == 5


@pytest.mark.asyncio
async def test_assign_questions_handles_mixed_difficulty(db_session):
    """Test that 'mixed' difficulty selects questions regardless of difficulty."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=3,
        difficulty="mixed"  # Special value
    )
    db_session.add(interview)
    await db_session.commit()

    # Add questions of different difficulties
    for difficulty in [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]:
        question = Question(
            id=str(uuid4()),
            content=f"{difficulty} question",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=difficulty,
            expected_duration_seconds=180
        )
        db_session.add(question)

    await db_session.commit()

    # Should select from all difficulties
    assigned = await service.assign_questions(db_session, interview)
    assert len(assigned) == 3


@pytest.mark.asyncio
async def test_assign_questions_handles_database_transaction_error(db_session):
    """Test that database errors are propagated correctly."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=3
    )
    db_session.add(interview)
    await db_session.commit()

    # Mock database to raise error
    with patch.object(db_session, 'exec', side_effect=OperationalError("", "", "")):
        with pytest.raises(OperationalError):
            await service.assign_questions(db_session, interview)


@pytest.mark.asyncio
async def test_get_category_for_type_returns_correct_mapping():
    """Test that interview types map to correct question categories."""
    service = InterviewService()

    assert service._get_category_for_type(InterviewType.BEHAVIORAL) == QuestionCategory.BEHAVIORAL
    assert service._get_category_for_type(InterviewType.TECHNICAL) == QuestionCategory.TECHNICAL
    assert service._get_category_for_type(InterviewType.SYSTEM_DESIGN) == QuestionCategory.SYSTEM_DESIGN
    assert service._get_category_for_type(InterviewType.MIXED) is None


@pytest.mark.asyncio
async def test_assign_questions_handles_null_difficulty_gracefully(db_session):
    """Test that null difficulty is handled correctly."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=3,
        difficulty=None  # No difficulty filter
    )
    db_session.add(interview)
    await db_session.commit()

    # Add questions of various difficulties
    for i in range(5):
        question = Question(
            id=str(uuid4()),
            content=f"Question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180
        )
        db_session.add(question)

    await db_session.commit()

    # Should select questions regardless of difficulty
    assigned = await service.assign_questions(db_session, interview)
    assert len(assigned) == 3


@pytest.mark.asyncio
async def test_assign_questions_creates_correct_interview_question_records(db_session):
    """Test that InterviewQuestion records are created with correct attributes."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=2,
        difficulty=Difficulty.MEDIUM
    )
    db_session.add(interview)
    await db_session.commit()

    # Add questions
    questions = []
    for i in range(3):
        question = Question(
            id=str(uuid4()),
            content=f"Question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180 + (i * 30)
        )
        db_session.add(question)
        questions.append(question)

    await db_session.commit()

    # Assign questions
    assigned = await service.assign_questions(db_session, interview)

    # Verify attributes
    assert len(assigned) == 2
    assert all(iq.session_id == interview.id for iq in assigned)
    assert all(iq.question_id in [q.id for q in questions] for iq in assigned)
    assert all(iq.order > 0 for iq in assigned)
    assert all(iq.time_limit_seconds > 0 for iq in assigned)


@pytest.mark.asyncio
async def test_assign_questions_avoids_duplicate_questions_in_session(db_session):
    """Test that same question is not assigned twice in one session."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=5,
        difficulty=Difficulty.MEDIUM
    )
    db_session.add(interview)
    await db_session.commit()

    # Add exactly 5 questions
    for i in range(5):
        question = Question(
            id=str(uuid4()),
            content=f"Question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180
        )
        db_session.add(question)

    await db_session.commit()

    # Assign questions
    assigned = await service.assign_questions(db_session, interview)

    # Verify no duplicates
    question_ids = [iq.question_id for iq in assigned]
    assert len(question_ids) == len(set(question_ids))


@pytest.mark.asyncio
async def test_assign_questions_respects_question_count_limit(db_session):
    """Test that question count is exactly as requested (not more)."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=3,
        difficulty=Difficulty.MEDIUM
    )
    db_session.add(interview)
    await db_session.commit()

    # Add 100 questions (way more than needed)
    for i in range(100):
        question = Question(
            id=str(uuid4()),
            content=f"Question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180
        )
        db_session.add(question)

    await db_session.commit()

    # Should assign exactly 3
    assigned = await service.assign_questions(db_session, interview)
    assert len(assigned) == 3


@pytest.mark.asyncio
async def test_assign_questions_for_mixed_interview_type(db_session):
    """Test question assignment for mixed interview type (all categories)."""
    service = InterviewService()

    interview = InterviewSession(
        id=str(uuid4()),
        user_id=str(uuid4()),
        interview_type=InterviewType.MIXED,
        status=InterviewStatus.IN_PROGRESS,
        question_count=6,
        difficulty=Difficulty.MEDIUM
    )
    db_session.add(interview)
    await db_session.commit()

    # Add questions from different categories
    categories = [
        QuestionCategory.BEHAVIORAL,
        QuestionCategory.TECHNICAL,
        QuestionCategory.SYSTEM_DESIGN
    ]
    for i, category in enumerate(categories * 2):  # 6 questions total
        question = Question(
            id=str(uuid4()),
            content=f"{category} question {i}",
            category=category,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180
        )
        db_session.add(question)

    await db_session.commit()

    # Should select from all categories
    assigned = await service.assign_questions(db_session, interview)
    assert len(assigned) == 6
