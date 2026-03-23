"""Pure unit tests for coaching API routes.

Tests rate limiting, hint generation, streaming, and route logic.
No database required — all dependencies are mocked.
"""

import json
import time
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.coaching import (
    COACHING_RATE_LIMIT,
    STATIC_HINTS,
    CoachingHintRequest,
    check_coaching_rate_limit,
    generate_coaching_hint,
    generate_coaching_hint_stream,
    get_coaching_hint,
    get_coaching_hint_stream,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(user_id=None):
    user = MagicMock()
    user.id = user_id or uuid4()
    return user


def _make_request(
    question="Tell me about a time you led a project",
    question_type="behavioral",
    transcript="",
):
    return CoachingHintRequest(
        question=question,
        question_type=question_type,
        transcript=transcript,
    )


# ---------------------------------------------------------------------------
# check_coaching_rate_limit
# ---------------------------------------------------------------------------


class TestCheckCoachingRateLimit:
    def setup_method(self):
        """Reset rate limit state before each test."""
        import app.api.coaching as coaching_module

        coaching_module._coaching_rate_limits = defaultdict(list)

    def test_allows_first_request(self):
        user_id = str(uuid4())
        allowed, remaining = check_coaching_rate_limit(user_id)
        assert allowed is True
        assert remaining == COACHING_RATE_LIMIT - 1

    def test_allows_up_to_limit(self):
        user_id = str(uuid4())
        for _ in range(COACHING_RATE_LIMIT):
            allowed, _ = check_coaching_rate_limit(user_id)
            assert allowed is True

    def test_rejects_over_limit(self):
        user_id = str(uuid4())
        # Exhaust the limit
        for _ in range(COACHING_RATE_LIMIT):
            check_coaching_rate_limit(user_id)
        # Next request should be rejected
        allowed, remaining = check_coaching_rate_limit(user_id)
        assert allowed is False
        assert remaining == 0

    def test_cleans_expired_timestamps(self):
        import app.api.coaching as coaching_module

        user_id = str(uuid4())
        # Insert an old timestamp outside the rate window
        old_ts = time.time() - 120  # 2 minutes ago
        coaching_module._coaching_rate_limits[user_id] = [old_ts]
        allowed, _ = check_coaching_rate_limit(user_id)
        assert allowed is True


# ---------------------------------------------------------------------------
# generate_coaching_hint (no-DB async helper)
# ---------------------------------------------------------------------------


class TestGenerateCoachingHint:
    @pytest.mark.asyncio
    @patch("app.api.coaching.settings")
    async def test_returns_static_hint_when_no_api_key(self, mock_settings):
        mock_settings.openrouter_api_key = ""
        hint = await generate_coaching_hint("Q?", "behavioral", "")
        assert hint == STATIC_HINTS["behavioral"]

    @pytest.mark.asyncio
    @patch("app.api.coaching.settings")
    async def test_returns_static_hint_for_technical_when_no_api_key(self, mock_settings):
        mock_settings.openrouter_api_key = ""
        hint = await generate_coaching_hint("Q?", "technical", "")
        assert hint == STATIC_HINTS["technical"]

    @pytest.mark.asyncio
    @patch("app.api.coaching.get_coaching_client")
    @patch("app.api.coaching.settings")
    async def test_returns_ai_hint_on_success(self, mock_settings, mock_get_client):
        mock_settings.openrouter_api_key = "test-key"
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "  Focus on using STAR structure.  "
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        hint = await generate_coaching_hint(
            "Tell me about teamwork.", "behavioral", "I worked on..."
        )
        assert hint == "Focus on using STAR structure."

    @pytest.mark.asyncio
    @patch("app.api.coaching.get_coaching_client")
    @patch("app.api.coaching.settings")
    async def test_falls_back_to_static_on_empty_ai_response(self, mock_settings, mock_get_client):
        mock_settings.openrouter_api_key = "test-key"
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = None  # empty content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        hint = await generate_coaching_hint("Q?", "system_design", "")
        assert hint == STATIC_HINTS["system_design"]

    @pytest.mark.asyncio
    @patch("app.api.coaching.get_coaching_client")
    @patch("app.api.coaching.settings")
    async def test_falls_back_to_static_on_api_exception(self, mock_settings, mock_get_client):
        mock_settings.openrouter_api_key = "test-key"
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("network error"))

        hint = await generate_coaching_hint("Q?", "behavioral", "")
        assert hint == STATIC_HINTS["behavioral"]


# ---------------------------------------------------------------------------
# generate_coaching_hint_stream (async generator)
# ---------------------------------------------------------------------------


class TestGenerateCoachingHintStream:
    @pytest.mark.asyncio
    @patch("app.api.coaching.settings")
    async def test_yields_static_hint_when_no_api_key(self, mock_settings):
        mock_settings.openrouter_api_key = ""
        chunks = []
        async for chunk in generate_coaching_hint_stream("Q?", "behavioral", ""):
            chunks.append(chunk)

        assert len(chunks) == 1
        data = json.loads(chunks[0].removeprefix("data: ").strip())
        assert data["hint"] == STATIC_HINTS["behavioral"]
        assert data["done"] is True

    @pytest.mark.asyncio
    @patch("app.api.coaching.get_coaching_client")
    @patch("app.api.coaching.settings")
    async def test_falls_back_on_stream_exception(self, mock_settings, mock_get_client):
        mock_settings.openrouter_api_key = "test-key"
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("timeout"))

        chunks = []
        async for chunk in generate_coaching_hint_stream("Q?", "technical", ""):
            chunks.append(chunk)

        assert len(chunks) == 1
        data = json.loads(chunks[0].removeprefix("data: ").strip())
        assert data["hint"] == STATIC_HINTS["technical"]
        assert data["done"] is True


# ---------------------------------------------------------------------------
# get_coaching_hint route
# ---------------------------------------------------------------------------


class TestGetCoachingHintRoute:
    @pytest.mark.asyncio
    @patch("app.api.coaching.generate_coaching_hint", new_callable=AsyncMock)
    @patch("app.api.coaching.check_coaching_rate_limit")
    async def test_returns_hint_on_success(self, mock_rate, mock_generate):
        mock_rate.return_value = (True, 4)
        mock_generate.return_value = "Use STAR structure."

        user = _make_user()
        request = _make_request()
        response = await get_coaching_hint(request, user)

        assert response.hint == "Use STAR structure."
        mock_generate.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.api.coaching.check_coaching_rate_limit")
    async def test_raises_429_when_rate_limited(self, mock_rate):
        mock_rate.return_value = (False, 0)

        user = _make_user()
        request = _make_request()
        with pytest.raises(HTTPException) as exc_info:
            await get_coaching_hint(request, user)
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    @patch("app.api.coaching.generate_coaching_hint", new_callable=AsyncMock)
    @patch("app.api.coaching.check_coaching_rate_limit")
    async def test_raises_422_for_invalid_question_type(self, mock_rate, mock_generate):
        mock_rate.return_value = (True, 4)
        # Bypass pydantic validation by constructing with a valid type then monkey-patching
        request = _make_request(question_type="behavioral")
        request.question_type = "invalid_type"  # force an invalid value post-construction

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await get_coaching_hint(request, user)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# get_coaching_hint_stream route
# ---------------------------------------------------------------------------


class TestGetCoachingHintStreamRoute:
    @pytest.mark.asyncio
    @patch("app.api.coaching.generate_coaching_hint_stream")
    @patch("app.api.coaching.check_coaching_rate_limit")
    async def test_returns_streaming_response_on_success(self, mock_rate, mock_stream_gen):
        mock_rate.return_value = (True, 3)
        from fastapi.responses import StreamingResponse

        async def _fake_gen():
            yield "data: {}\n\n"

        mock_stream_gen.return_value = _fake_gen()

        user = _make_user()
        request = _make_request()
        response = await get_coaching_hint_stream(request, user)

        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"

    @pytest.mark.asyncio
    @patch("app.api.coaching.check_coaching_rate_limit")
    async def test_raises_429_when_rate_limited_stream(self, mock_rate):
        mock_rate.return_value = (False, 0)

        user = _make_user()
        request = _make_request()
        with pytest.raises(HTTPException) as exc_info:
            await get_coaching_hint_stream(request, user)
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    @patch("app.api.coaching.generate_coaching_hint_stream")
    @patch("app.api.coaching.check_coaching_rate_limit")
    async def test_raises_422_for_invalid_question_type_stream(self, mock_rate, mock_stream_gen):
        mock_rate.return_value = (True, 4)
        request = _make_request(question_type="behavioral")
        request.question_type = "bogus"

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await get_coaching_hint_stream(request, user)
        assert exc_info.value.status_code == 422
