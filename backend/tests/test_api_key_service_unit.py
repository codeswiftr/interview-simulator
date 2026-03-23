"""Pure unit tests for api_key_service.

Tests key generation, hashing, verification, and CRUD operations.
No database required.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.api_key_service import (
    create_api_key,
    delete_api_key,
    generate_api_key,
    get_api_key_by_id,
    get_user_api_keys,
    hash_api_key,
    record_api_key_usage,
    update_api_key,
    verify_api_key,
    verify_api_key_and_get_user,
)


class TestGenerateApiKey:
    def test_starts_with_prefix(self):
        key = generate_api_key()
        assert key.startswith("is_")

    def test_length(self):
        key = generate_api_key()
        assert len(key) == 43

    def test_unique(self):
        keys = {generate_api_key() for _ in range(10)}
        assert len(keys) == 10


class TestHashAndVerifyApiKey:
    def test_hash_returns_string(self):
        h = hash_api_key("is_testkey123")
        assert isinstance(h, str)
        assert h.startswith("$2")

    def test_verify_correct_key(self):
        key = "is_testkey456"
        h = hash_api_key(key)
        assert verify_api_key(key, h) is True

    def test_verify_wrong_key(self):
        h = hash_api_key("is_correct")
        assert verify_api_key("is_wrong", h) is False

    def test_verify_invalid_hash(self):
        assert verify_api_key("is_key", "not_a_hash") is False


class TestCreateApiKey:
    @pytest.mark.asyncio
    async def test_creates_key(self):
        session = AsyncMock()
        user = MagicMock()

        user_result = MagicMock()
        user_result.first.return_value = user

        existing_result = MagicMock()
        existing_result.all.return_value = []

        session.exec.side_effect = [user_result, existing_result]

        key_data = MagicMock()
        key_data.name = "test key"
        key_data.scopes = [MagicMock(value="read"), MagicMock(value="write")]
        key_data.rate_limit = 100
        key_data.expires_at = None

        plain_key, api_key = await create_api_key(session, uuid4(), key_data)
        assert plain_key.startswith("is_")
        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_user_not_found(self):
        session = AsyncMock()
        user_result = MagicMock()
        user_result.first.return_value = None
        session.exec.return_value = user_result

        with pytest.raises(ValueError, match="User not found"):
            await create_api_key(session, uuid4(), MagicMock())

    @pytest.mark.asyncio
    async def test_raises_key_limit_exceeded(self):
        session = AsyncMock()
        user_result = MagicMock()
        user_result.first.return_value = MagicMock()

        existing_result = MagicMock()
        existing_result.all.return_value = [MagicMock() for _ in range(10)]

        session.exec.side_effect = [user_result, existing_result]

        with pytest.raises(ValueError, match="Maximum"):
            await create_api_key(session, uuid4(), MagicMock())


class TestGetUserApiKeys:
    @pytest.mark.asyncio
    async def test_returns_keys(self):
        session = AsyncMock()
        keys = [MagicMock(), MagicMock()]
        result = MagicMock()
        result.all.return_value = keys
        session.exec.return_value = result

        got = await get_user_api_keys(session, uuid4())
        assert len(got) == 2

    @pytest.mark.asyncio
    async def test_returns_empty(self):
        session = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        session.exec.return_value = result

        got = await get_user_api_keys(session, uuid4())
        assert got == []


class TestGetApiKeyById:
    @pytest.mark.asyncio
    async def test_returns_key(self):
        session = AsyncMock()
        key = MagicMock()
        result = MagicMock()
        result.first.return_value = key
        session.exec.return_value = result

        got = await get_api_key_by_id(session, uuid4(), uuid4())
        assert got is key

    @pytest.mark.asyncio
    async def test_returns_none(self):
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec.return_value = result

        got = await get_api_key_by_id(session, uuid4(), uuid4())
        assert got is None


class TestUpdateApiKey:
    @pytest.mark.asyncio
    @patch("app.services.api_key_service.get_api_key_by_id")
    async def test_updates_name(self, mock_get):
        session = AsyncMock()
        api_key = MagicMock()
        mock_get.return_value = api_key

        update_data = MagicMock()
        update_data.name = "new name"
        update_data.scopes = None
        update_data.rate_limit = None
        update_data.is_active = None
        update_data.expires_at = None

        result = await update_api_key(session, uuid4(), uuid4(), update_data)
        assert result is api_key
        assert api_key.name == "new name"
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.api_key_service.get_api_key_by_id")
    async def test_returns_none_if_not_found(self, mock_get):
        session = AsyncMock()
        mock_get.return_value = None

        result = await update_api_key(session, uuid4(), uuid4(), MagicMock())
        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.api_key_service.get_api_key_by_id")
    async def test_updates_scopes(self, mock_get):
        session = AsyncMock()
        api_key = MagicMock()
        mock_get.return_value = api_key

        update_data = MagicMock()
        update_data.name = None
        update_data.scopes = [MagicMock(value="admin")]
        update_data.rate_limit = None
        update_data.is_active = None
        update_data.expires_at = None

        await update_api_key(session, uuid4(), uuid4(), update_data)
        assert api_key.scopes == "admin"


class TestDeleteApiKey:
    @pytest.mark.asyncio
    @patch("app.services.api_key_service.get_api_key_by_id")
    async def test_deletes_key(self, mock_get):
        session = AsyncMock()
        api_key = MagicMock()
        mock_get.return_value = api_key

        result = await delete_api_key(session, uuid4(), uuid4())
        assert result is True
        session.delete.assert_awaited_once_with(api_key)
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.api_key_service.get_api_key_by_id")
    async def test_returns_false_not_found(self, mock_get):
        session = AsyncMock()
        mock_get.return_value = None

        result = await delete_api_key(session, uuid4(), uuid4())
        assert result is False


class TestVerifyApiKeyAndGetUser:
    @pytest.mark.asyncio
    async def test_returns_none_bad_prefix(self):
        session = AsyncMock()
        result = await verify_api_key_and_get_user(session, "bad_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_no_matching_keys(self):
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.exec.return_value = result_mock

        result = await verify_api_key_and_get_user(session, "is_12345678rest")
        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.api_key_service.verify_api_key")
    async def test_returns_user_on_valid_key(self, mock_verify):
        mock_verify.return_value = True
        session = AsyncMock()
        user = MagicMock()

        api_key = MagicMock()
        api_key.key_hash = "hash"
        api_key.is_valid.return_value = True
        api_key.last_used_at = None
        api_key.request_count = 0
        api_key.user_id = uuid4()

        keys_result = MagicMock()
        keys_result.all.return_value = [api_key]
        user_result = MagicMock()
        user_result.first.return_value = user

        session.exec.side_effect = [keys_result, user_result]

        result = await verify_api_key_and_get_user(session, "is_12345678rest")
        assert result is user

    @pytest.mark.asyncio
    @patch("app.services.api_key_service.verify_api_key")
    async def test_returns_none_expired_key(self, mock_verify):
        mock_verify.return_value = True
        session = AsyncMock()

        api_key = MagicMock()
        api_key.key_hash = "hash"
        api_key.is_valid.return_value = False

        keys_result = MagicMock()
        keys_result.all.return_value = [api_key]
        session.exec.return_value = keys_result

        result = await verify_api_key_and_get_user(session, "is_12345678rest")
        assert result is None


class TestRecordApiKeyUsage:
    @pytest.mark.asyncio
    async def test_increments_count(self):
        session = AsyncMock()
        api_key = MagicMock()
        api_key.request_count = 5

        await record_api_key_usage(session, api_key)
        assert api_key.request_count == 6
        assert api_key.last_used_at is not None
        session.add.assert_called_once_with(api_key)
        session.commit.assert_awaited_once()
