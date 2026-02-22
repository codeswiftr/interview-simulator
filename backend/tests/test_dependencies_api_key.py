"""Tests for API key authentication dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies_api_key import (
    api_key_scheme,
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
