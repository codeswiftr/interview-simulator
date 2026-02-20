"""Pure unit tests for InterviewService without database.

These tests mock database interactions to test the service logic directly.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.interview import InterviewSession, InterviewType
from app.models.question import Question, QuestionCategory
from app.services.interview_service import InterviewService


@pytest.fixture
def interview_service():
    """Provide InterviewService instance."""
    return InterviewService()


class TestGetCategoryForType:
    """Tests for _get_category_for_type static method."""

    def test_behavioral_maps_to_behavioral_category(self):
        """Test BEHAVIORAL type maps to BEHAVIORAL category."""
        result = InterviewService._get_category_for_type(InterviewType.BEHAVIORAL)
        assert result == QuestionCategory.BEHAVIORAL

    def test_technical_maps_to_technical_category(self):
        """Test TECHNICAL type maps to TECHNICAL category."""
        result = InterviewService._get_category_for_type(InterviewType.TECHNICAL)
        assert result == QuestionCategory.TECHNICAL

    def test_system_design_maps_to_system_design_category(self):
        """Test SYSTEM_DESIGN type maps to SYSTEM_DESIGN category."""
        result = InterviewService._get_category_for_type(InterviewType.SYSTEM_DESIGN)
        assert result == QuestionCategory.SYSTEM_DESIGN

    def test_unknown_type_returns_none(self):
        """Test unknown types return None for mixed interviews."""
        # Using a mock to test unmapped type
        result = InterviewService._get_category_for_type("unknown")
        assert result is None


class TestAssignQuestions:
    """Tests for assign_questions method with mocked database."""

    @pytest.mark.asyncio
    async def test_raises_error_when_not_enough_questions(self, interview_service):
        """Test raises ValueError when not enough questions available."""
        mock_session = AsyncMock()

        # Create mock interview
        interview = MagicMock(spec=InterviewSession)
        interview.id = uuid4()
        interview.interview_type = InterviewType.BEHAVIORAL
        interview.difficulty = "medium"
        interview.question_count = 5
        interview.target_company = None

        # Mock exec to return empty list (no questions)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc_info:
            await interview_service.assign_questions(mock_session, interview)

        assert "Not enough questions" in str(exc_info.value)
        assert "Requested 5" in str(exc_info.value)
        assert "found 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assigns_questions_successfully(self, interview_service):
        """Test successful question assignment."""
        mock_session = AsyncMock()

        # Create mock interview
        interview = MagicMock(spec=InterviewSession)
        interview.id = uuid4()
        interview.interview_type = InterviewType.TECHNICAL
        interview.difficulty = "medium"
        interview.question_count = 2
        interview.target_company = None

        # Create mock questions
        questions = []
        for i in range(2):
            q = MagicMock(spec=Question)
            q.id = uuid4()
            q.expected_duration_seconds = 180
            questions.append(q)

        # Mock exec to return questions
        mock_result = MagicMock()
        mock_result.all.return_value = questions
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.assign_questions(mock_session, interview)

        assert len(result) == 2
        assert mock_session.add.call_count == 2
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_handles_company_specific_questions(self, interview_service):
        """Test prioritizes company-specific questions."""
        mock_session = AsyncMock()

        interview = MagicMock(spec=InterviewSession)
        interview.id = uuid4()
        interview.interview_type = InterviewType.BEHAVIORAL
        interview.difficulty = "medium"
        interview.question_count = 2
        interview.target_company = "Google"

        # Company-specific questions
        company_questions = []
        for i in range(1):
            q = MagicMock(spec=Question)
            q.id = uuid4()
            q.expected_duration_seconds = 180
            company_questions.append(q)

        # General questions
        general_questions = []
        for i in range(1):
            q = MagicMock(spec=Question)
            q.id = uuid4()
            q.expected_duration_seconds = 180
            general_questions.append(q)

        # Mock to return company questions first, then general
        call_count = 0

        def mock_exec(*args):
            nonlocal call_count
            mock_result = MagicMock()
            if call_count == 0:
                mock_result.all.return_value = company_questions
            else:
                mock_result.all.return_value = general_questions
            call_count += 1
            return mock_result

        mock_session.exec = AsyncMock(side_effect=mock_exec)

        result = await interview_service.assign_questions(mock_session, interview)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_handles_mixed_difficulty(self, interview_service):
        """Test handles 'mixed' difficulty correctly."""
        mock_session = AsyncMock()

        interview = MagicMock(spec=InterviewSession)
        interview.id = uuid4()
        interview.interview_type = InterviewType.BEHAVIORAL
        interview.difficulty = "mixed"  # Should not filter by difficulty
        interview.question_count = 1
        interview.target_company = None

        question = MagicMock(spec=Question)
        question.id = uuid4()
        question.expected_duration_seconds = 180

        mock_result = MagicMock()
        mock_result.all.return_value = [question]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.assign_questions(mock_session, interview)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_handles_none_difficulty(self, interview_service):
        """Test handles None difficulty correctly."""
        mock_session = AsyncMock()

        interview = MagicMock(spec=InterviewSession)
        interview.id = uuid4()
        interview.interview_type = InterviewType.TECHNICAL
        interview.difficulty = None
        interview.question_count = 1
        interview.target_company = None

        question = MagicMock(spec=Question)
        question.id = uuid4()
        question.expected_duration_seconds = 180

        mock_result = MagicMock()
        mock_result.all.return_value = [question]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.assign_questions(mock_session, interview)

        assert len(result) == 1


class TestGetInterviewQuestions:
    """Tests for get_interview_questions method."""

    @pytest.mark.asyncio
    async def test_returns_questions_in_order(self, interview_service):
        """Test returns questions ordered correctly."""
        mock_session = AsyncMock()
        interview_id = uuid4()

        questions = [
            MagicMock(spec=Question, id=uuid4()),
            MagicMock(spec=Question, id=uuid4()),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = questions
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.get_interview_questions(mock_session, interview_id)

        assert len(result) == 2
        assert result == questions

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_questions(self, interview_service):
        """Test returns empty list when no questions assigned."""
        mock_session = AsyncMock()
        interview_id = uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.get_interview_questions(mock_session, interview_id)

        assert result == []


class TestHasAssignedQuestions:
    """Tests for has_assigned_questions method."""

    @pytest.mark.asyncio
    async def test_returns_true_when_questions_exist(self, interview_service):
        """Test returns True when questions are assigned."""
        mock_session = AsyncMock()
        interview_id = uuid4()

        mock_result = MagicMock()
        mock_result.one.return_value = 3  # 3 questions assigned
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.has_assigned_questions(mock_session, interview_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_no_questions(self, interview_service):
        """Test returns False when no questions assigned."""
        mock_session = AsyncMock()
        interview_id = uuid4()

        mock_result = MagicMock()
        mock_result.one.return_value = 0
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.has_assigned_questions(mock_session, interview_id)

        assert result is False


class TestAssignSpecificQuestion:
    """Tests for assign_specific_question method."""

    @pytest.mark.asyncio
    async def test_raises_error_when_question_not_found(self, interview_service):
        """Test raises ValueError when question doesn't exist."""
        mock_session = AsyncMock()

        interview = MagicMock(spec=InterviewSession)
        interview.id = uuid4()
        question_id = uuid4()

        # Mock exec to return None (question not found)
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError) as exc_info:
            await interview_service.assign_specific_question(mock_session, interview, question_id)

        assert "not found or is inactive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assigns_specific_question_successfully(self, interview_service):
        """Test successful specific question assignment."""
        mock_session = AsyncMock()

        interview = MagicMock(spec=InterviewSession)
        interview.id = uuid4()
        question_id = uuid4()

        # Create mock question
        question = MagicMock(spec=Question)
        question.id = question_id
        question.expected_duration_seconds = 300

        mock_result = MagicMock()
        mock_result.first.return_value = question
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await interview_service.assign_specific_question(mock_session, interview, question_id)

        assert result is not None
        assert mock_session.add.called
        assert mock_session.flush.called
