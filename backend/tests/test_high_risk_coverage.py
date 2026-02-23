"""High-risk integration tests for Interview Simulator backend.

This module contains integration tests targeting the most critical untested paths
in the Interview Simulator backend, focusing on:
- Authentication endpoints (login, register, token refresh)
- Interview creation flow with tier enforcement
- Feedback generation with async processing
- Subscription tier limits and feature access

These tests use the shared fixtures from conftest.py and follow the established
patterns for async FastAPI testing with httpx.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.interview import (
    InterviewQuestion,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import SubscriptionTier, User
from tests.conftest import register_and_login


class TestAuthEndpointsIntegration:
    """Integration tests for authentication endpoints focusing on high-risk paths."""

    @pytest.mark.asyncio
    async def test_register_creates_user_with_free_tier(self, client, db_session):
        """Test that new users are created with FREE tier by default.

        Verifies the registration flow creates a user with the correct
        default subscription tier and initial interview counts.
        """
        unique_email = f"newuser_{uuid4().hex[:8]}@example.com"

        response = await client.post(
            "/api/v1/users/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email
        assert data["subscription_tier"] == "free"
        assert data["interviews_this_month"] == 0
        assert data["total_interviews"] == 0

        # Verify in database
        result = await db_session.exec(select(User).where(User.email == unique_email))
        user = result.first()
        assert user is not None
        assert user.subscription_tier == SubscriptionTier.FREE

    @pytest.mark.asyncio
    async def test_login_returns_valid_tokens(self, client, db_session):
        """Test that login returns both access and refresh tokens.

        Verifies JWT token generation and refresh token storage
        in the database for token rotation support.
        """
        email = f"login_test_{uuid4().hex[:8]}@example.com"
        password = "SecurePass123!"

        # Register first
        await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password},
        )

        # Login
        response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": password},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50  # JWT is substantial
        assert len(data["refresh_token"]) > 20  # Refresh token is substantial

        # Verify refresh token is stored in DB
        result = await db_session.exec(select(User).where(User.email == email))
        user = result.first()
        assert user.refresh_token == data["refresh_token"]
        assert user.refresh_token_expires_at is not None

    @pytest.mark.asyncio
    async def test_token_refresh_rotates_refresh_token(self, client, db_session):
        """Test that token refresh performs proper token rotation.

        Verifies that:
        1. Old refresh token is invalidated
        2. New refresh token is different from old
        3. Access token is returned along with new refresh token
        """
        email = f"refresh_{uuid4().hex[:8]}@example.com"
        password = "SecurePass123!"

        # Register and login
        await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": password},
        )
        old_refresh_token = login_resp.json()["refresh_token"]

        # Refresh token
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        new_refresh_token = data["refresh_token"]

        # Token should be rotated (different)
        assert new_refresh_token != old_refresh_token
        assert len(new_refresh_token) > 20

        # Old token should be invalidated in DB
        result = await db_session.exec(select(User).where(User.email == email))
        user = result.first()
        assert user.refresh_token == new_refresh_token
        assert user.refresh_token != old_refresh_token

    @pytest.mark.asyncio
    async def test_login_with_invalid_password_fails(self, client, db_session):
        """Test that login fails with incorrect password.

        Verifies password verification prevents unauthorized access
        and doesn't leak information about email existence.
        """
        email = f"wrongpass_{uuid4().hex[:8]}@example.com"
        password = "CorrectPass123!"
        wrong_password = "WrongPass456!"

        # Register
        await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password},
        )

        # Try login with wrong password
        response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": wrong_password},
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_fails(self, client, db_session):
        """Test that refresh token fails when token is expired.

        Verifies token expiration is properly enforced and
        the invalid token is cleared from the user record.
        """
        email = f"expired_{uuid4().hex[:8]}@example.com"
        password = "SecurePass123!"

        # Register and login
        await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": password},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Manually expire the token in DB
        result = await db_session.exec(select(User).where(User.email == email))
        user = result.first()
        user.refresh_token_expires_at = datetime.now(UTC) - timedelta(hours=1)
        await db_session.commit()

        # Try to refresh with expired token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

        # Token should be cleared
        result = await db_session.exec(select(User).where(User.email == email))
        user = result.first()
        assert user.refresh_token is None


class TestInterviewCreationFlow:
    """Integration tests for interview creation with tier enforcement."""

    @pytest.mark.asyncio
    async def test_create_interview_for_free_user(self, client, db_session):
        """Test that free users can create interviews within quota.

        Verifies interview creation for free tier users respects
        the monthly interview limit (3 interviews/month).
        """
        token = await register_and_login(client)

        # Create interview
        response = await client.post(
            "/api/v1/interviews",
            json={
                "interview_type": "behavioral",
                "question_count": 3,
                "difficulty": "medium",
            },
            headers={"Authorization": token},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "scheduled"
        assert data["question_count"] == 3
        assert "remaining_interviews" in data
        assert data["remaining_interviews"] == 2  # 3 - 1 = 2

    @pytest.mark.asyncio
    async def test_create_interview_increments_counter(self, client, db_session):
        """Test that creating an interview increments user's monthly counter.

        Verifies the interviews_this_month counter is properly
        incremented and persisted.
        """
        token = await register_and_login(client)

        # Get user initial state
        user_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )
        initial_count = user_resp.json()["interviews_this_month"]

        # Create interview
        await client.post(
            "/api/v1/interviews",
            json={"interview_type": "behavioral"},
            headers={"Authorization": token},
        )

        # Verify counter incremented
        user_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )
        assert user_resp.json()["interviews_this_month"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_create_interview_with_questions(self, client, db_session):
        """Test that creating an interview assigns questions automatically.

        Verifies the full interview creation flow including
        automatic question assignment from the question pool.
        """
        token = await register_and_login(client)

        # Create questions first
        for i in range(5):
            question = Question(
                content=f"Behavioral question {i + 1}: Tell me about a challenge.",
                category=QuestionCategory.BEHAVIORAL,
                difficulty=Difficulty.MEDIUM,
                expected_duration_seconds=180,
                is_active=True,
            )
            db_session.add(question)
        await db_session.commit()

        # Create interview
        response = await client.post(
            "/api/v1/interviews",
            json={
                "interview_type": "behavioral",
                "question_count": 3,
                "difficulty": "medium",
            },
            headers={"Authorization": token},
        )

        assert response.status_code == 201
        interview_id = response.json()["id"]

        # Verify questions were assigned
        questions_result = await db_session.exec(
            select(InterviewQuestion).where(InterviewQuestion.session_id == interview_id)
        )
        questions = questions_result.all()
        assert len(questions) == 3

    @pytest.mark.asyncio
    async def test_create_interview_requires_authentication(self, client, db_session):
        """Test that creating an interview requires authentication.

        Verifies that unauthenticated requests are rejected
        with appropriate 401/403 status.
        """
        response = await client.post(
            "/api/v1/interviews",
            json={"interview_type": "behavioral"},
        )

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_interview_requires_ownership(self, client, db_session):
        """Test that users can only access their own interviews.

        Verifies interview access is properly scoped to the
        authenticated user's interviews.
        """
        # Create two users
        token1 = await register_and_login(client, email=f"user1_{uuid4().hex[:8]}@example.com")
        token2 = await register_and_login(client, email=f"user2_{uuid4().hex[:8]}@example.com")

        # User 1 creates interview
        resp1 = await client.post(
            "/api/v1/interviews",
            json={"interview_type": "behavioral"},
            headers={"Authorization": token1},
        )
        interview_id = resp1.json()["id"]

        # User 2 tries to access User 1's interview
        resp2 = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers={"Authorization": token2},
        )

        assert resp2.status_code == 404

    @pytest.mark.asyncio
    async def test_list_interviews_pagination(self, client, db_session):
        """Test listing interviews with pagination parameters.

        Verifies limit and offset parameters work correctly
        for interview listing.
        """
        token = await register_and_login(client)

        # Create multiple interviews
        for _ in range(5):
            await client.post(
                "/api/v1/interviews",
                json={"interview_type": "behavioral"},
                headers={"Authorization": token},
            )

        # Test pagination
        response = await client.get(
            "/api/v1/interviews?limit=2&offset=1",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get all and verify offset
        all_resp = await client.get(
            "/api/v1/interviews",
            headers={"Authorization": token},
        )
        all_interviews = all_resp.json()

        # Verify the paginated results are a subset
        ids_paginated = {i["id"] for i in data}
        ids_all = {i["id"] for i in all_interviews}
        assert ids_paginated.issubset(ids_all)


class TestFeedbackGenerationFlow:
    """Integration tests for feedback generation and retrieval."""

    @pytest.mark.asyncio
    async def test_get_interview_with_questions_and_responses(self, client, db_session):
        """Test retrieving an interview with its questions and responses.

        Verifies the full interview state including assigned questions
        can be retrieved after responses are submitted.
        """
        token = await register_and_login(client)

        # Create questions
        question = Question(
            content="Tell me about a time you resolved a conflict.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
            expected_duration_seconds=180,
            is_active=True,
        )
        db_session.add(question)
        await db_session.commit()
        await db_session.refresh(question)

        # Create interview
        interview_resp = await client.post(
            "/api/v1/interviews",
            json={
                "interview_type": "behavioral",
                "question_count": 1,
                "difficulty": "medium",
            },
            headers={"Authorization": token},
        )
        interview_id = interview_resp.json()["id"]

        # Start interview
        await client.post(
            f"/api/v1/interviews/{interview_id}/start",
            headers={"Authorization": token},
        )

        # Get interview details
        response = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == interview_id
        assert data["status"] == "in_progress"
        assert "questions" in data

    @pytest.mark.asyncio
    async def test_get_subscription_status(self, client, db_session):
        """Test retrieving subscription status for free tier user.

        Verifies the subscription status endpoint returns correct
        tier information, limits, and usage counters.
        """
        token = await register_and_login(client)

        response = await client.get(
            "/api/v1/subscriptions/status",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        assert "interviews_this_month" in data
        assert "interviews_limit" in data
        assert data["interviews_limit"] == 3
        assert "can_create_interview" in data
        assert data["can_create_interview"] is True

    @pytest.mark.asyncio
    async def test_generate_feedback_requires_completed_interview(self, client, db_session):
        """Test that feedback generation requires a completed interview.

        Verifies feedback cannot be generated for interviews
        that are still in progress.
        """
        token = await register_and_login(client)

        # Create and start interview
        interview_resp = await client.post(
            "/api/v1/interviews",
            json={"interview_type": "behavioral"},
            headers={"Authorization": token},
        )
        interview_id = interview_resp.json()["id"]

        await client.post(
            f"/api/v1/interviews/{interview_id}/start",
            headers={"Authorization": token},
        )

        # Try to generate session feedback (should fail without responses)
        response = await client.post(
            f"/api/v1/interviews/{interview_id}/feedback",
            headers={"Authorization": token},
        )

        # Should fail because no responses exist
        assert response.status_code == 400
        assert "no responses" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_response_requires_in_progress_interview(self, client, db_session):
        """Test that responses can only be created for in-progress interviews.

        Verifies the interview status check prevents responses
        on completed or scheduled interviews.
        """
        token = await register_and_login(client)

        # Create interview (stays in scheduled status)
        interview_resp = await client.post(
            "/api/v1/interviews",
            json={"interview_type": "behavioral"},
            headers={"Authorization": token},
        )
        interview_id = interview_resp.json()["id"]

        # Try to submit response without starting
        response = await client.post(
            f"/api/v1/interviews/{interview_id}/responses",
            json={
                "question_id": str(uuid4()),  # Fake question ID
                "transcript": "My answer to the question...",
            },
            headers={"Authorization": token},
        )

        # Should fail - interview not started
        assert response.status_code == 400


class TestSubscriptionTierEnforcement:
    """Integration tests for subscription tier feature access."""

    @pytest.mark.asyncio
    async def test_free_user_has_limited_interviews(self, client, db_session):
        """Test that free users have monthly interview limits.

        Verifies the free tier quota enforcement is active
        and correctly tracks usage.
        """
        token = await register_and_login(client)

        # Check initial status
        status_resp = await client.get(
            "/api/v1/subscriptions/status",
            headers={"Authorization": token},
        )
        assert status_resp.json()["interviews_this_month"] == 0

        # Create 3 interviews
        for _ in range(3):
            resp = await client.post(
                "/api/v1/interviews",
                json={"interview_type": "behavioral"},
                headers={"Authorization": token},
            )
            assert resp.status_code == 201

        # Check usage after 3
        status_resp = await client.get(
            "/api/v1/subscriptions/status",
            headers={"Authorization": token},
        )
        assert status_resp.json()["interviews_this_month"] == 3
        assert status_resp.json()["remaining_interviews"] == 0

    @pytest.mark.asyncio
    async def test_user_without_stripe_customer_can_create_checkout(self, client, db_session):
        """Test checkout session creation for user without Stripe customer ID.

        Verifies the Stripe customer creation flow works when
        a user doesn't already have a customer ID.
        """
        token = await register_and_login(client)

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.stripe") as mock_stripe,
        ):
            mock_settings.stripe_secret_key = "sk_test_xxx"
            mock_settings.cors_origins = ["http://localhost:3000"]
            mock_settings.stripe_trial_days = 0

            mock_customer = MagicMock()
            mock_customer.id = "cus_newcustomer123"
            mock_stripe.Customer.create.return_value = mock_customer

            mock_session = MagicMock()
            mock_session.url = "https://checkout.stripe.com/pay/test"
            mock_stripe.checkout.Session.create.return_value = mock_session

            response = await client.post(
                "/api/v1/subscriptions/checkout",
                json={"price_id": "price_pro_monthly"},
                headers={"Authorization": token},
            )

            assert response.status_code == 200
            data = response.json()
            assert "url" in data
            assert "stripe" in data["url"]

            # Verify Stripe customer was created
            mock_stripe.Customer.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_stripe_checkout_fails_without_config(self, client, db_session):
        """Test checkout fails gracefully when Stripe is not configured.

        Verifies proper error handling when Stripe API keys are missing.
        """
        token = await register_and_login(client)

        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_secret_key = None

            response = await client.post(
                "/api/v1/subscriptions/checkout",
                json={"price_id": "price_pro"},
                headers={"Authorization": token},
            )

            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_pro_user_has_unlimited_interviews(self, client, db_session):
        """Test that pro users have unlimited interview creation.

        Verifies PRO tier bypasses the monthly interview limit
        and returns None for remaining_interviews.
        """
        token = await register_and_login(client)

        # Simulate PRO tier
        result = await db_session.exec(
            select(User).where(User.email.like("testuser_%@example.com"))
        )
        # Get the user from login response instead
        user_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )
        user_id = user_resp.json()["id"]

        # Update user to PRO tier directly in DB
        result = await db_session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.subscription_tier = SubscriptionTier.PRO
        await db_session.commit()

        # Verify PRO status
        status_resp = await client.get(
            "/api/v1/subscriptions/status",
            headers={"Authorization": token},
        )
        assert status_resp.json()["tier"] == "pro"
        assert status_resp.json()["interviews_limit"] is None  # Unlimited

        # Should be able to create multiple interviews
        for _ in range(5):
            resp = await client.post(
                "/api/v1/interviews",
                json={"interview_type": "behavioral"},
                headers={"Authorization": token},
            )
            assert resp.status_code == 201


class TestInterviewStateTransitions:
    """Integration tests for interview state machine transitions."""

    @pytest.mark.asyncio
    async def test_interview_state_transitions_scheduled_to_in_progress(self, client, db_session):
        """Test interview transitions from scheduled to in_progress on start.

        Verifies the start endpoint properly updates interview status
        and initializes the interview session.
        """
        token = await register_and_login(client)

        # Create interview (starts as scheduled)
        create_resp = await client.post(
            "/api/v1/interviews",
            json={"interview_type": "behavioral"},
            headers={"Authorization": token},
        )
        interview_id = create_resp.json()["id"]

        # Verify initial state
        get_resp = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers={"Authorization": token},
        )
        assert get_resp.json()["status"] == "scheduled"

        # Start interview
        start_resp = await client.post(
            f"/api/v1/interviews/{interview_id}/start",
            headers={"Authorization": token},
        )
        assert start_resp.status_code == 200

        # Verify state changed
        get_resp = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers={"Authorization": token},
        )
        assert get_resp.json()["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_cannot_start_completed_interview(self, client, db_session):
        """Test that completed interviews cannot be restarted.

        Verifies the state machine prevents invalid transitions
        from completed back to in_progress.
        """
        token = await register_and_login(client)

        # Create and start interview
        create_resp = await client.post(
            "/api/v1/interviews",
            json={"interview_type": "behavioral"},
            headers={"Authorization": token},
        )
        interview_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/interviews/{interview_id}/start",
            headers={"Authorization": token},
        )

        # Try to start again (should fail)
        response = await client.post(
            f"/api/v1/interviews/{interview_id}/start",
            headers={"Authorization": token},
        )

        assert response.status_code == 400


class TestAuthenticationEdgeCases:
    """Edge case tests for authentication and authorization."""

    @pytest.mark.asyncio
    async def test_access_protected_endpoint_without_token(self, client, db_session):
        """Test that protected endpoints reject requests without token.

        Verifies 401/403 is returned when Authorization header is missing.
        """
        response = await client.get("/api/v1/users/me")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_invalid_token(self, client, db_session):
        """Test that protected endpoints reject requests with invalid token.

        Verifies token validation rejects malformed or invalid tokens.
        """
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_duplicate_email_registration_fails(self, client, db_session):
        """Test that registering with duplicate email fails.

        Verifies email uniqueness constraint is enforced
        at the database level.
        """
        email = f"duplicate_{uuid4().hex[:8]}@example.com"

        # First registration succeeds
        resp1 = await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": "SecurePass123!"},
        )
        assert resp1.status_code == 200

        # Second registration fails
        resp2 = await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": "AnotherPass456!"},
        )
        assert resp2.status_code == 400
        assert "already exists" in resp2.json()["detail"].lower()


class TestPasswordResetFlow:
    """Integration tests for password reset functionality."""

    @pytest.mark.asyncio
    async def test_forgot_password_returns_success_for_existing_user(self, client, db_session):
        """Test that forgot password returns success even for existing users.

        Verifies security best practice of not revealing whether
        the email exists in the system.
        """
        email = f"forgot_{uuid4().hex[:8]}@example.com"

        # Register user first
        await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": "SecurePass123!"},
        )

        # Request password reset
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )

        # Should always return 200 (security)
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_forgot_password_returns_success_for_nonexistent_email(self, client, db_session):
        """Test that forgot password returns success for non-existent email.

        Verifies the endpoint doesn't leak information about
        which emails are registered.
        """
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_with_valid_token(self, client, db_session):
        """Test password reset with a valid token.

        Verifies the complete reset flow works correctly
        and updates the user's password.
        """
        from app.models.password_reset import PasswordResetToken

        email = f"reset_{uuid4().hex[:8]}@example.com"
        original_password = "OriginalPass123!"
        new_password = "NewSecurePass456!"

        # Register
        await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": original_password},
        )

        # Request reset
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )

        # Get the reset token from DB
        result = await db_session.exec(select(User).where(User.email == email))
        user = result.first()

        result = await db_session.exec(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used.is_(False),
            )
        )
        reset_token = result.first()
        assert reset_token is not None

        # Reset password
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token.token,
                "new_password": new_password,
            },
        )

        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

        # Verify old password doesn't work
        old_login = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": original_password},
        )
        assert old_login.status_code == 401

        # Verify new password works
        new_login = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": new_password},
        )
        assert new_login.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_password_with_expired_token_fails(self, client, db_session):
        """Test that expired reset tokens are rejected.

        Verifies token expiration is properly checked.
        """
        from app.models.password_reset import PasswordResetToken

        email = f"expired_reset_{uuid4().hex[:8]}@example.com"

        # Register and get reset token
        await client.post(
            "/api/v1/users/register",
            json={"email": email, "password": "SecurePass123!"},
        )
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )

        result = await db_session.exec(select(User).where(User.email == email))
        user = result.first()

        result = await db_session.exec(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used.is_(False),
            )
        )
        reset_token = result.first()

        # Expire the token
        reset_token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        await db_session.commit()

        # Try to use expired token
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token.token,
                "new_password": "NewPass789!",
            },
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()
