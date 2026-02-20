"""Tests for preparation API endpoints - edge cases and comprehensive coverage.

Tests the AI Ghostwriter answer preparation workflow:
- Detective stage (clarifying questions)
- Draft generation (STAR-formatted answers)
- Practice delivery (audio transcription and rating)
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.preparation import (
    AnswerPreparation,
    DeliveryAttempt,
    PreparationQnA,
    PreparationStage,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import SubscriptionTier, User
from app.security import hash_password
from tests.conftest import register_and_login


@pytest.fixture
async def pro_user(db_session):
    """Create a Pro tier user for testing."""
    user = User(
        id=str(uuid4()),
        email=f"pro_user_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("TestPassword123!"),
        subscription_tier=SubscriptionTier.PRO,
        experience_level="senior",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def free_user(db_session):
    """Create a Free tier user for testing."""
    user = User(
        id=str(uuid4()),
        email=f"free_user_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("TestPassword123!"),
        subscription_tier=SubscriptionTier.FREE,
        experience_level="junior",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_question_for_prep(db_session):
    """Create a question for preparation tests."""
    question = Question(
        id=str(uuid4()),
        content="Tell me about a time you led a team through a difficult project.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def preparation_session(db_session, pro_user, test_question_for_prep):
    """Create a preparation session in detective stage."""
    prep = AnswerPreparation(
        id=uuid4(),
        user_id=pro_user.id,
        question_id=test_question_for_prep.id,
        stage=PreparationStage.DETECTIVE,
    )
    db_session.add(prep)
    await db_session.commit()
    await db_session.refresh(prep)
    return prep


@pytest.fixture
async def preparation_with_draft(db_session, pro_user, test_question_for_prep):
    """Create a preparation session in practice stage with a draft."""
    prep = AnswerPreparation(
        id=uuid4(),
        user_id=pro_user.id,
        question_id=test_question_for_prep.id,
        stage=PreparationStage.PRACTICE,
        draft_answer="**Situation**: I was leading a team of 5 engineers...\n**Task**: We needed to deliver a critical feature...\n**Action**: I organized daily standups...\n**Result**: We delivered on time with 95% test coverage.",
    )
    db_session.add(prep)
    await db_session.commit()
    await db_session.refresh(prep)
    return prep


class TestPreparationTierAccess:
    """Tests for subscription tier access control."""

    @pytest.mark.asyncio
    async def test_free_tier_blocked_from_preparation(self, client, free_user):
        """Free tier users cannot access preparation feature."""
        # Login as free user
        token = await register_and_login(
            client, email=free_user.email, password="TestPassword123!"
        )

        # Try to list preparations
        response = await client.get(
            "/api/v1/preparation",
            headers={"Authorization": token},
        )

        assert response.status_code == 402
        assert "Pro" in response.json()["detail"] or "Premium" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_pro_tier_allowed_preparation(self, client, pro_user):
        """Pro tier users can access preparation feature."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            "/api/v1/preparation",
            headers={"Authorization": token},
        )

        # Should succeed (200 or empty list)
        assert response.status_code == 200
        assert "preparations" in response.json()

    @pytest.mark.asyncio
    async def test_team_tier_allowed_preparation(self, client, db_session):
        """Team tier users can access preparation feature."""
        # Create team tier user
        team_user = User(
            id=str(uuid4()),
            email=f"team_{uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("TestPassword123!"),
            subscription_tier=SubscriptionTier.TEAM,
        )
        db_session.add(team_user)
        await db_session.commit()

        token = await register_and_login(
            client, email=team_user.email, password="TestPassword123!"
        )

        response = await client.get(
            "/api/v1/preparation",
            headers={"Authorization": token},
        )

        assert response.status_code == 200


class TestStartPreparation:
    """Tests for starting a preparation session."""

    @pytest.mark.asyncio
    async def test_start_preparation_success(self, client, pro_user, test_question_for_prep):
        """Start preparation creates session and returns ID."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            "/api/v1/preparation/start",
            headers={"Authorization": token},
            json={"question_id": str(test_question_for_prep.id)},
        )

        assert response.status_code == 201
        data = response.json()
        assert "preparation_id" in data
        assert data["stage"] == "detective"

    @pytest.mark.asyncio
    async def test_start_preparation_question_not_found(self, client, pro_user):
        """Starting preparation with invalid question returns 404."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            "/api/v1/preparation/start",
            headers={"Authorization": token},
            json={"question_id": str(uuid4())},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_start_preparation_resumes_existing(
        self, client, pro_user, preparation_session
    ):
        """Starting preparation for existing question resumes session."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        # First request - should get existing
        from sqlmodel import select

        from tests.conftest import get_test_engine

        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as session:
            result = await session.exec(
                select(AnswerPreparation).where(
                    AnswerPreparation.id == preparation_session.id
                )
            )
            existing = result.first()
            question_id = str(existing.question_id) if existing else None

        if question_id:
            response = await client.post(
                "/api/v1/preparation/start",
                headers={"Authorization": token},
                json={"question_id": question_id},
            )

            assert response.status_code == 201
            data = response.json()
            assert "Resuming" in data["message"] or "Existing" in data["message"]


class TestDetectiveStage:
    """Tests for the detective (clarifying questions) stage."""

    @pytest.mark.asyncio
    async def test_detective_question_no_api_key_fallback(
        self, client, pro_user, preparation_session
    ):
        """Without API key, returns generic fallback question."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = None

            response = await client.post(
                f"/api/v1/preparation/{preparation_session.id}/detective/question",
                headers={"Authorization": token},
            )

            # Should succeed with fallback question
            assert response.status_code == 200
            data = response.json()
            assert "question" in data
            assert data["order"] >= 1

    @pytest.mark.asyncio
    async def test_detective_question_wrong_stage(
        self, client, pro_user, preparation_with_draft
    ):
        """Cannot get detective question when not in detective stage."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{preparation_with_draft.id}/detective/question",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "not detective stage" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_detective_question_not_found(self, client, pro_user):
        """Getting question for nonexistent preparation returns 404."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{uuid4()}/detective/question",
            headers={"Authorization": token},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_detective_answer_no_unanswered_question(
        self, client, pro_user, preparation_session
    ):
        """Cannot submit answer when no unanswered question exists."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        # Try to submit answer without first getting a question
        response = await client.post(
            f"/api/v1/preparation/{preparation_session.id}/detective/answer",
            headers={"Authorization": token},
            json={"answer": "My experience includes..."},
        )

        assert response.status_code == 400
        assert "no unanswered question" in response.json()["detail"].lower()


class TestDetectiveMaxQuestions:
    """Tests for detective stage question limits."""

    @pytest.mark.asyncio
    async def test_detective_max_questions_limit(
        self, client, pro_user, preparation_session, db_session
    ):
        """Detective stage completes after 4-5 questions."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        # Add 4 answered Q&A entries
        for i in range(4):
            qna = PreparationQnA(
                id=uuid4(),
                preparation_id=preparation_session.id,
                question=f"Question {i+1}?",
                answer=f"Answer {i+1}",
                order=i + 1,
            )
            db_session.add(qna)
        await db_session.commit()

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = None

            response = await client.post(
                f"/api/v1/preparation/{preparation_session.id}/detective/question",
                headers={"Authorization": token},
            )

            # Should complete detective stage after max questions
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True


class TestDraftGeneration:
    """Tests for STAR answer draft generation."""

    @pytest.mark.asyncio
    async def test_generate_draft_requires_detective_complete(
        self, client, pro_user, preparation_session
    ):
        """Cannot generate draft until detective stage is complete."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{preparation_session.id}/generate-draft",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "not draft" in response.json()["detail"].lower() or "detective" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_generate_draft_no_qna_fails(
        self, client, pro_user, db_session, test_question_for_prep
    ):
        """Cannot generate draft without Q&A from detective stage."""
        # Create prep in draft stage but with no Q&A
        prep = AnswerPreparation(
            id=uuid4(),
            user_id=pro_user.id,
            question_id=test_question_for_prep.id,
            stage=PreparationStage.DRAFT,
        )
        db_session.add(prep)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{prep.id}/generate-draft",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "no q&a" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_ghostwriter_generates_star_answer(
        self, client, pro_user, db_session, test_question_for_prep
    ):
        """Ghostwriter generates STAR-formatted answer from Q&A."""
        # Create prep in draft stage with Q&A
        prep = AnswerPreparation(
            id=uuid4(),
            user_id=pro_user.id,
            question_id=test_question_for_prep.id,
            stage=PreparationStage.DRAFT,
        )
        db_session.add(prep)

        qna = PreparationQnA(
            id=uuid4(),
            preparation_id=prep.id,
            question="What was the project?",
            answer="A critical deadline for a new payment system.",
            order=1,
        )
        db_session.add(qna)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = None  # Use fallback

            response = await client.post(
                f"/api/v1/preparation/{prep.id}/generate-draft",
                headers={"Authorization": token},
            )

            assert response.status_code == 200
            data = response.json()
            assert "draft_answer" in data
            # Fallback includes STAR structure
            assert "Situation" in data["draft_answer"]
            assert data["stage"] == "practice"


class TestDraftRetrieval:
    """Tests for retrieving and updating drafts."""

    @pytest.mark.asyncio
    async def test_get_draft_success(self, client, pro_user, preparation_with_draft):
        """Getting draft returns the generated answer."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_with_draft.id}/draft",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "draft_answer" in data
        assert "Situation" in data["draft_answer"]

    @pytest.mark.asyncio
    async def test_get_draft_not_generated_yet(
        self, client, pro_user, preparation_session
    ):
        """Getting draft before generation returns 404."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_session.id}/draft",
            headers={"Authorization": token},
        )

        assert response.status_code == 404
        assert "not yet generated" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_draft_success(self, client, pro_user, preparation_with_draft):
        """Updating draft saves changes."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        new_draft = "**Situation**: Updated situation...\n**Task**: New task...\n**Action**: Different action...\n**Result**: Better outcome."

        response = await client.patch(
            f"/api/v1/preparation/{preparation_with_draft.id}/draft",
            headers={"Authorization": token},
            json={"draft_answer": new_draft},
        )

        assert response.status_code == 200
        data = response.json()
        assert "Updated situation" in data["draft_answer"]

    @pytest.mark.asyncio
    async def test_update_draft_before_generation_fails(
        self, client, pro_user, preparation_session
    ):
        """Cannot update draft before it's generated."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.patch(
            f"/api/v1/preparation/{preparation_session.id}/draft",
            headers={"Authorization": token},
            json={"draft_answer": "New draft content"},
        )

        assert response.status_code == 400
        assert "not yet generated" in response.json()["detail"].lower()


class TestPracticeDelivery:
    """Tests for practice delivery submission."""

    @pytest.mark.asyncio
    async def test_start_practice_success(self, client, pro_user, preparation_with_draft):
        """Starting practice creates a delivery attempt."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{preparation_with_draft.id}/practice/start",
            headers={"Authorization": token},
        )

        assert response.status_code == 201
        data = response.json()
        assert "attempt_id" in data
        assert data["stage"] == "practice"

    @pytest.mark.asyncio
    async def test_start_practice_without_draft_fails(
        self, client, pro_user, preparation_session
    ):
        """Cannot start practice without a draft."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{preparation_session.id}/practice/start",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_submit_practice_audio_not_found(
        self, client, pro_user, preparation_with_draft
    ):
        """Submitting practice with missing audio file returns 404."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{preparation_with_draft.id}/practice/submit",
            headers={"Authorization": token},
            json={"audio_url": "/uploads/audio/nonexistent.webm"},
        )

        assert response.status_code == 404
        assert "audio file not found" in response.json()["detail"].lower()


class TestDeliveryRating:
    """Tests for rating delivery attempts."""

    @pytest.mark.asyncio
    async def test_rate_delivery_attempt_not_found(
        self, client, pro_user, preparation_with_draft
    ):
        """Rating nonexistent attempt returns 404."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{preparation_with_draft.id}/rate-delivery",
            headers={"Authorization": token},
            json={"attempt_id": str(uuid4())},
        )

        assert response.status_code == 404
        assert "attempt not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_rate_delivery_no_transcript_fails(
        self, client, pro_user, preparation_with_draft, db_session
    ):
        """Rating attempt without transcript returns 400."""
        # Create attempt without transcript
        attempt = DeliveryAttempt(
            id=uuid4(),
            preparation_id=preparation_with_draft.id,
            audio_url="/uploads/audio/test.webm",
            transcript=None,  # No transcript
        )
        db_session.add(attempt)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.post(
            f"/api/v1/preparation/{preparation_with_draft.id}/rate-delivery",
            headers={"Authorization": token},
            json={"attempt_id": str(attempt.id)},
        )

        assert response.status_code == 400
        assert "no transcript" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_rate_delivery_success(
        self, client, pro_user, preparation_with_draft, db_session
    ):
        """Rating attempt with transcript succeeds."""
        # Create attempt with transcript
        attempt = DeliveryAttempt(
            id=uuid4(),
            preparation_id=preparation_with_draft.id,
            audio_url="/uploads/audio/test.webm",
            transcript="I led a team of 5 engineers on a critical payment system project. We had a tight deadline, so I organized daily standups. We delivered on time.",
        )
        db_session.add(attempt)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        with patch("app.api.preparation.DeliveryRatingService") as mock_service:
            mock_rating = MagicMock()
            mock_rating.delivery_score = 85.0
            mock_rating.content_coverage = 90.0
            mock_rating.key_points = 80.0
            mock_rating.flow_structure = 85.0
            mock_rating.comparison_feedback = "Good delivery with strong structure."
            mock_rating.strengths = ["Clear structure", "Good examples"]
            mock_rating.improvements = ["Add more metrics"]

            mock_instance = AsyncMock()
            mock_instance.rate_delivery = AsyncMock(return_value=mock_rating)
            mock_service.return_value = mock_instance

            response = await client.post(
                f"/api/v1/preparation/{preparation_with_draft.id}/rate-delivery",
                headers={"Authorization": token},
                json={"attempt_id": str(attempt.id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["delivery_score"] == 85.0
            assert len(data["strengths"]) > 0
            assert data["stage"] == "complete"


class TestComparison:
    """Tests for draft vs delivery comparison."""

    @pytest.mark.asyncio
    async def test_get_comparison_success(
        self, client, pro_user, preparation_with_draft, db_session
    ):
        """Getting comparison returns draft and delivery side by side."""
        # Create rated attempt
        attempt = DeliveryAttempt(
            id=uuid4(),
            preparation_id=preparation_with_draft.id,
            audio_url="/uploads/audio/test.webm",
            transcript="My delivery of the answer...",
            delivery_score=80.0,
            comparison_feedback="Good attempt!",
            comparison_details={
                "strengths": ["Good structure"],
                "improvements": ["More detail needed"],
            },
        )
        db_session.add(attempt)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_with_draft.id}/comparison",
            headers={"Authorization": token},
            params={"attempt_id": str(attempt.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert "draft" in data
        assert "delivery" in data
        assert data["delivery_score"] == 80.0
        assert "Good structure" in data["strengths"]

    @pytest.mark.asyncio
    async def test_get_comparison_attempt_not_found(
        self, client, pro_user, preparation_with_draft
    ):
        """Comparison with invalid attempt ID returns 404."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_with_draft.id}/comparison",
            headers={"Authorization": token},
            params={"attempt_id": str(uuid4())},
        )

        assert response.status_code == 404


class TestListPreparations:
    """Tests for listing user preparations."""

    @pytest.mark.asyncio
    async def test_list_preparations_returns_user_preps(
        self, client, pro_user, preparation_with_draft
    ):
        """Listing preparations returns only current user's preps."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            "/api/v1/preparation",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "preparations" in data
        assert len(data["preparations"]) >= 1

    @pytest.mark.asyncio
    async def test_list_preparations_empty_for_new_user(self, client, db_session):
        """New user has empty preparations list."""
        # Create new pro user
        new_user = User(
            id=str(uuid4()),
            email=f"newpro_{uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("TestPassword123!"),
            subscription_tier=SubscriptionTier.PRO,
        )
        db_session.add(new_user)
        await db_session.commit()

        token = await register_and_login(
            client, email=new_user.email, password="TestPassword123!"
        )

        response = await client.get(
            "/api/v1/preparation",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["preparations"] == []


class TestPreparationState:
    """Tests for getting complete preparation state."""

    @pytest.mark.asyncio
    async def test_get_state_returns_complete_data(
        self, client, pro_user, preparation_with_draft, db_session
    ):
        """Getting state returns question, Q&A, draft, and attempts."""
        # Add Q&A and attempt
        qna = PreparationQnA(
            id=uuid4(),
            preparation_id=preparation_with_draft.id,
            question="What was the context?",
            answer="A tight deadline project.",
            order=1,
        )
        db_session.add(qna)

        attempt = DeliveryAttempt(
            id=uuid4(),
            preparation_id=preparation_with_draft.id,
            transcript="My delivery...",
        )
        db_session.add(attempt)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_with_draft.id}/state",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "preparation_id" in data
        assert "question" in data
        assert "qna" in data
        assert "draft_answer" in data
        assert "attempts" in data
        assert len(data["qna"]) >= 1
        assert len(data["attempts"]) >= 1

    @pytest.mark.asyncio
    async def test_get_state_wrong_user_returns_404(
        self, client, db_session, preparation_with_draft
    ):
        """Getting state for another user's preparation returns 404."""
        # Create different user
        other_user = User(
            id=str(uuid4()),
            email=f"other_{uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("TestPassword123!"),
            subscription_tier=SubscriptionTier.PRO,
        )
        db_session.add(other_user)
        await db_session.commit()

        token = await register_and_login(
            client, email=other_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_with_draft.id}/state",
            headers={"Authorization": token},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetAttempts:
    """Tests for retrieving delivery attempts."""

    @pytest.mark.asyncio
    async def test_get_attempts_returns_all(
        self, client, pro_user, preparation_with_draft, db_session
    ):
        """Getting attempts returns all attempts for preparation."""
        # Create multiple attempts
        for i in range(3):
            attempt = DeliveryAttempt(
                id=uuid4(),
                preparation_id=preparation_with_draft.id,
                transcript=f"Attempt {i+1}",
            )
            db_session.add(attempt)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_with_draft.id}/attempts",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "attempts" in data
        assert len(data["attempts"]) >= 3

    @pytest.mark.asyncio
    async def test_get_attempts_empty_list(
        self, client, pro_user, preparation_with_draft
    ):
        """Getting attempts with no attempts returns empty list."""
        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        response = await client.get(
            f"/api/v1/preparation/{preparation_with_draft.id}/attempts",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["attempts"] == []


class TestStageTransitions:
    """Tests for stage progression validation."""

    @pytest.mark.asyncio
    async def test_stage_progression_detective_to_draft(
        self, client, pro_user, db_session, test_question_for_prep
    ):
        """Stage transitions from detective to draft after enough questions."""
        prep = AnswerPreparation(
            id=uuid4(),
            user_id=pro_user.id,
            question_id=test_question_for_prep.id,
            stage=PreparationStage.DETECTIVE,
        )
        db_session.add(prep)

        # Add 4 answered questions (enough to trigger ENOUGH_INFO)
        for i in range(4):
            qna = PreparationQnA(
                id=uuid4(),
                preparation_id=prep.id,
                question=f"Question {i+1}?",
                answer=f"Answer {i+1}",
                order=i + 1,
            )
            db_session.add(qna)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = None

            response = await client.post(
                f"/api/v1/preparation/{prep.id}/detective/question",
                headers={"Authorization": token},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True

    @pytest.mark.asyncio
    async def test_stage_progression_practice_to_complete(
        self, client, pro_user, preparation_with_draft, db_session
    ):
        """Stage transitions from practice to complete after rating."""
        # Create attempt with transcript
        attempt = DeliveryAttempt(
            id=uuid4(),
            preparation_id=preparation_with_draft.id,
            transcript="My delivery of the practiced answer.",
        )
        db_session.add(attempt)
        await db_session.commit()

        token = await register_and_login(
            client, email=pro_user.email, password="TestPassword123!"
        )

        with patch("app.api.preparation.DeliveryRatingService") as mock_service:
            mock_rating = MagicMock()
            mock_rating.delivery_score = 85.0
            mock_rating.content_coverage = 90.0
            mock_rating.key_points = 80.0
            mock_rating.flow_structure = 85.0
            mock_rating.comparison_feedback = "Good job!"
            mock_rating.strengths = ["Clear"]
            mock_rating.improvements = ["More detail"]

            mock_instance = AsyncMock()
            mock_instance.rate_delivery = AsyncMock(return_value=mock_rating)
            mock_service.return_value = mock_instance

            response = await client.post(
                f"/api/v1/preparation/{preparation_with_draft.id}/rate-delivery",
                headers={"Authorization": token},
                json={"attempt_id": str(attempt.id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["stage"] == "complete"
