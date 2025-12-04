"""Interview session management service."""

from uuid import UUID

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.interview import InterviewQuestion, InterviewSession, InterviewType
from app.models.question import Question, QuestionCategory


class InterviewService:
    """Service for managing interview sessions and question assignment.

    Handles:
    - Random question selection matching interview type
    - Creating InterviewQuestion records to link questions to sessions
    - Retrieving assigned questions for a session
    """

    @staticmethod
    def _get_category_for_type(interview_type: InterviewType) -> QuestionCategory | None:
        """Map interview type to question category.

        Args:
            interview_type: The type of interview

        Returns:
            Matching QuestionCategory or None for mixed interviews
        """
        mapping = {
            InterviewType.BEHAVIORAL: QuestionCategory.BEHAVIORAL,
            InterviewType.TECHNICAL: QuestionCategory.TECHNICAL,
            InterviewType.SYSTEM_DESIGN: QuestionCategory.SYSTEM_DESIGN,
        }
        return mapping.get(interview_type)

    async def assign_questions(
        self,
        session: AsyncSession,
        interview: InterviewSession,
    ) -> list[InterviewQuestion]:
        """Select random questions and assign them to the interview session.

        Selects questions matching the interview type (category), difficulty, and
        optionally target company. When target_company is specified, prioritizes
        company-specific questions but falls back to general questions if needed.

        Args:
            session: Database session
            interview: The interview session to assign questions to

        Returns:
            List of created InterviewQuestion records

        Raises:
            ValueError: If not enough questions available for the interview type
        """
        # Determine category filter
        category = self._get_category_for_type(interview.interview_type)

        # Get difficulty value
        difficulty_value = (
            interview.difficulty.value
            if hasattr(interview.difficulty, "value")
            else interview.difficulty
        )

        questions: list[Question] = []

        # If target_company is specified, prioritize company-specific questions
        if interview.target_company:
            company_stmt = select(Question).where(Question.is_active == True)  # noqa: E712

            if category:
                company_stmt = company_stmt.where(Question.category == category.value)

            if difficulty_value and difficulty_value != "mixed":
                company_stmt = company_stmt.where(Question.difficulty == difficulty_value)

            # Filter for questions with matching company tag
            company_stmt = company_stmt.where(
                Question.company_tags.any(interview.target_company.lower())
            )
            company_stmt = company_stmt.order_by(func.random()).limit(interview.question_count)

            result = await session.exec(company_stmt)
            questions = list(result.all())

        # If we don't have enough company-specific questions, get remaining from general pool
        remaining_count = interview.question_count - len(questions)
        if remaining_count > 0:
            existing_ids = [q.id for q in questions]

            general_stmt = select(Question).where(Question.is_active == True)  # noqa: E712

            if category:
                general_stmt = general_stmt.where(Question.category == category.value)

            if difficulty_value and difficulty_value != "mixed":
                general_stmt = general_stmt.where(Question.difficulty == difficulty_value)

            # Exclude already selected questions
            if existing_ids:
                general_stmt = general_stmt.where(~Question.id.in_(existing_ids))

            general_stmt = general_stmt.order_by(func.random()).limit(remaining_count)

            result = await session.exec(general_stmt)
            questions.extend(list(result.all()))

        if len(questions) < interview.question_count:
            available = len(questions)
            difficulty_info = (
                f", difficulty '{difficulty_value}'"
                if difficulty_value and difficulty_value != "mixed"
                else ""
            )
            raise ValueError(
                f"Not enough questions available. "
                f"Requested {interview.question_count}, found {available} "
                f"for category '{category.value if category else 'mixed'}'{difficulty_info}"
            )

        # Create InterviewQuestion records
        interview_questions = []
        for order, question in enumerate(questions, start=1):
            interview_question = InterviewQuestion(
                session_id=interview.id,
                question_id=question.id,
                order=order,
                time_limit_seconds=question.expected_duration_seconds,
            )
            session.add(interview_question)
            interview_questions.append(interview_question)

        await session.flush()  # Ensure IDs are generated

        return interview_questions

    async def get_interview_questions(
        self,
        session: AsyncSession,
        interview_id: UUID,
    ) -> list[Question]:
        """Get all questions assigned to an interview session.

        Args:
            session: Database session
            interview_id: UUID of the interview session

        Returns:
            List of Question objects in order they should be asked
        """
        stmt = (
            select(Question)
            .join(InterviewQuestion, InterviewQuestion.question_id == Question.id)
            .where(InterviewQuestion.session_id == interview_id)
            .order_by(InterviewQuestion.order)
        )

        result = await session.exec(stmt)
        return list(result.all())

    async def has_assigned_questions(
        self,
        session: AsyncSession,
        interview_id: UUID,
    ) -> bool:
        """Check if an interview session has questions assigned.

        Args:
            session: Database session
            interview_id: UUID of the interview session

        Returns:
            True if questions are assigned, False otherwise
        """
        stmt = (
            select(func.count())
            .select_from(InterviewQuestion)
            .where(InterviewQuestion.session_id == interview_id)
        )
        result = await session.exec(stmt)
        count = result.one()
        return count > 0

    async def assign_specific_question(
        self,
        session: AsyncSession,
        interview: InterviewSession,
        question_id: UUID,
    ) -> InterviewQuestion:
        """Assign a specific question to an interview session (for quick practice).

        Args:
            session: Database session
            interview: The interview session to assign question to
            question_id: UUID of the specific question to assign

        Returns:
            Created InterviewQuestion record

        Raises:
            ValueError: If question doesn't exist or is inactive
        """
        # Verify question exists and is active
        stmt = select(Question).where(
            Question.id == question_id,
            Question.is_active == True,  # noqa: E712
        )
        result = await session.exec(stmt)
        question = result.first()

        if not question:
            raise ValueError("Question not found or is inactive")

        # Create InterviewQuestion record
        interview_question = InterviewQuestion(
            session_id=interview.id,
            question_id=question.id,
            order=1,
            time_limit_seconds=question.expected_duration_seconds,
        )
        session.add(interview_question)
        await session.flush()

        return interview_question
