"""Gap-filling unit tests for coaching API.

Covers: client singleton lifecycle, stream accumulation / empty-stream fallback,
question-type focus areas, and rate-limit header on the streaming route.
No database required — all dependencies are mocked.
"""

import json
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.coaching import (
    STATIC_HINTS,
    CoachingHintRequest,
    generate_coaching_hint_stream,
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


def _make_stream_chunk(content: str | None):
    """Build a minimal streaming chunk object mirroring the OpenAI SDK shape."""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = content
    return chunk


# ---------------------------------------------------------------------------
# get_coaching_client — singleton lifecycle
# ---------------------------------------------------------------------------


class TestGetCoachingClientSingleton:
    def setup_method(self):
        """Reset the global client before every test."""
        import app.api.coaching as coaching_module

        coaching_module._coaching_client = None

    def teardown_method(self):
        """Always reset after the test to avoid cross-test pollution."""
        import app.api.coaching as coaching_module

        coaching_module._coaching_client = None

    @patch("app.api.coaching.settings")
    def test_get_coaching_client_creates_singleton_with_openrouter_url(self, mock_settings):
        """First call must create an AsyncOpenAI client pointed at OpenRouter."""
        mock_settings.openrouter_api_key = "sk-or-test-key"

        from app.api.coaching import get_coaching_client

        client = get_coaching_client()

        assert client is not None

        # The singleton must be stored in the module-level variable
        import app.api.coaching as coaching_module

        assert coaching_module._coaching_client is client

        # The base URL must reference OpenRouter
        assert "openrouter.ai" in str(client.base_url)

    @patch("app.api.coaching.settings")
    def test_get_coaching_client_reuses_existing_instance(self, mock_settings):
        """Subsequent calls must return the identical object without re-constructing."""
        mock_settings.openrouter_api_key = "sk-or-test-key"

        from app.api.coaching import get_coaching_client

        client_first = get_coaching_client()
        client_second = get_coaching_client()

        assert client_first is client_second


# ---------------------------------------------------------------------------
# generate_coaching_hint_stream — accumulation and empty-stream fallback
# ---------------------------------------------------------------------------


class TestGenerateCoachingHintStreamAccumulation:
    @pytest.mark.asyncio
    @patch("app.api.coaching.get_coaching_client")
    @patch("app.api.coaching.settings")
    async def test_generate_coaching_hint_stream_accumulates_and_yields_done(
        self, mock_settings, mock_get_client
    ):
        """Streamed chunks must be accumulated; the final SSE event must have done=True
        and contain the full concatenated content."""
        mock_settings.openrouter_api_key = "sk-or-test"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Three chunks whose text concatenates to a complete sentence
        chunk_contents = ["Focus on ", "STAR ", "structure."]

        async def _fake_stream():
            for text in chunk_contents:
                yield _make_stream_chunk(text)

        mock_client.chat.completions.create = AsyncMock(return_value=_fake_stream())

        collected = []
        async for raw in generate_coaching_hint_stream(
            "Tell me about teamwork.", "behavioral", "I collaborated with..."
        ):
            collected.append(raw)

        # Must have emitted at least one intermediate chunk and the final done event
        assert len(collected) >= 2

        events = [json.loads(raw.removeprefix("data: ").strip()) for raw in collected]

        # The last event must signal done=True
        last = events[-1]
        assert last["done"] is True

        # The accumulated text must contain the full concatenation of all chunks
        assert "Focus on STAR structure." in last["hint"]

        # Every intermediate event must carry done=False
        for event in events[:-1]:
            assert event["done"] is False

    @pytest.mark.asyncio
    @patch("app.api.coaching.get_coaching_client")
    @patch("app.api.coaching.settings")
    async def test_generate_coaching_hint_stream_empty_accumulated_falls_back(
        self, mock_settings, mock_get_client
    ):
        """When the AI stream yields no usable content (None delta), the generator
        must fall back to the static hint for that question type."""
        mock_settings.openrouter_api_key = "sk-or-test"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Chunk where delta.content is None — nothing accumulates
        async def _empty_stream():
            yield _make_stream_chunk(None)

        mock_client.chat.completions.create = AsyncMock(return_value=_empty_stream())

        collected = []
        async for raw in generate_coaching_hint_stream("Q?", "technical", ""):
            collected.append(raw)

        # Exactly one SSE event — the static fallback
        assert len(collected) == 1
        data = json.loads(collected[0].removeprefix("data: ").strip())
        assert data["done"] is True
        assert data["hint"] == STATIC_HINTS["technical"]


# ---------------------------------------------------------------------------
# generate_coaching_hint — system_design focus areas in the prompt
# ---------------------------------------------------------------------------


class TestGenerateCoachingHintSystemDesignFocusAreas:
    @pytest.mark.asyncio
    @patch("app.api.coaching.get_coaching_client")
    @patch("app.api.coaching.settings")
    async def test_generate_coaching_hint_system_design_uses_correct_focus_areas(
        self, mock_settings, mock_get_client
    ):
        """The prompt sent to the AI client for a system_design question must
        explicitly mention Requirements, scalability, and trade-offs."""
        mock_settings.openrouter_api_key = "sk-or-test"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        captured_messages: list = []

        async def _capture(**kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            mock_choice = MagicMock()
            mock_choice.message.content = "Think about scalability."
            mock_resp = MagicMock()
            mock_resp.choices = [mock_choice]
            return mock_resp

        mock_client.chat.completions.create = _capture

        from app.api.coaching import generate_coaching_hint

        await generate_coaching_hint(
            "Design a URL shortener.", "system_design", "I would start with Redis..."
        )

        assert captured_messages, "No messages were forwarded to the AI client"
        full_prompt = " ".join(m["content"] for m in captured_messages)

        # Verify the three canonical system_design focus keywords appear in the prompt
        assert "Requirements" in full_prompt
        assert "scalability" in full_prompt or "Scalability" in full_prompt
        assert "trade-offs" in full_prompt or "Trade-offs" in full_prompt


# ---------------------------------------------------------------------------
# get_coaching_hint_stream route — X-RateLimit-Remaining response header
# ---------------------------------------------------------------------------


class TestGetCoachingHintStreamRateLimitHeader:
    def setup_method(self):
        import app.api.coaching as coaching_module

        coaching_module._coaching_rate_limits = defaultdict(list)

    @pytest.mark.asyncio
    @patch("app.api.coaching.generate_coaching_hint_stream")
    @patch("app.api.coaching.check_coaching_rate_limit")
    async def test_get_coaching_hint_stream_includes_rate_limit_header(
        self, mock_rate, mock_stream_gen
    ):
        """The StreamingResponse headers must include X-RateLimit-Remaining set to
        the value returned by check_coaching_rate_limit."""
        remaining = 3
        mock_rate.return_value = (True, remaining)

        async def _fake_gen():
            yield f"data: {json.dumps({'hint': 'test hint', 'done': True})}\n\n"

        mock_stream_gen.return_value = _fake_gen()

        from fastapi.responses import StreamingResponse

        user = _make_user()
        request = _make_request()
        response = await get_coaching_hint_stream(request, user)

        assert isinstance(response, StreamingResponse)
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == str(remaining)
