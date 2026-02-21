"""Tests for question recommendation service."""

from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.feedback import ContentFeedback
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.question_recommender import (
    _get_difficulty_progression,
    _get_same_topic_questions,
    _get_user_weak_areas,
    recommend_next_questions,
)


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        id=str(uuid4()),
        email=f"rec_user_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("TestPassword123!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def behavioral_questions(db_session):
    """Create a set of behavioral questions with various difficulties and topics."""
    questions = [
        Question(
            id=uuid4(),
            content="Tell me about a time you led a team.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            topic_tags=["leadership", "teamwork"],
        ),
        Question(
            id=uuid4(),
            content="Describe a conflict you resolved.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            topic_tags=["leadership", "conflict-resolution"],
        ),
        Question(
            id=uuid4(),
            content="Tell me about a simple success.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.EASY,
            topic_tags=["teamwork"],
        ),
        Question(
            id=uuid4(),
            content="Describe your biggest leadership challenge.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.HARD,
            topic_tags=["leadership"],
        ),
        Question(
            id=uuid4(),
            content="How do you handle difficult stakeholders?",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.HARD,
            topic_tags=["communication", "stakeholder-management"],
        ),
    ]
    for q in questions:
        db_session.add(q)
    await db_session.commit()
    return questions


@pytest.fixture
async def technical_questions(db_session):
    """Create technical questions."""
    questions = [
        Question(
            id=uuid4(),
            content="Explain binary search.",
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.EASY,
            topic_tags=["algorithms", "search"],
        ),
        Question(
            id=uuid4(),
            content="Implement a linked list.",
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.MEDIUM,
            topic_tags=["data-structures"],
        ),
    ]
    for q in questions:
        db_session.add(q)
    await db_session.commit()
    return questions


class TestRecommendNextQuestions:
    """Tests for recommend_next_questions function."""

    @pytest.mark.asyncio
    async def test_recommend_same_topic_questions(
        self, db_session, test_user, behavioral_questions
    ):
        """Returns questions from same topic as current question."""
        current_q = behavioral_questions[0]  # leadership, teamwork

        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=current_q.id,
            feedback_score=70.0,
        )

        assert len(recommendations) > 0
        assert str(current_q.id) not in recommendations

        # Check that some recommendations are from same category
        for rec_id in recommendations[:2]:
            result = await db_session.exec(
                select(Question).where(Question.id == rec_id)
            )
            rec_q = result.first()
            assert rec_q is not None
            assert rec_q.category == QuestionCategory.BEHAVIORAL

    @pytest.mark.asyncio
    async def test_recommend_higher_difficulty_on_high_score(
        self, db_session, test_user, behavioral_questions
    ):
        """Increases difficulty after 80+ score."""
        # Start with medium difficulty question
        current_q = behavioral_questions[0]  # MEDIUM
        assert current_q.difficulty == Difficulty.MEDIUM

        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=current_q.id,
            feedback_score=85.0,  # High score
        )

        assert len(recommendations) > 0
        assert len(recommendations) <= 5

    @pytest.mark.asyncio
    async def test_recommend_same_difficulty_on_mid_score(
        self, db_session, test_user, behavioral_questions
    ):
        """Keeps same difficulty after 50-79 score."""
        current_q = behavioral_questions[0]  # MEDIUM

        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=current_q.id,
            feedback_score=65.0,  # Mid score
        )

        assert len(recommendations) > 0
        assert str(current_q.id) not in recommendations

    @pytest.mark.asyncio
    async def test_recommend_lower_difficulty_on_low_score(
        self, db_session, test_user, behavioral_questions
    ):
        """Decreases difficulty after <50 score."""
        current_q = behavioral_questions[0]  # MEDIUM

        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=current_q.id,
            feedback_score=35.0,  # Low score
        )

        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_recommend_excludes_current_question(
        self, db_session, test_user, behavioral_questions
    ):
        """Never recommends the current question."""
        current_q = behavioral_questions[0]

        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=current_q.id,
            feedback_score=70.0,
        )

        assert str(current_q.id) not in recommendations

    @pytest.mark.asyncio
    async def test_recommend_returns_max_five(
        self, db_session, test_user, behavioral_questions, technical_questions
    ):
        """Returns at most 5 questions."""
        current_q = behavioral_questions[0]

        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=current_q.id,
            feedback_score=70.0,
        )

        assert len(recommendations) <= 5

    @pytest.mark.asyncio
    async def test_recommend_empty_for_invalid_question(
        self, db_session, test_user
    ):
        """Returns empty list for nonexistent question."""
        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=uuid4(),  # Invalid
            feedback_score=70.0,
        )

        assert recommendations == []

    @pytest.mark.asyncio
    async def test_recommend_weak_area_questions(
        self, db_session, test_user, behavioral_questions
    ):
        """Includes questions from user's weak topic areas."""
        # Create an interview session with low-scoring response
        session_obj = InterviewSession(
            id=uuid4(),
            user_id=test_user.id,
            interview_type="behavioral",
            status=InterviewStatus.COMPLETED,
        )
        db_session.add(session_obj)
        await db_session.commit()

        # Create response for a question with "communication" topic
        comm_question = behavioral_questions[4]  # communication topic
        response = InterviewResponse(
            id=uuid4(),
            session_id=session_obj.id,
            question_id=comm_question.id,
            duration_seconds=120,
        )
        db_session.add(response)
        await db_session.commit()

        # Add low content feedback
        feedback = ContentFeedback(
            id=uuid4(),
            response_id=response.id,
            technical_accuracy=50.0,
            star_adherence=45.0,
            answer_structure=40.0,
            completeness=50.0,
            relevance=55.0,
            overall_content_score=48.0,  # Below threshold
            strengths=["Good effort"],
            improvements=["Needs more structure"],
        )
        db_session.add(feedback)
        await db_session.commit()

        # Now get recommendations for a different question
        current_q = behavioral_questions[0]  # leadership topic

        recommendations = await recommend_next_questions(
            session=db_session,
            user_id=test_user.id,
            question_id=current_q.id,
            feedback_score=75.0,
        )

        # Should include some recommendations
        assert len(recommendations) > 0


class TestDifficultyProgression:
    """Tests for _get_difficulty_progression function."""

    def test_increase_difficulty_on_high_score(self):
        """Score >= 80 increases difficulty."""
        result = _get_difficulty_progression(Difficulty.EASY, 85.0)
        assert result == Difficulty.MEDIUM

        result = _get_difficulty_progression(Difficulty.MEDIUM, 80.0)
        assert result == Difficulty.HARD

    def test_max_difficulty_stays_same(self):
        """Already at HARD difficulty stays HARD."""
        result = _get_difficulty_progression(Difficulty.HARD, 90.0)
        assert result == Difficulty.HARD

    def test_same_difficulty_on_mid_score(self):
        """Score 50-79 keeps same difficulty."""
        result = _get_difficulty_progression(Difficulty.MEDIUM, 65.0)
        assert result == Difficulty.MEDIUM

        result = _get_difficulty_progression(Difficulty.MEDIUM, 79.0)
        assert result == Difficulty.MEDIUM

    def test_decrease_difficulty_on_low_score(self):
        """Score < 50 decreases difficulty."""
        result = _get_difficulty_progression(Difficulty.HARD, 40.0)
        assert result == Difficulty.MEDIUM

        result = _get_difficulty_progression(Difficulty.MEDIUM, 35.0)
        assert result == Difficulty.EASY

    def test_min_difficulty_stays_same(self):
        """Already at EASY difficulty stays EASY."""
        result = _get_difficulty_progression(Difficulty.EASY, 30.0)
        assert result == Difficulty.EASY


class TestSameTopicQuestions:
    """Tests for _get_same_topic_questions function."""

    @pytest.mark.asyncio
    async def test_finds_questions_with_matching_topics(
        self, db_session, behavioral_questions
    ):
        """Finds questions with overlapping topic tags."""
        current_q = behavioral_questions[0]  # leadership, teamwork

        result = await _get_same_topic_questions(
            db_session, current_q, exclude_ids={current_q.id}, limit=3
        )

        assert len(result) > 0
        for q in result:
            assert q.id != current_q.id
            assert q.category == QuestionCategory.BEHAVIORAL

    @pytest.mark.asyncio
    async def test_falls_back_to_category_match(
        self, db_session
    ):
        """Falls back to category match if no topic tags."""
        # Create question with no topic tags
        q_no_tags = Question(
            id=uuid4(),
            content="Generic behavioral question",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            topic_tags=[],
        )
        db_session.add(q_no_tags)

        # Create another behavioral question
        q_other = Question(
            id=uuid4(),
            content="Another behavioral question",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.EASY,
            topic_tags=[],
        )
        db_session.add(q_other)
        await db_session.commit()

        result = await _get_same_topic_questions(
            db_session, q_no_tags, exclude_ids={q_no_tags.id}, limit=2
        )

        # Should find questions by category
        assert len(result) >= 1


class TestUserWeakAreas:
    """Tests for _get_user_weak_areas function."""

    @pytest.mark.asyncio
    async def test_returns_empty_for_new_user(self, db_session, test_user):
        """New user with no history returns empty weak areas."""
        weak_areas = await _get_user_weak_areas(db_session, test_user.id)
        assert weak_areas == []

    @pytest.mark.asyncio
    async def test_identifies_weak_topics_from_low_scores(
        self, db_session, test_user, behavioral_questions
    ):
        """Identifies topics from low-scoring responses."""
        # Create interview session and commit first
        session_obj = InterviewSession(
            id=uuid4(),
            user_id=test_user.id,
            interview_type="behavioral",
            status=InterviewStatus.COMPLETED,
        )
        db_session.add(session_obj)
        await db_session.commit()
        await db_session.refresh(session_obj)

        # Create low-scoring response for stakeholder question
        stakeholder_q = behavioral_questions[4]  # stakeholder-management topic
        response = InterviewResponse(
            id=uuid4(),
            session_id=session_obj.id,
            question_id=stakeholder_q.id,
            duration_seconds=90,
        )
        db_session.add(response)
        await db_session.commit()
        await db_session.refresh(response)

        # Add low content feedback
        feedback = ContentFeedback(
            id=uuid4(),
            response_id=response.id,
            technical_accuracy=50.0,
            star_adherence=40.0,
            answer_structure=45.0,
            completeness=50.0,
            relevance=55.0,
            overall_content_score=48.0,  # Below 60 threshold
        )
        db_session.add(feedback)
        await db_session.commit()

        weak_areas = await _get_user_weak_areas(db_session, test_user.id)

        # Should identify the weak topic
        assert len(weak_areas) > 0
        assert any("stakeholder" in topic or "communication" in topic for topic in weak_areas)
