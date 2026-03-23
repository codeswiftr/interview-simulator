"""Gap tests for users API — tests not covered in existing test files.

Tests to add:
- test_login_sets_last_login_at
- test_update_profile_full_name_and_email_change_simultaneously

All tests are PURE UNIT TESTS — no database required.
"""

from datetime import UTC, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.users import login, update_profile
from app.models.user import ExperienceLevel, UserLogin, UserUpdate


def _mock_session():
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _mock_user(
    email="test@example.com",
    user_id=None,
    password_hash="hashed",
    full_name="Test User",
):
    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = email
    user.hashed_password = password_hash
    user.full_name = full_name
    user.experience_level = ExperienceLevel.MID
    user.is_active = True
    user.stripe_customer_id = None
    user.stripe_subscription_id = None
    user.subscription_status = None
    user.last_login_at = None
    user.refresh_token = None
    user.refresh_token_expires_at = None
    return user


def _mock_request(host="127.0.0.1"):
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = host
    return request


class TestLoginSetsLastLoginAt:
    """Tests that login correctly sets last_login_at timestamp."""

    @pytest.mark.asyncio
    async def test_login_sets_last_login_at(self):
        """Successful login should set user.last_login_at to current time."""
        session = _mock_session()
        request = _mock_request()
        user = _mock_user(email="user@example.com", password_hash="bcrypt_hash")
        payload = UserLogin(email="user@example.com", password="CorrectPass1!")

        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        fake_refresh_expires = timedelta(days=30)

        with (
            patch("app.services.account_lockout.AccountLockoutService") as mock_cls,
            patch("app.api.users.verify_password", return_value=True),
            patch("app.api.users.needs_rehash", return_value=False),
            patch("app.api.users.create_access_token", return_value="access_tok"),
            patch(
                "app.api.users.create_refresh_token",
                return_value=("refresh_tok", fake_refresh_expires),
            ),
            patch("app.security.hash_refresh_token", return_value="hashed_refresh"),
        ):
            mock_service = AsyncMock()
            mock_service.is_account_locked = AsyncMock(return_value=(False, None))
            mock_service.record_login_attempt = AsyncMock()
            mock_cls.return_value = mock_service

            await login(payload, request, session)

        assert user.last_login_at is not None
        assert user.last_login_at.tzinfo is not None


class TestUpdateProfileMultipleFields:
    """Tests for updating multiple profile fields simultaneously."""

    @pytest.mark.asyncio
    async def test_update_profile_full_name_and_email_change_simultaneously(self):
        """When both full_name and email change, both should be processed."""
        session = _mock_session()
        user = _mock_user(email="old@example.com", full_name="Old Name")

        no_conflict = MagicMock()
        no_conflict.first.return_value = None
        session.exec.return_value = no_conflict

        updates = UserUpdate(full_name="New Name", email="new@example.com")

        with patch("app.api.users.EmailService") as mock_email_cls:
            mock_email = MagicMock()
            mock_email.send_email_verification = AsyncMock()
            mock_email_cls.return_value = mock_email

            with pytest.raises(HTTPException) as exc_info:
                await update_profile(updates, user, session)

            assert exc_info.value.status_code == 202
            assert user.full_name == "New Name"
            mock_email.send_email_verification.assert_awaited_once()
