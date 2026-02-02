"""Unit tests for InterviewService."""

from uuid import uuid4
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.interview_service import InterviewService
from app.models.interview import InterviewSession, InterviewType, InterviewQuestion
from app.models.question import Question, QuestionCategory

@pytest.fixture
def service():
    return InterviewService()

@pytest.mark.asyncio
async def test_get_category_for_type(service):
    """Test mapping interview type to question category."""
    assert service._get_category_for_type(InterviewType.BEHAVIORAL) == QuestionCategory.BEHAVIORAL
    assert service._get_category_for_type(InterviewType.TECHNICAL) == QuestionCategory.TECHNICAL
    assert service._get_category_for_type(InterviewType.SYSTEM_DESIGN) == QuestionCategory.SYSTEM_DESIGN
    assert service._get_category_for_type(InterviewType.MIXED) is None
    assert service._get_category_for_type("unknown") is None

@pytest.mark.asyncio
async def test_assign_questions_insufficient_questions(service):
    """Test raising ValueError when not enough questions available."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.BEHAVIORAL
    mock_interview.question_count = 5
    mock_interview.difficulty = "easy"
    mock_interview.target_company = None

    # Mock DB response to return 0 questions
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    with pytest.raises(ValueError) as exc_info:
        await service.assign_questions(mock_session, mock_interview)
    
    assert "Not enough questions available" in str(exc_info.value)
    assert "difficulty 'easy'" in str(exc_info.value)

@pytest.mark.asyncio
async def test_assign_questions_insufficient_mixed_category_message(service):
    """Test error message when category is mixed and difficulty is mixed."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.MIXED
    mock_interview.question_count = 3
    mock_interview.difficulty = "mixed"
    mock_interview.target_company = None

    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    with pytest.raises(ValueError) as exc_info:
        await service.assign_questions(mock_session, mock_interview)

    message = str(exc_info.value)
    assert "category 'mixed'" in message
    assert "difficulty" not in message

@pytest.mark.asyncio
async def test_assign_questions_company_pool_sufficient(service):
    """Test company-specific pool fulfills request without general pool fallback."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.TECHNICAL
    mock_interview.question_count = 1
    mock_interview.difficulty = "medium"
    mock_interview.target_company = "Meta"

    q1 = Question(id=uuid4(), expected_duration_seconds=150)
    mock_result_company = MagicMock()
    mock_result_company.all.return_value = [q1]
    mock_session.exec.return_value = mock_result_company

    result = await service.assign_questions(mock_session, mock_interview)

    assert len(result) == 1
    assert result[0].question_id == q1.id
    assert result[0].time_limit_seconds == 150
    assert mock_session.exec.call_count == 1

@pytest.mark.asyncio
async def test_assign_questions_general_only_with_no_difficulty(service):
    """Test assigning questions with no target company and no difficulty filter."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.MIXED
    mock_interview.question_count = 2
    mock_interview.difficulty = None
    mock_interview.target_company = None

    q1 = Question(id=uuid4(), expected_duration_seconds=120)
    q2 = Question(id=uuid4(), expected_duration_seconds=200)
    mock_result_general = MagicMock()
    mock_result_general.all.return_value = [q1, q2]
    mock_session.exec.return_value = mock_result_general

    result = await service.assign_questions(mock_session, mock_interview)

    assert len(result) == 2
    assert result[0].order == 1
    assert result[1].order == 2
    assert result[0].time_limit_seconds == 120
    assert result[1].time_limit_seconds == 200
    assert mock_session.add.call_count == 2

@pytest.mark.asyncio
async def test_assign_questions_company_fallback_excludes_duplicates(service):
    """Test fallback to general pool when company pool insufficient."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.BEHAVIORAL
    mock_interview.question_count = 2
    mock_interview.difficulty = "easy"
    mock_interview.target_company = "Netflix"

    q1 = Question(id=uuid4(), expected_duration_seconds=180)
    q2 = Question(id=uuid4(), expected_duration_seconds=180)

    mock_result_company = MagicMock()
    mock_result_company.all.return_value = [q1]
    mock_result_general = MagicMock()
    mock_result_general.all.return_value = [q2]

    mock_session.exec.side_effect = [mock_result_company, mock_result_general]

    result = await service.assign_questions(mock_session, mock_interview)

    assert [iq.question_id for iq in result] == [q1.id, q2.id]
    assert mock_session.exec.call_count == 2

@pytest.mark.asyncio
async def test_assign_questions_with_target_company(service):
    """Test assigning questions with a target company."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.TECHNICAL
    mock_interview.question_count = 2
    mock_interview.difficulty = "medium"
    mock_interview.target_company = "Google"

    # Mock questions
    q1 = Question(id=uuid4(), expected_duration_seconds=180)
    q2 = Question(id=uuid4(), expected_duration_seconds=180)

    # First call (company pool) returns 1 question
    # Second call (general pool) returns 1 question
    mock_result_company = MagicMock()
    mock_result_company.all.return_value = [q1]
    
    mock_result_general = MagicMock()
    mock_result_general.all.return_value = [q2]
    
    mock_session.exec.side_effect = [mock_result_company, mock_result_general]

    result = await service.assign_questions(mock_session, mock_interview)

    assert len(result) == 2
    assert result[0].question_id == q1.id
    assert result[1].question_id == q2.id
    assert mock_session.add.call_count == 2

@pytest.mark.asyncio
async def test_get_interview_questions(service):
    """Test retrieving assigned questions."""
    mock_session = AsyncMock()
    interview_id = uuid4()
    
    q1 = Question(id=uuid4())
    mock_result = MagicMock()
    mock_result.all.return_value = [q1]
    mock_session.exec.return_value = mock_result

    result = await service.get_interview_questions(mock_session, interview_id)
    
    assert len(result) == 1
    assert result[0].id == q1.id

@pytest.mark.asyncio
async def test_has_assigned_questions(service):
    """Test checking if questions are assigned."""
    mock_session = AsyncMock()
    interview_id = uuid4()
    
    mock_result = MagicMock()
    mock_result.one.return_value = 1
    mock_session.exec.return_value = mock_result

    assert await service.has_assigned_questions(mock_session, interview_id) is True

@pytest.mark.asyncio
async def test_has_assigned_questions_false(service):
    """Test checking when no questions are assigned."""
    mock_session = AsyncMock()
    interview_id = uuid4()

    mock_result = MagicMock()
    mock_result.one.return_value = 0
    mock_session.exec.return_value = mock_result

    assert await service.has_assigned_questions(mock_session, interview_id) is False

@pytest.mark.asyncio
async def test_assign_specific_question_success(service):
    """Test assigning a specific question successfully."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    mock_interview.id = uuid4()
    question_id = uuid4()
    
    q1 = Question(id=question_id, expected_duration_seconds=120)
    mock_result = MagicMock()
    mock_result.first.return_value = q1
    mock_session.exec.return_value = mock_result

    result = await service.assign_specific_question(mock_session, mock_interview, question_id)
    
    assert result.question_id == question_id
    assert result.session_id == mock_interview.id
    assert mock_session.add.called
    mock_session.flush.assert_awaited()

@pytest.mark.asyncio
async def test_assign_specific_question_not_found(service):
    """Test assigning a non-existent or inactive question."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_interview = MagicMock()
    question_id = uuid4()

    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(ValueError, match="Question not found"):
        await service.assign_specific_question(mock_session, mock_interview, question_id)


# ==================== Integration Tests ====================
# These tests use real database interactions to verify service behavior


@pytest.mark.asyncio
async def test_assign_questions_integration_behavioral(db_session, test_user, service):
    """Integration test: Assign behavioral questions to an interview session."""
    from app.models.interview import InterviewSession, InterviewType, DifficultyLevel
    from app.models.question import Question, QuestionCategory, Difficulty

    # Create test questions
    for i in range(5):
        question = Question(
            content=f"Behavioral question {i+1}",
            category=QuestionCategory.BEHAVIORAL.value,
            difficulty=Difficulty.MEDIUM.value,
            expected_duration_seconds=180,
            is_active=True
        )
        db_session.add(question)
    await db_session.commit()

    # Create interview session
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL.value,
        question_count=3,
        difficulty=DifficultyLevel.MEDIUM.value
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions
    assigned = await service.assign_questions(db_session, interview)

    assert len(assigned) == 3
    assert all(iq.session_id == interview.id for iq in assigned)
    assert all(iq.time_limit_seconds == 180 for iq in assigned)
    assert assigned[0].order == 1
    assert assigned[2].order == 3


@pytest.mark.asyncio
async def test_assign_questions_integration_mixed_interview(db_session, test_user, service):
    """Integration test: Assign questions for mixed interview type."""
    from app.models.interview import InterviewSession, InterviewType
    from app.models.question import Question, QuestionCategory, Difficulty

    # Create mixed questions
    categories = [QuestionCategory.BEHAVIORAL, QuestionCategory.TECHNICAL, QuestionCategory.SYSTEM_DESIGN]
    for i, category in enumerate(categories * 2):
        question = Question(
            content=f"{category.value} question {i+1}",
            category=category.value,
            difficulty=Difficulty.MEDIUM.value,
            expected_duration_seconds=180,
            is_active=True
        )
        db_session.add(question)
    await db_session.commit()

    # Create mixed interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.MIXED.value,
        question_count=4
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions - should pull from all categories
    assigned = await service.assign_questions(db_session, interview)

    assert len(assigned) == 4
    # Verify questions are properly ordered
    orders = [iq.order for iq in assigned]
    assert orders == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_assign_questions_integration_company_specific(db_session, test_user, service):
    """Integration test: Assign company-specific questions."""
    from app.models.interview import InterviewSession, InterviewType, DifficultyLevel
    from app.models.question import Question, QuestionCategory, Difficulty

    # Create Google-specific questions
    for i in range(3):
        question = Question(
            content=f"Google technical question {i+1}",
            category=QuestionCategory.TECHNICAL.value,
            difficulty=Difficulty.MEDIUM.value,
            company_tags=["google", "faang"],
            expected_duration_seconds=180,
            is_active=True
        )
        db_session.add(question)

    # Create general technical questions
    for i in range(3):
        question = Question(
            content=f"General technical question {i+1}",
            category=QuestionCategory.TECHNICAL.value,
            difficulty=Difficulty.MEDIUM.value,
            expected_duration_seconds=180,
            is_active=True
        )
        db_session.add(question)
    await db_session.commit()

    # Create interview targeting Google
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL.value,
        target_company="Google",
        question_count=5,
        difficulty=DifficultyLevel.MEDIUM.value
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign questions - should prioritize Google questions
    assigned = await service.assign_questions(db_session, interview)

    assert len(assigned) == 5
    # First 3 should be Google-specific, remaining from general pool
    questions = await service.get_interview_questions(db_session, interview.id)
    google_questions = [q for q in questions if "google" in q.company_tags]
    assert len(google_questions) >= 3


@pytest.mark.asyncio
async def test_assign_questions_integration_insufficient_questions(db_session, test_user, service):
    """Integration test: Handle insufficient questions gracefully."""
    from app.models.interview import InterviewSession, InterviewType
    from app.models.question import Question, QuestionCategory, Difficulty

    # Create only 2 technical questions
    for i in range(2):
        question = Question(
            content=f"Technical question {i+1}",
            category=QuestionCategory.TECHNICAL.value,
            difficulty=Difficulty.HARD.value,
            expected_duration_seconds=180,
            is_active=True
        )
        db_session.add(question)
    await db_session.commit()

    # Request 5 questions
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL.value,
        question_count=5
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await service.assign_questions(db_session, interview)

    assert "Not enough questions available" in str(exc_info.value)
    assert "Requested 5, found 2" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_interview_questions_integration(db_session, test_user, service):
    """Integration test: Retrieve questions in correct order."""
    from app.models.interview import InterviewSession, InterviewType, InterviewQuestion
    from app.models.question import Question, QuestionCategory, Difficulty

    # Create questions
    q1 = Question(content="Q1", category=QuestionCategory.BEHAVIORAL.value, difficulty=Difficulty.EASY.value, is_active=True)
    q2 = Question(content="Q2", category=QuestionCategory.BEHAVIORAL.value, difficulty=Difficulty.MEDIUM.value, is_active=True)
    q3 = Question(content="Q3", category=QuestionCategory.BEHAVIORAL.value, difficulty=Difficulty.HARD.value, is_active=True)
    db_session.add_all([q1, q2, q3])
    await db_session.commit()
    await db_session.refresh(q1)
    await db_session.refresh(q2)
    await db_session.refresh(q3)

    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL.value,
        question_count=3
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Manually assign questions in specific order
    iq1 = InterviewQuestion(session_id=interview.id, question_id=q3.id, order=1, time_limit_seconds=180)
    iq2 = InterviewQuestion(session_id=interview.id, question_id=q1.id, order=2, time_limit_seconds=180)
    iq3 = InterviewQuestion(session_id=interview.id, question_id=q2.id, order=3, time_limit_seconds=180)
    db_session.add_all([iq1, iq2, iq3])
    await db_session.commit()

    # Retrieve questions
    questions = await service.get_interview_questions(db_session, interview.id)

    assert len(questions) == 3
    assert questions[0].id == q3.id
    assert questions[1].id == q1.id
    assert questions[2].id == q2.id


@pytest.mark.asyncio
async def test_has_assigned_questions_integration(db_session, test_user, service):
    """Integration test: Check if interview has assigned questions."""
    from app.models.interview import InterviewSession, InterviewType, InterviewQuestion
    from app.models.question import Question, QuestionCategory

    # Create interview without questions
    interview1 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL.value,
        question_count=1
    )
    db_session.add(interview1)

    # Create interview with questions
    interview2 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL.value,
        question_count=1
    )
    db_session.add(interview2)
    await db_session.commit()
    await db_session.refresh(interview1)
    await db_session.refresh(interview2)

    # Add question to interview2
    question = Question(content="Test Q", category=QuestionCategory.TECHNICAL.value, is_active=True)
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    iq = InterviewQuestion(session_id=interview2.id, question_id=question.id, order=1, time_limit_seconds=180)
    db_session.add(iq)
    await db_session.commit()

    # Check both interviews
    assert await service.has_assigned_questions(db_session, interview1.id) is False
    assert await service.has_assigned_questions(db_session, interview2.id) is True


@pytest.mark.asyncio
async def test_assign_specific_question_integration(db_session, test_user, service):
    """Integration test: Assign a specific question for quick practice."""
    from app.models.interview import InterviewSession, InterviewType
    from app.models.question import Question, QuestionCategory, Difficulty

    # Create questions
    q1 = Question(
        content="Specific practice question",
        category=QuestionCategory.BEHAVIORAL.value,
        difficulty=Difficulty.MEDIUM.value,
        expected_duration_seconds=120,
        is_active=True
    )
    db_session.add(q1)
    await db_session.commit()
    await db_session.refresh(q1)

    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL.value,
        question_count=1
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Assign specific question
    assigned = await service.assign_specific_question(db_session, interview, q1.id)

    assert assigned.question_id == q1.id
    assert assigned.session_id == interview.id
    assert assigned.order == 1
    assert assigned.time_limit_seconds == 120

    # Verify it's persisted
    questions = await service.get_interview_questions(db_session, interview.id)
    assert len(questions) == 1
    assert questions[0].id == q1.id


@pytest.mark.asyncio
async def test_assign_specific_question_integration_inactive(db_session, test_user, service):
    """Integration test: Cannot assign inactive question."""
    from app.models.interview import InterviewSession, InterviewType
    from app.models.question import Question, QuestionCategory

    # Create inactive question
    q1 = Question(
        content="Inactive question",
        category=QuestionCategory.BEHAVIORAL.value,
        is_active=False
    )
    db_session.add(q1)
    await db_session.commit()
    await db_session.refresh(q1)

    # Create interview
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL.value,
        question_count=1
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    # Should fail to assign inactive question
    with pytest.raises(ValueError, match="Question not found or is inactive"):
        await service.assign_specific_question(db_session, interview, q1.id)
