"""Unit tests for DeliveryRatingService.

Tests delivery comparison and rating without making API calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.delivery_rating_service import DeliveryRating, DeliveryRatingService


class TestDeliveryRatingDataclass:
    """Tests for DeliveryRating dataclass."""

    def test_creates_with_all_fields(self):
        """Test creates dataclass with all fields."""
        rating = DeliveryRating(
            delivery_score=85.0,
            content_coverage=90.0,
            key_points=80.0,
            flow_structure=85.0,
            strengths=["Good pace", "Clear examples"],
            improvements=["Add more metrics"],
            comparison_feedback="Well done overall.",
        )

        assert rating.delivery_score == 85.0
        assert rating.content_coverage == 90.0
        assert len(rating.strengths) == 2
        assert len(rating.improvements) == 1


class TestDeliveryRatingServiceInit:
    """Tests for DeliveryRatingService initialization."""

    def test_initializes_with_no_client(self):
        """Test service initializes with no client."""
        service = DeliveryRatingService()
        assert service._client is None


class TestGetClient:
    """Tests for _get_client method."""

    def test_creates_client_on_first_call(self):
        """Test creates OpenAI client on first call."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                service = DeliveryRatingService()
                service._get_client()

                MockClient.assert_called_once_with(
                    api_key="test_key",
                    base_url="https://openrouter.ai/api/v1",
                )

    def test_returns_same_client_on_subsequent_calls(self):
        """Test returns cached client on subsequent calls."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                MockClient.return_value = mock_client

                service = DeliveryRatingService()
                client1 = service._get_client()
                client2 = service._get_client()

                assert client1 is client2
                MockClient.assert_called_once()


class TestRateDelivery:
    """Tests for rate_delivery method."""

    @pytest.mark.asyncio
    async def test_returns_fallback_without_api_key(self):
        """Test returns fallback rating when API key not configured."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = None

            service = DeliveryRatingService()
            result = await service.rate_delivery(
                draft="My prepared answer about leadership...",
                delivery_transcript="I talked about leading a team...",
            )

            assert result.delivery_score == 75.0
            assert result.content_coverage == 75.0
            assert len(result.strengths) == 3
            assert len(result.improvements) == 3

    @pytest.mark.asyncio
    async def test_parses_json_response(self):
        """Test parses AI JSON response correctly."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(
                {
                    "content_coverage": 85.0,
                    "key_points": 90.0,
                    "flow_structure": 80.0,
                    "delivery_score": 85.0,
                    "strengths": ["Good examples", "Clear structure"],
                    "improvements": ["Add metrics"],
                    "comparison_feedback": "Good delivery.",
                }
            )

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                MockClient.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery(
                    draft="Draft answer",
                    delivery_transcript="Delivery attempt",
                )

                assert result.delivery_score == 85.0
                assert result.content_coverage == 85.0
                assert result.key_points == 90.0
                assert "Good examples" in result.strengths

    @pytest.mark.asyncio
    async def test_parses_json_from_markdown_code_block(self):
        """Test extracts JSON from markdown code blocks."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            json_content = json.dumps(
                {
                    "content_coverage": 80.0,
                    "key_points": 85.0,
                    "flow_structure": 75.0,
                    "delivery_score": 80.0,
                    "strengths": ["Clear"],
                    "improvements": ["More detail"],
                    "comparison_feedback": "Good.",
                }
            )

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[
                0
            ].message.content = f"Here's my analysis:\n```json\n{json_content}\n```"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                MockClient.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery(
                    draft="Draft",
                    delivery_transcript="Delivery",
                )

                assert result.delivery_score == 80.0

    @pytest.mark.asyncio
    async def test_parses_json_from_plain_code_block(self):
        """Test extracts JSON from plain code blocks."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            json_content = json.dumps(
                {
                    "content_coverage": 70.0,
                    "key_points": 75.0,
                    "flow_structure": 80.0,
                    "delivery_score": 75.0,
                    "strengths": ["Good pace"],
                    "improvements": ["Add examples"],
                    "comparison_feedback": "Solid.",
                }
            )

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = f"Analysis:\n```\n{json_content}\n```"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                MockClient.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery(
                    draft="Draft",
                    delivery_transcript="Delivery",
                )

                assert result.delivery_score == 75.0

    @pytest.mark.asyncio
    async def test_calculates_score_when_not_provided(self):
        """Test calculates delivery_score as average when not provided."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(
                {
                    "content_coverage": 80.0,
                    "key_points": 70.0,
                    "flow_structure": 90.0,
                    # delivery_score not provided
                    "strengths": ["A"],
                    "improvements": ["B"],
                    "comparison_feedback": "C",
                }
            )

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                MockClient.return_value = mock_client

                service = DeliveryRatingService()
                result = await service.rate_delivery(
                    draft="Draft",
                    delivery_transcript="Delivery",
                )

                # (80 + 70 + 90) / 3 = 80
                assert result.delivery_score == 80.0

    @pytest.mark.asyncio
    async def test_raises_on_empty_response(self):
        """Test raises ValueError on empty AI response."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = None

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                MockClient.return_value = mock_client

                service = DeliveryRatingService()

                with pytest.raises(ValueError) as exc_info:
                    await service.rate_delivery("Draft", "Delivery")

                assert "Empty response" in str(exc_info.value) or "Failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json(self):
        """Test raises ValueError on invalid JSON response."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "This is not JSON"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                MockClient.return_value = mock_client

                service = DeliveryRatingService()

                with pytest.raises(ValueError) as exc_info:
                    await service.rate_delivery("Draft", "Delivery")

                assert "Invalid" in str(exc_info.value) or "Failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_api_error(self):
        """Test raises ValueError on API error."""
        with patch("app.services.delivery_rating_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test_key"

            with patch("app.services.delivery_rating_service.AsyncOpenAI") as MockClient:
                mock_client = MagicMock()
                mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
                MockClient.return_value = mock_client

                service = DeliveryRatingService()

                with pytest.raises(ValueError) as exc_info:
                    await service.rate_delivery("Draft", "Delivery")

                assert "Failed" in str(exc_info.value)


class TestRatingPrompt:
    """Tests for the rating prompt template."""

    def test_prompt_contains_required_sections(self):
        """Test prompt template contains required sections."""
        prompt = DeliveryRatingService.RATING_PROMPT

        assert "{draft}" in prompt
        assert "{delivery}" in prompt
        assert "Content Coverage" in prompt
        assert "Key Points" in prompt
        assert "Flow" in prompt
        assert "Strengths" in prompt
        assert "Improvements" in prompt
        assert "JSON" in prompt
