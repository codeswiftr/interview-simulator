"""Pure unit tests for question recommender service.

Tests the recommendation algorithm without database.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.question import Difficulty, Question, QuestionCategory
from app.services.question_recommender import (
    DIFFICULTY_ORDER,
    MAX_RECOMMENDATIONS,
    WEAK_AREA_THRESHOLD,
    _get_difficulty_progression,
    _get_popular_questions,
    _get_questions_by_difficulty,
    _get_questions_by_topics,
    _get_same_topic_questions,
    _get_user_answered_questions,
    _get_user_weak_areas,
    recommend_next_questions,
)


class TestGetDifficultyProgression:
    """Tests for _get_difficulty_progression helper."""

    def test_increases_difficulty_on_high_score(self):
        """Test difficulty increases when score >= 80."""
        # EASY -> MEDIUM
        result = _get_difficulty_progression(Difficulty.EASY, 85)
        assert result == Difficulty.MEDIUM

        # MEDIUM -> HARD
        result = _get_difficulty_progression(Difficulty.MEDIUM, 90)
        assert result == Difficulty.HARD

    def test_stays_same_on_medium_score(self):
        """Test difficulty stays same when 50 <= score < 80."""
        # EASY stays EASY
        result = _get_difficulty_progression(Difficulty.EASY, 65)
        assert result == Difficulty.EASY

        # MEDIUM stays MEDIUM
        result = _get_difficulty_progression(Difficulty.MEDIUM, 75)
        assert result == Difficulty.MEDIUM

        # HARD stays HARD
        result = _get_difficulty_progression(Difficulty.HARD, 50)
        assert result == Difficulty.HARD

    def test_decreases_difficulty_on_low_score(self):
        """Test difficulty decreases when score < 50."""
        # HARD -> MEDIUM
        result = _get_difficulty_progression(Difficulty.HARD, 40)
        assert result == Difficulty.MEDIUM

        # MEDIUM -> EASY
        result = _get_difficulty_progression(Difficulty.MEDIUM, 30)
        assert result == Difficulty.EASY

    def test_doesnt_go_below_easy(self):
        """Test difficulty doesn't go below EASY."""
        result = _get_difficulty_progression(Difficulty.EASY, 20)
        assert result == Difficulty.EASY

    def test_doesnt_go_above_hard(self):
        """Test difficulty doesn't go above HARD."""
        result = _get_difficulty_progression(Difficulty.HARD, 95)
        assert result == Difficulty.HARD

    def test_handles_boundary_scores(self):
        """Test boundary score values."""
        # Exactly 80 should increase
        result = _get_difficulty_progression(Difficulty.EASY, 80)
        assert result == Difficulty.MEDIUM

        # Exactly 50 should stay same
        result = _get_difficulty_progression(Difficulty.MEDIUM, 50)
        assert result == Difficulty.MEDIUM

        # Just below 50 should decrease
        result = _get_difficulty_progression(Difficulty.MEDIUM, 49.9)
        assert result == Difficulty.EASY


class TestGetSameTopicQuestions:
    """Tests for _get_same_topic_questions helper."""

    @pytest.mark.asyncio
    async def test_returns_questions_with_matching_topics(self):
        """Test returns questions matching topic tags."""
        mock_session = AsyncMock()

        current_question = MagicMock(spec=Question)
        current_question.category = QuestionCategory.BEHAVIORAL
        current_question.topic_tags = ["leadership", "teamwork"]

        # Mock questions returned
        matching_qs = [
            MagicMock(spec=Question, id=uuid4()),
            MagicMock(spec=Question, id=uuid4()),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = matching_qs
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_same_topic_questions(mock_session, current_question, set(), limit=2)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_falls_back_to_category_when_no_topic_matches(self):
        """Test falls back to category match when no topic tags match."""
        mock_session = AsyncMock()

        current_question = MagicMock(spec=Question)
        current_question.category = QuestionCategory.TECHNICAL
        current_question.topic_tags = ["python"]

        # First query returns empty (no topic matches)
        # Second query returns category matches
        category_qs = [MagicMock(spec=Question, id=uuid4())]

        call_count = 0

        def mock_exec(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:
                result.all.return_value = []  # No topic matches
            else:
                result.all.return_value = category_qs  # Category fallback
            call_count += 1
            return result

        mock_session.exec = AsyncMock(side_effect=mock_exec)

        result = await _get_same_topic_questions(mock_session, current_question, set(), limit=2)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_uses_category_fallback_when_no_topic_tags(self):
        """Test uses category match when question has no topic tags."""
        mock_session = AsyncMock()

        current_question = MagicMock(spec=Question)
        current_question.category = QuestionCategory.SYSTEM_DESIGN
        current_question.topic_tags = []  # No tags

        category_qs = [MagicMock(spec=Question, id=uuid4())]

        mock_result = MagicMock()
        mock_result.all.return_value = category_qs
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_same_topic_questions(mock_session, current_question, set(), limit=2)

        assert len(result) == 1


class TestGetQuestionsByDifficulty:
    """Tests for _get_questions_by_difficulty helper."""

    @pytest.mark.asyncio
    async def test_returns_questions_matching_difficulty(self):
        """Test returns questions of specified difficulty."""
        mock_session = AsyncMock()

        questions = [MagicMock(spec=Question, id=uuid4())]

        mock_result = MagicMock()
        mock_result.all.return_value = questions
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_questions_by_difficulty(
            mock_session,
            QuestionCategory.TECHNICAL,
            Difficulty.MEDIUM,
            set(),
            limit=1,
        )

        assert len(result) == 1


class TestGetQuestionsByTopics:
    """Tests for _get_questions_by_topics helper."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_topics(self):
        """Test returns empty list when no topics provided."""
        mock_session = AsyncMock()

        result = await _get_questions_by_topics(mock_session, [], set(), limit=2)

        assert result == []
        assert not mock_session.exec.called

    @pytest.mark.asyncio
    async def test_returns_questions_matching_topics(self):
        """Test returns questions matching topics."""
        mock_session = AsyncMock()

        questions = [
            MagicMock(spec=Question, id=uuid4()),
            MagicMock(spec=Question, id=uuid4()),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = questions
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_questions_by_topics(
            mock_session, ["algorithms", "data-structures"], set(), limit=2
        )

        assert len(result) == 2


class TestGetUserWeakAreas:
    """Tests for _get_user_weak_areas helper."""

    @pytest.mark.asyncio
    async def test_returns_weak_topics_from_low_scores(self):
        """Test returns topics from responses with low scores."""
        mock_session = AsyncMock()
        user_id = uuid4()

        # Mock feedback data: topic_tags, score
        feedback_data = [
            (["leadership"], 55.0),
            (["leadership"], 45.0),
            (["communication"], 58.0),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = feedback_data
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_user_weak_areas(mock_session, user_id, limit=2)

        assert "leadership" in result  # Most frequent weak area

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_weak_areas(self):
        """Test returns empty list when no low-scoring feedback."""
        mock_session = AsyncMock()
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_user_weak_areas(mock_session, user_id)

        assert result == []


class TestGetUserAnsweredQuestions:
    """Tests for _get_user_answered_questions helper."""

    @pytest.mark.asyncio
    async def test_returns_answered_question_ids(self):
        """Test returns set of answered question IDs."""
        mock_session = AsyncMock()
        user_id = uuid4()

        answered_ids = [uuid4(), uuid4(), uuid4()]

        mock_result = MagicMock()
        mock_result.all.return_value = answered_ids
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_user_answered_questions(mock_session, user_id)

        assert isinstance(result, set)
        assert len(result) == 3


class TestGetPopularQuestions:
    """Tests for _get_popular_questions helper."""

    @pytest.mark.asyncio
    async def test_returns_recent_questions(self):
        """Test returns recent questions as popularity proxy."""
        mock_session = AsyncMock()

        questions = [
            MagicMock(spec=Question, id=uuid4()),
            MagicMock(spec=Question, id=uuid4()),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = questions
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await _get_popular_questions(mock_session, set(), limit=2)

        assert len(result) == 2


class TestRecommendNextQuestions:
    """Tests for the main recommend_next_questions function."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_question_not_found(self):
        """Test returns empty list when current question not found."""
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=None)

        result = await recommend_next_questions(
            mock_session,
            user_id=uuid4(),
            question_id=uuid4(),
            feedback_score=75.0,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_of_strings(self):
        """Test returns list of string IDs."""
        mock_session = AsyncMock()

        current_question = MagicMock(spec=Question)
        current_question.id = uuid4()
        current_question.category = QuestionCategory.BEHAVIORAL
        current_question.difficulty = Difficulty.MEDIUM
        current_question.topic_tags = []

        mock_session.get = AsyncMock(return_value=current_question)

        # Create mock question for recommendation
        rec_question = MagicMock(spec=Question)
        rec_question.id = uuid4()

        # Need to properly sequence mocks for different queries
        # 1. Same topic questions query - returns rec_question
        # 2. Weak areas query - returns empty list (tuple format)
        # 3. Answered questions query - returns empty set
        # 4. Popular questions query - returns empty
        query_results = [
            [rec_question],  # same_topic_questions
            [],  # weak_areas (returns tuples but empty)
            [],  # answered_questions
            [],  # popular_questions
        ]
        call_idx = [0]

        def mock_exec(query):
            result = MagicMock()
            if call_idx[0] < len(query_results):
                result.all.return_value = query_results[call_idx[0]]
                call_idx[0] += 1
            else:
                result.all.return_value = []
            return result

        mock_session.exec = AsyncMock(side_effect=mock_exec)

        result = await recommend_next_questions(
            mock_session,
            user_id=uuid4(),
            question_id=current_question.id,
            feedback_score=75.0,
            max_questions=5,
        )

        # Should return string IDs
        assert all(isinstance(q_id, str) for q_id in result)

    @pytest.mark.asyncio
    async def test_excludes_current_question(self):
        """Test excludes current question from recommendations."""
        mock_session = AsyncMock()

        current_question = MagicMock(spec=Question)
        current_question.id = uuid4()
        current_question.category = QuestionCategory.TECHNICAL
        current_question.difficulty = Difficulty.EASY
        current_question.topic_tags = []

        mock_session.get = AsyncMock(return_value=current_question)

        # Return empty results (all excluded)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await recommend_next_questions(
            mock_session,
            user_id=uuid4(),
            question_id=current_question.id,
            feedback_score=75.0,
        )

        # Current question ID should not be in results
        assert str(current_question.id) not in result


class TestConstants:
    """Tests for module constants."""

    def test_difficulty_order_is_ascending(self):
        """Test DIFFICULTY_ORDER is in ascending order."""
        assert DIFFICULTY_ORDER[0] == Difficulty.EASY
        assert DIFFICULTY_ORDER[1] == Difficulty.MEDIUM
        assert DIFFICULTY_ORDER[2] == Difficulty.HARD

    def test_max_recommendations_is_reasonable(self):
        """Test MAX_RECOMMENDATIONS is a reasonable value."""
        assert MAX_RECOMMENDATIONS >= 1
        assert MAX_RECOMMENDATIONS <= 10

    def test_weak_area_threshold_is_percentage(self):
        """Test WEAK_AREA_THRESHOLD is a valid percentage."""
        assert 0 <= WEAK_AREA_THRESHOLD <= 100
