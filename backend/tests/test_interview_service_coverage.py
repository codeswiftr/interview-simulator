"""Comprehensive service-level tests for interview_service.py to improve coverage.

This test module specifically targets coverage gaps in assign_questions():
- Company-specific filtering (line 79)
- Fallback pool logic (lines 88, 105)
- Error handling for insufficient questions (lines 110-119)
- InterviewQuestion record creation (lines 126-135)
"""

from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.interview import (
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.interview_service import InterviewService

# Use shared fixtures from conftest.py (db_session, clean_database, etc.)


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email="testuser@example.com",
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


# Test: Company-specific filtering (line 79)


@pytest.mark.asyncio
async def test_assign_questions_with_company_tags_filters_correctly(
    db_session, test_user, interview_service
):
    """Test that assign_questions filters by company_tags when target_company is specified."""
    # Create questions with different company tags
    google_question1 = Question(
        content="Google behavioral question 1",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["google", "faang"],
    )
    google_question2 = Question(
        content="Google behavioral question 2",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["google"],
    )
    amazon_question = Question(
        content="Amazon behavioral question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["amazon", "faang"],
    )
    general_question = Question(
        content="General behavioral question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=[],
    )

    db_session.add_all([google_question1, google_question2, amazon_question, general_question])
    await db_session.commit()

    # Create interview targeting Google
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        target_company="Google",  # Should filter by "google" (lowercased)
        question_count=2,
        difficulty=Difficulty.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions
    assigned = await interview_service.assign_questions(db_session, interview)

    # Verify we got 2 questions
    assert len(assigned) == 2

    # Verify all assigned questions have 'google' in company_tags
    result = await db_session.exec(
        select(Question).where(Question.id.in_([iq.question_id for iq in assigned]))
    )
    assigned_questions = list(result.all())

    for question in assigned_questions:
        assert "google" in question.company_tags, f"Expected 'google' in {question.company_tags}"


@pytest.mark.asyncio
async def test_assign_questions_company_filtering_case_insensitive(
    db_session, test_user, interview_service
):
    """Test that company filtering is case-insensitive (target_company lowercased)."""
    # Create questions with lowercase company tag
    microsoft_question = Question(
        content="Microsoft technical question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["microsoft"],
    )
    db_session.add(microsoft_question)
    await db_session.commit()

    # Create interview with UPPERCASE target_company
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        target_company="MICROSOFT",  # Should be lowercased to "microsoft"
        question_count=1,
        difficulty=Difficulty.HARD,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should successfully find the question despite case difference
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 1
    assert assigned[0].question_id == microsoft_question.id


# Test: Fallback pool logic (lines 88, 105)


@pytest.mark.asyncio
async def test_assign_questions_fallback_to_general_pool_when_insufficient_company_questions(
    db_session, test_user, interview_service
):
    """Test that assign_questions falls back to general pool when company-specific questions run out."""
    # Create only 2 Google questions
    google_question1 = Question(
        content="Google question 1",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["google"],
    )
    google_question2 = Question(
        content="Google question 2",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["google"],
    )

    # Create 3 general questions
    general_question1 = Question(
        content="General question 1",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    general_question2 = Question(
        content="General question 2",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    general_question3 = Question(
        content="General question 3",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )

    db_session.add_all(
        [
            google_question1,
            google_question2,
            general_question1,
            general_question2,
            general_question3,
        ]
    )
    await db_session.commit()

    # Request 5 questions for Google (but only 2 exist with Google tag)
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        target_company="Google",
        question_count=5,
        difficulty=Difficulty.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should successfully assign 5 questions (2 Google + 3 general)
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 5

    # Verify the 2 Google questions are included
    assigned_ids = [iq.question_id for iq in assigned]
    assert google_question1.id in assigned_ids
    assert google_question2.id in assigned_ids


@pytest.mark.asyncio
async def test_assign_questions_fallback_excludes_already_selected_questions(
    db_session, test_user, interview_service
):
    """Test that fallback pool logic excludes questions already selected from company pool."""
    # Create 1 company question and 4 general questions (one of which has company tag)
    company_question = Question(
        content="Meta specific question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["meta"],
    )

    general_questions = [
        Question(
            content=f"General technical question {i}",
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.EASY,
        )
        for i in range(4)
    ]

    db_session.add(company_question)
    db_session.add_all(general_questions)
    await db_session.commit()

    # Request 5 questions
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        target_company="Meta",
        question_count=5,
        difficulty=Difficulty.EASY,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should assign all 5 (1 company + 4 general)
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 5

    # Ensure no duplicates
    assigned_ids = [iq.question_id for iq in assigned]
    assert len(assigned_ids) == len(set(assigned_ids)), "Duplicate questions assigned"


# Test: Error handling for insufficient questions (lines 110-119)


@pytest.mark.asyncio
async def test_assign_questions_raises_error_when_not_enough_questions_available(
    db_session, test_user, interview_service
):
    """Test that assign_questions raises ValueError when not enough questions exist."""
    # Create only 2 questions
    question1 = Question(
        content="Technical question 1",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
    )
    question2 = Question(
        content="Technical question 2",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
    )
    db_session.add_all([question1, question2])
    await db_session.commit()

    # Request 5 questions (but only 2 exist)
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        question_count=5,
        difficulty=Difficulty.HARD,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await interview_service.assign_questions(db_session, interview)

    error_message = str(exc_info.value)
    assert "Not enough questions available" in error_message
    assert "Requested 5, found 2" in error_message
    assert "category 'technical'" in error_message
    assert "difficulty 'hard'" in error_message


@pytest.mark.asyncio
async def test_assign_questions_error_message_includes_category_for_specific_type(
    db_session, test_user, interview_service
):
    """Test error message includes category information for specific interview types."""
    # Create no behavioral questions

    # Request behavioral questions
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=3,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should raise ValueError with category info
    with pytest.raises(ValueError) as exc_info:
        await interview_service.assign_questions(db_session, interview)

    error_message = str(exc_info.value)
    assert "category 'behavioral'" in error_message
    assert "Requested 3, found 0" in error_message


@pytest.mark.asyncio
async def test_assign_questions_error_message_excludes_difficulty_for_mixed(
    db_session, test_user, interview_service
):
    """Test error message excludes difficulty info when difficulty is 'mixed'."""
    # Create no questions

    # Request mixed difficulty
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        question_count=1,
        difficulty="mixed",  # Should not appear in error message
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    with pytest.raises(ValueError) as exc_info:
        await interview_service.assign_questions(db_session, interview)

    error_message = str(exc_info.value)
    assert "difficulty" not in error_message.lower()
    assert "category 'system_design'" in error_message


@pytest.mark.asyncio
async def test_assign_questions_error_message_shows_mixed_category_for_mixed_interview(
    db_session, test_user, interview_service
):
    """Test error message shows 'mixed' category for MIXED interview type."""
    # Create no questions

    # Request mixed interview type
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.MIXED,
        question_count=2,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    with pytest.raises(ValueError) as exc_info:
        await interview_service.assign_questions(db_session, interview)

    error_message = str(exc_info.value)
    assert "category 'mixed'" in error_message


# Test: InterviewQuestion record creation (lines 126-135)


@pytest.mark.asyncio
async def test_assign_questions_creates_interview_question_records_with_correct_order(
    db_session, test_user, interview_service
):
    """Test that InterviewQuestion records are created with sequential order starting at 1."""
    # Create 5 questions
    questions = [
        Question(
            content=f"Question {i}",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(5)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=5,
        difficulty=Difficulty.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions
    assigned = await interview_service.assign_questions(db_session, interview)

    # Verify order starts at 1 and is sequential
    orders = sorted([iq.order for iq in assigned])
    assert orders == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_assign_questions_sets_time_limit_from_question(
    db_session, test_user, interview_service
):
    """Test that InterviewQuestion.time_limit_seconds is set from Question.expected_duration_seconds."""
    # Create questions with specific time limits
    question1 = Question(
        content="Short question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        expected_duration_seconds=120,  # 2 minutes
    )
    question2 = Question(
        content="Long question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        expected_duration_seconds=300,  # 5 minutes
    )
    db_session.add_all([question1, question2])
    await db_session.commit()

    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        question_count=2,
        difficulty=Difficulty.EASY,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions
    assigned = await interview_service.assign_questions(db_session, interview)

    # Verify time limits are set correctly
    for iq in assigned:
        result = await db_session.exec(select(Question).where(Question.id == iq.question_id))
        question = result.first()
        assert iq.time_limit_seconds == question.expected_duration_seconds


@pytest.mark.asyncio
async def test_assign_questions_creates_persisted_records_with_ids(
    db_session, test_user, interview_service
):
    """Test that InterviewQuestion records are flushed and have IDs assigned."""
    # Create 3 questions
    questions = [
        Question(
            content=f"Question {i}",
            category=QuestionCategory.SYSTEM_DESIGN,
            difficulty=Difficulty.MEDIUM,
        )
        for i in range(3)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.SYSTEM_DESIGN,
        question_count=3,
        difficulty=Difficulty.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions
    assigned = await interview_service.assign_questions(db_session, interview)

    # Verify all records have IDs (flush happened)
    for iq in assigned:
        assert iq.id is not None
        assert iq.session_id == interview.id
        assert iq.question_id is not None


# Test: Additional edge cases


@pytest.mark.asyncio
async def test_assign_questions_respects_difficulty_filter_in_company_pool(
    db_session, test_user, interview_service
):
    """Test that company-specific pool respects difficulty filter."""
    # Create Google questions with different difficulties
    easy_google = Question(
        content="Easy Google question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["google"],
    )
    hard_google = Question(
        content="Hard Google question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["google"],
    )
    db_session.add_all([easy_google, hard_google])
    await db_session.commit()

    # Request only EASY questions for Google
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        target_company="Google",
        question_count=1,
        difficulty=Difficulty.EASY,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should only assign the EASY Google question
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 1
    assert assigned[0].question_id == easy_google.id


@pytest.mark.asyncio
async def test_assign_questions_respects_difficulty_filter_in_general_pool(
    db_session, test_user, interview_service
):
    """Test that general pool fallback also respects difficulty filter."""
    # Create 1 company question (medium) and general questions (various difficulties)
    company_medium = Question(
        content="Company medium question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["stripe"],
    )
    general_medium = Question(
        content="General medium question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
    )
    general_hard = Question(
        content="General hard question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
    )

    db_session.add_all([company_medium, general_medium, general_hard])
    await db_session.commit()

    # Request 2 MEDIUM questions for Stripe
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        target_company="Stripe",
        question_count=2,
        difficulty=Difficulty.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should assign 2 medium questions (1 company + 1 general)
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 2
    assigned_ids = [iq.question_id for iq in assigned]
    assert company_medium.id in assigned_ids
    assert general_medium.id in assigned_ids
    assert general_hard.id not in assigned_ids


@pytest.mark.asyncio
async def test_assign_questions_only_selects_active_questions(
    db_session, test_user, interview_service
):
    """Test that only is_active=True questions are selected."""
    # Create active and inactive questions
    active_question = Question(
        content="Active question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=True,
    )
    inactive_question = Question(
        content="Inactive question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        is_active=False,
    )
    db_session.add_all([active_question, inactive_question])
    await db_session.commit()

    # Request 1 question
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=1,
        difficulty=Difficulty.MEDIUM,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should only select the active question
    assigned = await interview_service.assign_questions(db_session, interview)

    assert len(assigned) == 1
    assert assigned[0].question_id == active_question.id


@pytest.mark.asyncio
async def test_get_interview_questions_returns_ordered_list(
    db_session, test_user, interview_service
):
    """Test get_interview_questions returns questions in correct order."""
    # Create questions and interview
    questions = [
        Question(
            content=f"Question {i}",
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
        question_count=3,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Manually create InterviewQuestion records in specific order
    iq1 = InterviewQuestion(
        session_id=interview.id,
        question_id=questions[2].id,
        order=1,
    )
    iq2 = InterviewQuestion(
        session_id=interview.id,
        question_id=questions[0].id,
        order=2,
    )
    iq3 = InterviewQuestion(
        session_id=interview.id,
        question_id=questions[1].id,
        order=3,
    )
    db_session.add_all([iq1, iq2, iq3])
    await db_session.commit()

    # Get questions
    result = await interview_service.get_interview_questions(db_session, interview.id)

    # Verify order
    assert len(result) == 3
    assert result[0].id == questions[2].id  # order=1
    assert result[1].id == questions[0].id  # order=2
    assert result[2].id == questions[1].id  # order=3


@pytest.mark.asyncio
async def test_has_assigned_questions_returns_true_when_questions_exist(
    db_session, test_user, interview_service
):
    """Test has_assigned_questions returns True when questions are assigned."""
    # Create question and interview
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    db_session.add(question)
    await db_session.commit()

    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign question
    iq = InterviewQuestion(
        session_id=interview.id,
        question_id=question.id,
        order=1,
    )
    db_session.add(iq)
    await db_session.commit()

    # Check
    result = await interview_service.has_assigned_questions(db_session, interview.id)
    assert result is True


@pytest.mark.asyncio
async def test_has_assigned_questions_returns_false_when_no_questions(
    db_session, test_user, interview_service
):
    """Test has_assigned_questions returns False when no questions are assigned."""
    # Create interview without questions
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Check
    result = await interview_service.has_assigned_questions(db_session, interview.id)
    assert result is False


@pytest.mark.asyncio
async def test_assign_specific_question_creates_interview_question(
    db_session, test_user, interview_service
):
    """Test assign_specific_question creates InterviewQuestion record."""
    # Create question
    question = Question(
        content="Specific question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign specific question
    result = await interview_service.assign_specific_question(db_session, interview, question.id)

    assert result.session_id == interview.id
    assert result.question_id == question.id
    assert result.order == 1
    assert result.time_limit_seconds == 180


@pytest.mark.asyncio
async def test_assign_specific_question_raises_error_for_inactive_question(
    db_session, test_user, interview_service
):
    """Test assign_specific_question raises ValueError for inactive question."""
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
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Try to assign inactive question
    with pytest.raises(ValueError) as exc_info:
        await interview_service.assign_specific_question(db_session, interview, question.id)

    assert "not found or is inactive" in str(exc_info.value)


@pytest.mark.asyncio
async def test_assign_specific_question_raises_error_for_nonexistent_question(
    db_session, test_user, interview_service
):
    """Test assign_specific_question raises ValueError for non-existent question."""
    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.SCHEDULED,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Try to assign non-existent question
    fake_id = uuid4()
    with pytest.raises(ValueError) as exc_info:
        await interview_service.assign_specific_question(db_session, interview, fake_id)

    assert "not found or is inactive" in str(exc_info.value)
