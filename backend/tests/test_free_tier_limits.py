"""Tests for free tier interview limits and usage tracking.

Tests cover:
- Free user under limit can create interviews
- Free user at limit gets 402 with upgrade details
- Pro user has unlimited interviews
- Usage resets at month boundary
- Remaining count is returned in responses
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlmodel import select

from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import SubscriptionTier, User
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_free_user_under_limit_can_create_interview(client, db_session):
    """Test that free user under limit (0-2 interviews) can create interview."""
    token = await register_and_login(client, email="free@example.com")

    # Verify user is on free tier
    result = await db_session.exec(select(User).where(User.email == "free@example.com"))
    user = result.first()
    assert user.subscription_tier == SubscriptionTier.FREE
    assert user.interviews_this_month == 0

    # Create first interview (should succeed)
    response = await client.post(
        "/api/v1/interviews",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 3,
        },
    )
    if response.status_code != 201:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["remaining_interviews"] == 2  # 3 - 1 = 2 remaining

    # Create second interview (should succeed)
    response = await client.post(
        "/api/v1/interviews",
        headers={"Authorization": token},
        json={
            "interview_type": "technical",
            "question_count": 2,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["remaining_interviews"] == 1  # 3 - 2 = 1 remaining

    # Create third interview (should succeed - last one)
    response = await client.post(
        "/api/v1/interviews",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 1,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["remaining_interviews"] == 0  # 3 - 3 = 0 remaining


@pytest.mark.asyncio
async def test_free_user_at_limit_gets_402_with_upgrade_details(client, db_session):
    """Test that free user at 3 interviews gets 402 with upgrade URL and price."""
    token = await register_and_login(client, email="limited@example.com")

    # Get user and set to limit
    result = await db_session.exec(select(User).where(User.email == "limited@example.com"))
    user = result.first()
    user.interviews_this_month = 3  # At limit
    await db_session.commit()

    # Mock settings to provide Stripe details
    with patch("app.config.settings") as mock_settings:
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly_123"
        mock_settings.frontend_url = "http://localhost:5173"

        # Attempt to create 4th interview (should fail with 402)
        response = await client.post(
            "/api/v1/interviews",
            headers={"Authorization": token},
            json={
                "interview_type": "behavioral",
                "question_count": 3,
            },
        )

        assert response.status_code == 402
        data = response.json()
        assert "detail" in data

        # Check upgrade details in response
        detail = data["detail"]
        assert (
            detail["message"]
            == "Free tier limit reached (3 interviews per month). Upgrade to Pro for unlimited interviews."
        )
        assert detail["interviews_used"] == 3
        assert detail["interviews_limit"] == 3
        assert (
            detail["upgrade_url"] == "http://localhost:5173/upgrade?price_id=price_pro_monthly_123"
        )
        assert detail["price_id"] == "price_pro_monthly_123"


@pytest.mark.asyncio
async def test_pro_user_has_unlimited_interviews(client, db_session):
    """Test that Pro tier user can create unlimited interviews."""
    token = await register_and_login(client, email="pro@example.com")

    # Upgrade user to Pro
    result = await db_session.exec(select(User).where(User.email == "pro@example.com"))
    user = result.first()
    user.subscription_tier = SubscriptionTier.PRO
    user.interviews_this_month = 10  # Already created 10
    await db_session.commit()

    # Create another interview (should succeed despite high count)
    response = await client.post(
        "/api/v1/interviews",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["remaining_interviews"] is None  # Pro has no limit

    # Verify counter incremented
    await db_session.refresh(user)
    assert user.interviews_this_month == 11


@pytest.mark.asyncio
async def test_team_user_has_unlimited_interviews(client, db_session):
    """Test that Team tier user can create unlimited interviews."""
    token = await register_and_login(client, email="team@example.com")

    # Upgrade user to Team
    result = await db_session.exec(select(User).where(User.email == "team@example.com"))
    user = result.first()
    user.subscription_tier = SubscriptionTier.TEAM
    user.interviews_this_month = 50  # Already created 50
    await db_session.commit()

    # Create another interview (should succeed)
    response = await client.post(
        "/api/v1/interviews",
        headers={"Authorization": token},
        json={
            "interview_type": "system_design",
            "question_count": 3,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["remaining_interviews"] is None  # Team has no limit


@pytest.mark.asyncio
async def test_usage_resets_at_month_boundary(client, db_session):
    """Test that interview counter resets when month changes."""
    token = await register_and_login(client, email="monthly@example.com")

    # Get user and set them to last month
    result = await db_session.exec(select(User).where(User.email == "monthly@example.com"))
    user = result.first()

    # Simulate user created last month with 3 interviews
    last_month = datetime.now(UTC) - timedelta(days=35)
    user.created_at = last_month
    user.interviews_this_month = 3  # At limit from last month
    await db_session.commit()

    # Create interview in current month (should reset counter and succeed)
    response = await client.post(
        "/api/v1/interviews",
        headers={"Authorization": token},
        json={
            "interview_type": "behavioral",
            "question_count": 2,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["remaining_interviews"] == 2  # Counter was reset, now at 1/3

    # Verify counter was reset and incremented
    await db_session.refresh(user)
    assert user.interviews_this_month == 1


@pytest.mark.asyncio
async def test_remaining_count_in_quick_practice(client, db_session):
    """Test that remaining count is returned in quick practice endpoint."""
    token = await register_and_login(client, email="practice@example.com")

    # Create a test question
    question = Question(
        content="Test question for quick practice",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Create quick practice (1st interview)
    response = await client.post(
        f"/api/v1/interviews/quick-practice?question_id={question.id}",
        headers={"Authorization": token},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["remaining_interviews"] == 2  # 2 remaining after 1st


@pytest.mark.asyncio
async def test_subscription_status_shows_correct_limit(client, db_session):
    """Test that /subscriptions/status endpoint shows correct limit of 3."""
    token = await register_and_login(client, email="status@example.com")

    response = await client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["interviews_limit"] == 3  # Changed from 5 to 3
    assert data["interviews_this_month"] == 0
    assert data["can_create_interview"] is True


@pytest.mark.asyncio
async def test_subscription_status_after_using_interviews(client, db_session):
    """Test subscription status after creating interviews."""
    token = await register_and_login(client, email="used@example.com")

    # Create 2 interviews
    for _ in range(2):
        await client.post(
            "/api/v1/interviews",
            headers={"Authorization": token},
            json={"interview_type": "behavioral", "question_count": 1},
        )

    # Check status
    response = await client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["interviews_this_month"] == 2
    assert data["interviews_limit"] == 3
    assert data["can_create_interview"] is True  # Still under limit

    # Create 3rd interview (at limit now)
    await client.post(
        "/api/v1/interviews",
        headers={"Authorization": token},
        json={"interview_type": "behavioral", "question_count": 1},
    )

    # Check status again
    response = await client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["interviews_this_month"] == 3
    assert data["can_create_interview"] is False  # At limit


@pytest.mark.asyncio
async def test_upgrade_url_not_provided_without_stripe(client, db_session):
    """Test that upgrade URL is None when Stripe is not configured."""
    token = await register_and_login(client, email="nostripe@example.com")

    # Set user to limit
    result = await db_session.exec(select(User).where(User.email == "nostripe@example.com"))
    user = result.first()
    user.interviews_this_month = 3
    await db_session.commit()

    # Mock settings with no Stripe
    with patch("app.config.settings") as mock_settings:
        mock_settings.stripe_secret_key = ""
        mock_settings.stripe_price_id_pro_monthly = ""
        mock_settings.frontend_url = "http://localhost:5173"

        # Attempt to create interview
        response = await client.post(
            "/api/v1/interviews",
            headers={"Authorization": token},
            json={"interview_type": "behavioral", "question_count": 1},
        )

        assert response.status_code == 402
        data = response.json()
        detail = data["detail"]
        assert detail["upgrade_url"] is None
        assert detail["price_id"] == ""


@pytest.mark.asyncio
async def test_concurrent_requests_dont_bypass_limit(client, db_session):
    """Test that concurrent requests don't bypass the limit through race conditions.

    The quota check and counter increment are performed atomically via a single
    UPDATE ... WHERE statement, preventing TOCTOU race conditions under concurrency.
    """
    import asyncio

    token = await register_and_login(client, email="concurrent@example.com")

    # Set user to 2 interviews (1 remaining)
    result = await db_session.exec(select(User).where(User.email == "concurrent@example.com"))
    user = result.first()
    user.interviews_this_month = 2
    await db_session.commit()

    # Try to create 3 interviews concurrently (only 1 should succeed)
    async def create_interview():
        return await client.post(
            "/api/v1/interviews",
            headers={"Authorization": token},
            json={"interview_type": "behavioral", "question_count": 1},
        )

    # Make 3 concurrent requests
    results = await asyncio.gather(
        create_interview(),
        create_interview(),
        create_interview(),
        return_exceptions=True,
    )

    # Count successes and failures
    success_count = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 201)
    payment_required_count = sum(
        1 for r in results if not isinstance(r, Exception) and r.status_code == 402
    )

    # At most 1 should succeed, rest should fail
    assert success_count <= 1
    assert payment_required_count >= 2

    # Verify final count is correct
    await db_session.refresh(user)
    assert user.interviews_this_month <= 3
