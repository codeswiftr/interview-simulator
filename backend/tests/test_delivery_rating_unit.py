"""Comprehensive unit tests for DeliveryRatingService.

Targets lines 67, 71-76, 91-163 of delivery_rating_service.py.
All tests are pure unit tests — no DB, no real HTTP calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.delivery_rating_service import DeliveryRating, DeliveryRatingService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_VALID_JSON = {
    "content_coverage": 85.0,
    "key_points": 90.0,
    "flow_structure": 80.0,
    "delivery_score": 85.0,
    "strengths": ["Clear examples", "Good structure", "Confident tone"],
    "improvements": ["Add metrics", "Smoother transitions", "More detail"],
    "comparison_feedback": "Solid delivery that covered the main draft points.",
}


def _make_response(content: str | None) -> MagicMock:
    """Build a mock OpenAI ChatCompletion response."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = content
    return mock_resp


def _patch_client(mock_response: MagicMock, side_effect: Exception | None = None):
    """Context-manager stack: patch settings (with key) + AsyncOpenAI client."""

    def _inner(test_fn):
        raise NotImplementedError  # not used directly; see inline usage

    return mock_response  # kept for reference


# ---------------------------------------------------------------------------
# DeliveryRating dataclass — line 14-24
# ---------------------------------------------------------------------------


class TestDeliveryRatingDataclass:
    """Verify the DeliveryRating dataclass stores and exposes all fields."""

    def test_all_fields_stored_correctly(self):
        rating = DeliveryRating(
            delivery_score=92.5,
            content_coverage=88.0,
            key_points=95.0,
            flow_structure=94.0,
            strengths=["Clarity", "Examples", "Pace"],
            improvements=["Metrics", "Transitions", "Depth"],
            comparison_feedback="Excellent coverage of draft.",
        )

        assert rating.delivery_score == 92.5
        assert rating.content_coverage == 88.0
        assert rating.key_points == 95.0
        assert rating.flow_structure == 94.0
        assert rating.strengths == ["Clarity", "Examples", "Pace"]
        assert rating.improvements == ["Metrics", "Transitions", "Depth"]
        assert rating.comparison_feedback == "Excellent coverage of draft."

    def test_empty_lists_allowed(self):
        rating = DeliveryRating(
            delivery_score=0.0,
            content_coverage=0.0,
            key_points=0.0,
            flow_structure=0.0,
            strengths=[],
            improvements=[],
            comparison_feedback="",
        )
        assert rating.strengths == []
        assert rating.improvements == []

    def test_boundary_scores(self):
        rating = DeliveryRating(
            delivery_score=100.0,
            content_coverage=0.0,
            key_points=50.0,
            flow_structure=100.0,
            strengths=["Perfect"],
            improvements=["Nothing"],
            comparison_feedback="Boundary test.",
        )
        assert rating.delivery_score == 100.0
        assert rating.content_coverage == 0.0


# ---------------------------------------------------------------------------
# __init__ — line 67
# ---------------------------------------------------------------------------


class TestDeliveryRatingServiceInit:
    """Verify initialization sets _client to None (line 67)."""

    def test_client_is_none_after_init(self):
        service = DeliveryRatingService()
        assert service._client is None

    def test_independent_instances_each_have_none_client(self):
        s1 = DeliveryRatingService()
        s2 = DeliveryRatingService()
        assert s1._client is None
        assert s2._client is None
        assert s1 is not s2


# ---------------------------------------------------------------------------
# _get_client — lines 71-76
# ---------------------------------------------------------------------------


class TestGetClient:
    """Cover lines 71-76: lazy AsyncOpenAI instantiation with correct args."""

    def test_creates_client_first_call_with_correct_args(self):
        """Line 71-75: _client is None, so AsyncOpenAI is constructed."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-test-key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_instance = MagicMock()
                MockOpenAI.return_value = mock_instance

                service = DeliveryRatingService()
                result = service._get_client()

                MockOpenAI.assert_called_once_with(
                    api_key="sk-or-test-key",
                    base_url="https://openrouter.ai/api/v1",
                )
                assert result is mock_instance

    def test_client_cached_on_second_call(self):
        """Line 71: `if self._client is None` is False on second call — no re-construction."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-test-key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_instance = MagicMock()
                MockOpenAI.return_value = mock_instance

                service = DeliveryRatingService()
                first = service._get_client()
                second = service._get_client()

                assert first is second
                MockOpenAI.assert_called_once()

    def test_client_set_on_service_after_first_call(self):
        """After first call, service._client must not be None (line 72 executed)."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()

                service = DeliveryRatingService()
                service._get_client()

                assert service._client is not None

    def test_uses_api_key_from_settings(self):
        """Verifies the key passed to AsyncOpenAI comes exactly from settings."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "unique-api-key-xyz"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()

                service = DeliveryRatingService()
                service._get_client()

                call_kwargs = MockOpenAI.call_args.kwargs
                assert call_kwargs["api_key"] == "unique-api-key-xyz"
                assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"


# ---------------------------------------------------------------------------
# rate_delivery — lines 91-163
# ---------------------------------------------------------------------------


class TestRateDeliveryFallback:
    """Lines 91-106: fallback when openrouter_api_key is falsy."""

    @pytest.mark.asyncio
    async def test_empty_string_key_returns_fallback(self):
        """Empty string is falsy — should hit fallback path (line 91-106)."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""

            service = DeliveryRatingService()
            result = await service.rate_delivery("draft text", "delivery text")

        assert result.delivery_score == 75.0
        assert result.content_coverage == 75.0
        assert result.key_points == 75.0
        assert result.flow_structure == 75.0
        assert len(result.strengths) == 3
        assert len(result.improvements) == 3
        assert "draft" in result.comparison_feedback.lower() or result.comparison_feedback

    @pytest.mark.asyncio
    async def test_none_key_returns_fallback(self):
        """None is falsy — same fallback branch."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = None

            service = DeliveryRatingService()
            result = await service.rate_delivery("draft", "delivery")

        assert isinstance(result, DeliveryRating)
        assert result.delivery_score == 75.0

    @pytest.mark.asyncio
    async def test_fallback_strengths_content(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""

            service = DeliveryRatingService()
            result = await service.rate_delivery("draft", "delivery")

        assert "Clear delivery" in result.strengths
        assert any("example" in imp.lower() for imp in result.improvements)

    @pytest.mark.asyncio
    async def test_fallback_does_not_call_openai(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                service = DeliveryRatingService()
                await service.rate_delivery("draft", "delivery")

                MockOpenAI.assert_not_called()


class TestRateDeliveryApiCall:
    """Lines 108-118: successful API call path."""

    @pytest.mark.asyncio
    async def test_calls_api_with_correct_model(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(FULL_VALID_JSON))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                await service.rate_delivery("draft", "delivery")

                call_kwargs = mock_client.chat.completions.create.call_args.kwargs
                assert call_kwargs["model"] == "anthropic/claude-3.5-haiku"
                assert call_kwargs["max_tokens"] == 800
                assert call_kwargs["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_prompt_includes_draft_and_delivery(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(FULL_VALID_JSON))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                await service.rate_delivery("MY_UNIQUE_DRAFT", "MY_UNIQUE_DELIVERY")

                call_kwargs = mock_client.chat.completions.create.call_args.kwargs
                prompt_content = call_kwargs["messages"][0]["content"]
                assert "MY_UNIQUE_DRAFT" in prompt_content
                assert "MY_UNIQUE_DELIVERY" in prompt_content


class TestRateDeliveryEmptyResponse:
    """Line 121-122: empty content from AI raises ValueError."""

    @pytest.mark.asyncio
    async def test_none_content_raises_value_error(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=_make_response(None))
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")

    @pytest.mark.asyncio
    async def test_empty_string_content_raises_value_error(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=_make_response(""))
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")


class TestRateDeliveryJsonParsing:
    """Lines 125-155: JSON parsing with and without markdown fences."""

    @pytest.mark.asyncio
    async def test_parses_raw_json(self):
        """Bare JSON string — no code fences."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(FULL_VALID_JSON))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        assert result.delivery_score == 85.0
        assert result.content_coverage == 85.0
        assert result.key_points == 90.0
        assert result.flow_structure == 80.0
        assert result.strengths == ["Clear examples", "Good structure", "Confident tone"]
        assert result.improvements == ["Add metrics", "Smoother transitions", "More detail"]
        assert result.comparison_feedback == "Solid delivery that covered the main draft points."

    @pytest.mark.asyncio
    async def test_parses_json_inside_json_code_fence(self):
        """Lines 127-130: ```json ... ``` block extraction."""
        raw = json.dumps(FULL_VALID_JSON)
        wrapped = f"Here is the analysis:\n```json\n{raw}\n```\nEnd."

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(wrapped)
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        assert result.delivery_score == 85.0
        assert result.content_coverage == 85.0

    @pytest.mark.asyncio
    async def test_parses_json_inside_plain_code_fence(self):
        """Lines 131-134: plain ``` ... ``` block extraction (no 'json' hint)."""
        raw = json.dumps(FULL_VALID_JSON)
        wrapped = f"Analysis:\n```\n{raw}\n```"

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(wrapped)
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        assert result.delivery_score == 85.0

    @pytest.mark.asyncio
    async def test_calculates_average_when_delivery_score_absent(self):
        """Lines 140-145: delivery_score computed as average of three sub-scores."""
        data = {
            "content_coverage": 60.0,
            "key_points": 90.0,
            "flow_structure": 90.0,
            # delivery_score intentionally missing
            "strengths": ["A", "B", "C"],
            "improvements": ["X", "Y", "Z"],
            "comparison_feedback": "Test.",
        }

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(data))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        # (60 + 90 + 90) / 3 == 80
        assert result.delivery_score == 80.0

    @pytest.mark.asyncio
    async def test_calculates_average_all_zeros_when_absent_and_no_sub_scores(self):
        """delivery_score is None and sub-scores default to 0 → average of 0."""
        data = {
            # all scores absent
            "strengths": [],
            "improvements": [],
            "comparison_feedback": "",
        }

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(data))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        assert result.delivery_score == 0.0

    @pytest.mark.asyncio
    async def test_missing_optional_fields_default_to_empty(self):
        """data.get() calls use safe defaults — strengths/improvements/feedback."""
        minimal = {
            "content_coverage": 70.0,
            "key_points": 70.0,
            "flow_structure": 70.0,
            "delivery_score": 70.0,
        }

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(minimal))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        assert result.strengths == []
        assert result.improvements == []
        assert result.comparison_feedback == ""

    @pytest.mark.asyncio
    async def test_delivery_score_cast_to_float(self):
        """delivery_score provided as int — cast to float (line 148)."""
        data = {**FULL_VALID_JSON, "delivery_score": 88}

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(data))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        assert isinstance(result.delivery_score, float)
        assert result.delivery_score == 88.0

    @pytest.mark.asyncio
    async def test_sub_scores_cast_to_float(self):
        """Sub-scores provided as ints — cast to float (lines 149-151)."""
        data = {
            "content_coverage": 80,
            "key_points": 75,
            "flow_structure": 85,
            "delivery_score": 80,
            "strengths": [],
            "improvements": [],
            "comparison_feedback": "",
        }

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(json.dumps(data))
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery("draft", "delivery")

        assert isinstance(result.content_coverage, float)
        assert isinstance(result.key_points, float)
        assert isinstance(result.flow_structure, float)


class TestRateDeliveryJsonParseErrors:
    """Lines 157-159: JSONDecodeError / ValueError inside the inner try/except."""

    @pytest.mark.asyncio
    async def test_invalid_json_raises_value_error(self):
        """Non-JSON content triggers JSONDecodeError → re-raised as ValueError."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response("this is not json at all")
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")

    @pytest.mark.asyncio
    async def test_truncated_json_raises_value_error(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response('{"content_coverage": 80, "key_points":')
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")

    @pytest.mark.asyncio
    async def test_json_inside_code_fence_that_is_invalid_raises(self):
        """Extracts content from fence, but content itself is bad JSON."""
        bad_inner = "```json\n{ not valid json }\n```"

        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=_make_response(bad_inner)
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")


class TestRateDeliveryOuterExceptionHandler:
    """Lines 161-163: outer except wraps unexpected exceptions."""

    @pytest.mark.asyncio
    async def test_api_network_error_raises_value_error(self):
        """Exception from .create() is caught and re-raised as ValueError (line 161-163)."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=ConnectionError("Network timeout")
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")

    @pytest.mark.asyncio
    async def test_runtime_error_from_api_raises_value_error(self):
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=RuntimeError("Unexpected upstream error")
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")

    @pytest.mark.asyncio
    async def test_error_message_includes_original_message(self):
        """The outer handler includes str(e) in the ValueError message."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("upstream-specific-message")
                )
                MockOpenAI.return_value = mock_client

                service = DeliveryRatingService()
                with pytest.raises(ValueError) as exc_info:
                    await service.rate_delivery("draft", "delivery")

                assert "upstream-specific-message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_raises_causes_outer_handler(self):
        """If _get_client itself raises, the outer except catches it."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockOpenAI:
                MockOpenAI.side_effect = TypeError("bad init args")

                service = DeliveryRatingService()
                with pytest.raises(ValueError, match="Failed to rate delivery"):
                    await service.rate_delivery("draft", "delivery")


class TestRatingPromptTemplate:
    """Verify RATING_PROMPT template structure (no lines targeted but validates contract)."""

    def test_prompt_has_draft_placeholder(self):
        assert "{draft}" in DeliveryRatingService.RATING_PROMPT

    def test_prompt_has_delivery_placeholder(self):
        assert "{delivery}" in DeliveryRatingService.RATING_PROMPT

    def test_prompt_format_substitutes_correctly(self):
        formatted = DeliveryRatingService.RATING_PROMPT.format(
            draft="MY DRAFT", delivery="MY DELIVERY"
        )
        assert "MY DRAFT" in formatted
        assert "MY DELIVERY" in formatted

    def test_prompt_contains_json_schema_keys(self):
        prompt = DeliveryRatingService.RATING_PROMPT
        for key in (
            "content_coverage",
            "key_points",
            "flow_structure",
            "delivery_score",
            "strengths",
            "improvements",
            "comparison_feedback",
        ):
            assert key in prompt, f"Expected '{key}' in RATING_PROMPT"

    def test_prompt_references_star_method(self):
        assert "STAR" in DeliveryRatingService.RATING_PROMPT
