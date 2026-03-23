"""Tests for API key authentication dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies_api_key import (
    get_user_flexible,
    get_user_from_api_key,
    require_api_key,
)


class TestGetUserFromAPIKey:
    """Tests for get_user_from_api_key dependency."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_credentials(self):
        """Returns None when no credentials provided."""
        result = await get_user_from_api_key(
            credentials=None,
            session=AsyncMock(spec=AsyncSession),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_key_prefix(self):
        """Returns None when key doesn't start with 'is_'."""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "invalid_key"

        result = await get_user_from_api_key(
            credentials=credentials,
            session=AsyncMock(spec=AsyncSession),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_user_for_valid_api_key(self):
        """Returns user when API key is valid."""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "is_1234567890abcdef"

        mock_user = MagicMock()
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "app.dependencies_api_key.api_key_service.verify_api_key_and_get_user",
            new_callable=AsyncMock,
        ) as mock_verify:
            mock_verify.return_value = mock_user

            result = await get_user_from_api_key(
                credentials=credentials,
                session=mock_session,
            )

        assert result == mock_user
        mock_verify.assert_called_once_with(mock_session, "is_1234567890abcdef")


class TestRequireAPIKey:
    """Tests for require_api_key dependency."""

    @pytest.mark.asyncio
    async def test_raises_exception_when_no_user(self):
        """Raises HTTPException when user is None."""
        with patch(
            "app.dependencies_api_key.get_user_from_api_key",
            new_callable=AsyncMock,
        ) as mock_get_user:
            mock_get_user.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await require_api_key(
                    user=None,
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_returns_user_when_provided(self):
        """Returns user when user is provided."""
        mock_user = MagicMock()

        result = await require_api_key(user=mock_user)

        assert result == mock_user


class TestGetUserFlexibleJWTBranch:
    """Tests for the JWT path of get_user_flexible() after Fix 1 (sync get_jwt_auth)."""

    @pytest.mark.asyncio
    async def test_jwt_token_returns_user_from_database(self):
        """JWT branch: valid token with a known user is returned from the DB."""
        mock_user = MagicMock()

        # Credentials that do NOT start with 'is_' → JWT branch is taken.
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "a.valid.jwt"

        # Payload stub returned by auth.decode_token()
        mock_payload = MagicMock()
        mock_payload.sub = "user-uuid-1234"

        # auth instance returned by get_jwt_auth() (synchronous)
        mock_auth = MagicMock()
        mock_auth.decode_token.return_value = mock_payload

        # DB session that finds the user
        mock_result = MagicMock()
        mock_result.first.return_value = mock_user
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.exec.return_value = mock_result

        # get_jwt_auth is imported lazily inside get_user_flexible, so we patch
        # it at its source module rather than at the app.dependencies_api_key namespace.
        with patch(
            "forge_shared.auth.dependencies.get_jwt_auth",
            return_value=mock_auth,
        ):
            result = await get_user_flexible(
                credentials=credentials,
                session=mock_session,
            )

        assert result == mock_user
        mock_auth.decode_token.assert_called_once_with("a.valid.jwt")

    @pytest.mark.asyncio
    async def test_jwt_token_invalid_raises_401(self):
        """JWT branch: decode failure raises HTTP 401."""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "bad.token.value"

        mock_auth = MagicMock()
        mock_auth.decode_token.side_effect = ValueError("invalid token")

        with patch(
            "forge_shared.auth.dependencies.get_jwt_auth",
            return_value=mock_auth,
        ), pytest.raises(HTTPException) as exc_info:
            await get_user_flexible(
                credentials=credentials,
                session=AsyncMock(spec=AsyncSession),
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "validate" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_jwt_token_user_not_found_raises_401(self):
        """JWT branch: valid token but non-existent user raises HTTP 401."""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "good.token.for.unknown.user"

        mock_payload = MagicMock()
        mock_payload.sub = "ghost-user-uuid"

        mock_auth = MagicMock()
        mock_auth.decode_token.return_value = mock_payload

        # DB returns no user
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.exec.return_value = mock_result

        with patch(
            "forge_shared.auth.dependencies.get_jwt_auth",
            return_value=mock_auth,
        ), pytest.raises(HTTPException) as exc_info:
            await get_user_flexible(
                credentials=credentials,
                session=mock_session,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "user not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_no_credentials_raises_401(self):
        """get_user_flexible raises HTTP 401 when no credentials are provided."""
        with pytest.raises(HTTPException) as exc_info:
            await get_user_flexible(
                credentials=None,
                session=AsyncMock(spec=AsyncSession),
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "missing" in exc_info.value.detail.lower()
