"""Delivery rating service for comparing practice attempts to drafts."""

import json
import logging
from dataclasses import dataclass
from uuid import UUID

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DeliveryRating:
    """Rating result from delivery comparison."""

    delivery_score: float  # Overall score 0-100
    content_coverage: float  # 0-100
    key_points: float  # 0-100
    flow_structure: float  # 0-100
    strengths: list[str]
    improvements: list[str]
    comparison_feedback: str


class DeliveryRatingService:
    """Service for rating delivery attempts against prepared drafts.

    Uses Claude Haiku via OpenRouter to compare delivery transcripts
    to draft answers and provide actionable feedback.
    """

    RATING_PROMPT = """You are an expert interview coach comparing a candidate's actual delivery to their prepared draft answer.

DRAFT (what they planned to say):
{draft}

DELIVERY (what they actually said):
{delivery}

Rate the delivery on the following dimensions (0-100):

1. **Content Coverage** (0-100): Did they hit all STAR components and cover the main points from the draft?
2. **Key Points** (0-100): Did they include the essential information from their draft?
3. **Flow & Structure** (0-100): Was the delivery logical, clear, and well-organized?

Calculate an overall score as the average of these three dimensions.

Also provide:
- **Strengths**: 3 specific things they did well in their delivery
- **Improvements**: 3 actionable suggestions for how they can improve their delivery
- **Comparison Feedback**: A detailed paragraph comparing their delivery to the draft, highlighting what they covered well and what they missed

Respond in this exact JSON format:
{{
    "content_coverage": <score>,
    "key_points": <score>,
    "flow_structure": <score>,
    "delivery_score": <overall average>,
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "comparison_feedback": "<detailed paragraph>"
}}"""

    def __init__(self) -> None:
        """Initialize the rating service."""
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenRouter client for Claude Haiku."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        return self._client

    async def rate_delivery(
        self, draft: str, delivery_transcript: str
    ) -> DeliveryRating:
        """Rate a delivery attempt against the prepared draft.

        Args:
            draft: The prepared draft answer
            delivery_transcript: The transcribed delivery from the practice attempt

        Returns:
            DeliveryRating with scores and feedback

        Raises:
            ValueError: If AI service fails or returns invalid response
        """
        if not settings.openrouter_api_key:
            # Fallback rating for development/testing
            logger.warning("OpenRouter API key not configured, using fallback rating")
            return DeliveryRating(
                delivery_score=75.0,
                content_coverage=75.0,
                key_points=75.0,
                flow_structure=75.0,
                strengths=["Clear delivery", "Good pace", "Engaging tone"],
                improvements=[
                    "Include more specific examples",
                    "Add quantifiable results",
                    "Practice smoother transitions",
                ],
                comparison_feedback="Your delivery captured the main points from your draft. Consider adding more specific details and metrics to strengthen your answer.",
            )

        try:
            client = self._get_client()

            prompt = self.RATING_PROMPT.format(
                draft=draft, delivery=delivery_transcript
            )

            response = await client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from AI service")

            # Parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()

                data = json.loads(content)

                # Calculate overall score if not provided
                delivery_score = data.get("delivery_score")
                if delivery_score is None:
                    delivery_score = (
                        data.get("content_coverage", 0)
                        + data.get("key_points", 0)
                        + data.get("flow_structure", 0)
                    ) / 3

                return DeliveryRating(
                    delivery_score=float(delivery_score),
                    content_coverage=float(data.get("content_coverage", 0)),
                    key_points=float(data.get("key_points", 0)),
                    flow_structure=float(data.get("flow_structure", 0)),
                    strengths=data.get("strengths", []),
                    improvements=data.get("improvements", []),
                    comparison_feedback=data.get("comparison_feedback", ""),
                )

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse AI response: {e}\nResponse: {content}")
                raise ValueError(f"Invalid response format from AI service: {e}") from None

        except Exception as e:
            logger.error(f"Error rating delivery: {e}")
            raise ValueError(f"Failed to rate delivery: {str(e)}") from None
