"""Question recommendation service for intelligent next-question suggestions.

Provides personalized question recommendations based on:
- Topic relevance (same category/topic)
- Difficulty progression (based on performance)
- Weak area focus (based on past feedback)
"""

import logging
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.feedback import ContentFeedback
from app.models.interview import InterviewResponse, InterviewSession
from app.models.question import Difficulty, Question, QuestionCategory

logger = logging.getLogger(__name__)

# Difficulty progression map
DIFFICULTY_ORDER = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
MAX_RECOMMENDATIONS = 5
WEAK_AREA_THRESHOLD = 60.0  # Score below this indicates weak area


async def recommend_next_questions(
    session: AsyncSession,
    user_id: UUID,
    question_id: UUID,
    feedback_score: float,
    max_questions: int = MAX_RECOMMENDATIONS,
) -> list[str]:
    """Recommend next questions based on user performance and history.

    Algorithm:
    1. Get 2 questions from the same topic/category
    2. Adjust difficulty based on feedback score
    3. Get 1-2 questions from user's weak areas
    4. Fill remaining slots with popular questions

    Args:
        session: Database session
        user_id: User ID for personalization
        question_id: Current question ID (to exclude)
        feedback_score: Score from current feedback (0-100)
        max_questions: Maximum number of recommendations

    Returns:
        List of recommended question IDs (as strings)
    """
    recommendations: list[str] = []
    excluded_ids: set[UUID] = {question_id}

    # Get current question for context
    current_question = await session.get(Question, question_id)
    if not current_question:
        logger.warning(f"Question {question_id} not found for recommendations")
        return []

    # 1. Get same-topic questions (2)
    same_topic = await _get_same_topic_questions(session, current_question, excluded_ids, limit=2)
    recommendations.extend([str(q.id) for q in same_topic])
    excluded_ids.update(q.id for q in same_topic)

    # 2. Get next difficulty level question based on score
    next_difficulty = _get_difficulty_progression(current_question.difficulty, feedback_score)
    if next_difficulty != current_question.difficulty:
        difficulty_qs = await _get_questions_by_difficulty(
            session, current_question.category, next_difficulty, excluded_ids, limit=1
        )
        recommendations.extend([str(q.id) for q in difficulty_qs])
        excluded_ids.update(q.id for q in difficulty_qs)

    # 3. Get weak area questions (1-2)
    weak_areas = await _get_user_weak_areas(session, user_id)
    if weak_areas:
        weak_area_qs = await _get_questions_by_topics(session, weak_areas, excluded_ids, limit=2)
        recommendations.extend([str(q.id) for q in weak_area_qs])
        excluded_ids.update(q.id for q in weak_area_qs)

    # 4. Get user's answered question IDs to exclude from recommendations
    answered_ids = await _get_user_answered_questions(session, user_id)
    excluded_ids.update(answered_ids)

    # 5. Fill remaining with popular/random questions if needed
    remaining_slots = max_questions - len(recommendations)
    if remaining_slots > 0:
        popular = await _get_popular_questions(session, excluded_ids, limit=remaining_slots)
        recommendations.extend([str(q.id) for q in popular])

    # Deduplicate while preserving order
    seen = set()
    unique_recommendations = []
    for q_id in recommendations:
        if q_id not in seen:
            seen.add(q_id)
            unique_recommendations.append(q_id)

    return unique_recommendations[:max_questions]


async def _get_same_topic_questions(
    session: AsyncSession,
    current_question: Question,
    exclude_ids: set[UUID],
    limit: int = 2,
) -> list[Question]:
    """Get questions from the same category and topic.

    First tries to match topic_tags, falls back to category match.
    """
    # Try matching by topic tags first
    if current_question.topic_tags:
        query = (
            select(Question)
            .where(Question.is_active.is_(True))
            .where(Question.id.notin_(exclude_ids))
            .where(Question.category == current_question.category)
            .where(Question.topic_tags.overlap(current_question.topic_tags))
            .limit(limit)
        )
        result = await session.exec(query)
        questions = list(result.all())
        if questions:
            return questions

    # Fall back to same category
    query = (
        select(Question)
        .where(Question.is_active.is_(True))
        .where(Question.id.notin_(exclude_ids))
        .where(Question.category == current_question.category)
        .limit(limit)
    )
    result = await session.exec(query)
    return list(result.all())


def _get_difficulty_progression(
    current_difficulty: Difficulty,
    feedback_score: float,
) -> Difficulty:
    """Determine next difficulty level based on performance.

    - Score >= 80: Increase difficulty (challenge user)
    - Score >= 50: Stay at same level (consolidate)
    - Score < 50: Decrease difficulty (build confidence)
    """
    try:
        current_idx = DIFFICULTY_ORDER.index(current_difficulty)
    except ValueError:
        return current_difficulty

    if feedback_score >= 80 and current_idx < len(DIFFICULTY_ORDER) - 1:
        return DIFFICULTY_ORDER[current_idx + 1]
    elif feedback_score < 50 and current_idx > 0:
        return DIFFICULTY_ORDER[current_idx - 1]

    return current_difficulty


async def _get_questions_by_difficulty(
    session: AsyncSession,
    category: QuestionCategory,
    difficulty: Difficulty,
    exclude_ids: set[UUID],
    limit: int = 1,
) -> list[Question]:
    """Get questions of a specific difficulty in a category."""
    query = (
        select(Question)
        .where(Question.is_active.is_(True))
        .where(Question.id.notin_(exclude_ids))
        .where(Question.category == category)
        .where(Question.difficulty == difficulty)
        .limit(limit)
    )
    result = await session.exec(query)
    return list(result.all())


async def _get_user_weak_areas(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 2,
) -> list[str]:
    """Analyze user's past feedback to identify weak topic areas.

    Returns topic tags where user scored below threshold.
    """
    # Get user's responses with low content scores
    query = (
        select(Question.topic_tags, ContentFeedback.overall_content_score)
        .join(InterviewResponse, ContentFeedback.response_id == InterviewResponse.id)
        .join(InterviewSession, InterviewResponse.session_id == InterviewSession.id)
        .join(Question, InterviewResponse.question_id == Question.id)
        .where(InterviewSession.user_id == user_id)
        .where(ContentFeedback.overall_content_score < WEAK_AREA_THRESHOLD)
        .order_by(ContentFeedback.created_at.desc())
        .limit(10)  # Look at recent low-scoring responses
    )
    result = await session.exec(query)
    rows = list(result.all())

    # Collect topic tags from weak responses
    weak_topics: dict[str, int] = {}
    for topic_tags, _ in rows:
        if topic_tags:
            for tag in topic_tags:
                weak_topics[tag] = weak_topics.get(tag, 0) + 1

    # Sort by frequency and return top weak areas
    sorted_topics = sorted(weak_topics.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, _ in sorted_topics[:limit]]


async def _get_questions_by_topics(
    session: AsyncSession,
    topics: list[str],
    exclude_ids: set[UUID],
    limit: int = 2,
) -> list[Question]:
    """Get questions matching any of the specified topics."""
    if not topics:
        return []

    query = (
        select(Question)
        .where(Question.is_active.is_(True))
        .where(Question.id.notin_(exclude_ids))
        .where(Question.topic_tags.overlap(topics))
        .limit(limit)
    )
    result = await session.exec(query)
    return list(result.all())


async def _get_user_answered_questions(
    session: AsyncSession,
    user_id: UUID,
) -> set[UUID]:
    """Get all question IDs the user has already answered."""
    query = (
        select(InterviewResponse.question_id)
        .join(InterviewSession, InterviewResponse.session_id == InterviewSession.id)
        .where(InterviewSession.user_id == user_id)
    )
    result = await session.exec(query)
    return set(result.all())


async def _get_popular_questions(
    session: AsyncSession,
    exclude_ids: set[UUID],
    limit: int = 2,
) -> list[Question]:
    """Get popular/commonly practiced questions as fallback.

    Currently returns random active questions. Future: track popularity.
    """
    query = (
        select(Question)
        .where(Question.is_active.is_(True))
        .where(Question.id.notin_(exclude_ids))
        .order_by(Question.created_at.desc())  # Most recent as proxy for popular
        .limit(limit)
    )
    result = await session.exec(query)
    return list(result.all())
