"""Pure unit tests for users API route logic.

Tests register, login, profile update, email verification, password change.
No database required — all DB interactions mocked.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.users import (
    change_password,
    delete_account,
    get_me,
    register_user,
    update_profile,
    verify_email,
)
from app.models.user import ExperienceLevel, PasswordChange, UserCreate, UserUpdate


def _mock_session():
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _mock_user(email="test@example.com", user_id=None, password_hash="hashed"):
    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = email
    user.hashed_password = password_hash
    user.full_name = "Test User"
    user.experience_level = ExperienceLevel.MID
    user.is_active = True
    user.stripe_customer_id = None
    user.stripe_subscription_id = None
    user.subscription_status = None
    user.last_login_at = None
    user.refresh_token = None
    user.refresh_token_expires_at = None
    return user


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_raises_on_duplicate_email(self):
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = MagicMock()  # existing user found
        session.exec.return_value = result

        payload = UserCreate(email="taken@example.com", password="ValidPass123!")
        request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await register_user(payload, request, session)
        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("app.api.users.hash_password", return_value="hashed")
    @patch("app.api.users.get_analytics")
    async def test_register_creates_user(self, mock_analytics, mock_hash):
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = None  # no existing user
        session.exec.return_value = result

        analytics = MagicMock()
        mock_analytics.return_value = analytics

        payload = UserCreate(email="New@Example.com", password="ValidPass123!")
        request = MagicMock()

        await register_user(payload, request, session)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        analytics.identify.assert_called_once()
        analytics.capture.assert_called_once()


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_invalid_token_raises_400(self):
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await verify_email("bad-token", session)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_used_token_raises_400(self):
        session = _mock_session()
        token_obj = MagicMock()
        token_obj.used = True
        result = MagicMock()
        result.first.return_value = token_obj
        session.exec.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await verify_email("used-token", session)
        assert "already been used" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_expired_token_raises_400(self):
        session = _mock_session()
        token_obj = MagicMock()
        token_obj.used = False
        token_obj.expires_at = datetime.now(UTC) - timedelta(hours=1)
        result = MagicMock()
        result.first.return_value = token_obj
        session.exec.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await verify_email("expired-token", session)
        assert "expired" in str(exc_info.value.detail)


class TestChangePassword:
    @pytest.mark.asyncio
    @patch("app.api.users.verify_password", return_value=False)
    async def test_wrong_current_password_raises_400(self, mock_verify):
        session = _mock_session()
        user = _mock_user()
        payload = PasswordChange(current_password="wrong", new_password="NewValid123!")

        with pytest.raises(HTTPException) as exc_info:
            await change_password(payload, user, session)
        assert exc_info.value.status_code == 400
        assert "incorrect" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("app.api.users.hash_password", return_value="new_hash")
    @patch("app.api.users.verify_password", return_value=True)
    async def test_successful_password_change(self, mock_verify, mock_hash):
        session = _mock_session()
        user = _mock_user()
        payload = PasswordChange(current_password="OldPass123!", new_password="NewValid123!")

        result = await change_password(payload, user, session)
        assert result["message"] == "Password updated successfully"
        assert user.hashed_password == "new_hash"
        session.commit.assert_awaited_once()


class TestGetMe:
    @pytest.mark.asyncio
    async def test_returns_current_user(self):
        user = _mock_user()
        result = await get_me(user)
        assert result == user


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_soft_deletes_user(self):
        session = _mock_session()
        user = _mock_user()

        await delete_account(user, session)
        assert user.is_active is False
        assert "deleted" in user.email
        assert user.full_name == "Deleted User"
        assert user.stripe_customer_id is None
        session.commit.assert_awaited_once()


class TestUpdateProfile:
    @pytest.mark.asyncio
    async def test_update_full_name(self):
        session = _mock_session()
        user = _mock_user()
        updates = UserUpdate(full_name="New Name")

        await update_profile(updates, user, session)
        assert user.full_name == "New Name"
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_experience_level(self):
        session = _mock_session()
        user = _mock_user()
        updates = UserUpdate(experience_level=ExperienceLevel.SENIOR)

        await update_profile(updates, user, session)
        assert user.experience_level == ExperienceLevel.SENIOR

    @pytest.mark.asyncio
    async def test_email_change_sends_verification(self):
        session = _mock_session()
        user = _mock_user(email="old@example.com")

        # First call: check for existing email — none found
        result_no_existing = MagicMock()
        result_no_existing.first.return_value = None
        session.exec.return_value = result_no_existing

        updates = UserUpdate(email="new@example.com")

        with patch("app.api.users.EmailService") as mock_email_cls:
            mock_email = MagicMock()
            mock_email.send_email_verification = AsyncMock()
            mock_email_cls.return_value = mock_email

            with pytest.raises(HTTPException) as exc_info:
                await update_profile(updates, user, session)
            assert exc_info.value.status_code == 202
            mock_email.send_email_verification.assert_awaited_once()
