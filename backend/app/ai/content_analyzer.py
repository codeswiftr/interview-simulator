"""Content analysis service using Claude for semantic evaluation.

Supports multiple providers:
- Anthropic (direct)
- OpenRouter (via OpenAI-compatible API)
"""

import json
import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ContentMetrics:
    """Metrics from content analysis."""

    technical_accuracy: float
    star_adherence: float
    answer_structure: float
    completeness: float
    relevance: float
    strengths: list[str]
    improvements: list[str]
    detailed_feedback: str


class ContentAnalyzer:
    """Analyzes interview response content using Claude.

    Evaluates responses for:
    - Technical accuracy
    - STAR method adherence (for behavioral questions)
    - Answer structure and organization
    - Completeness
    - Relevance to the question
    """

    ANALYSIS_PROMPT = """You are an expert interview coach analyzing a candidate's response.

Question: {question}
Question Type: {question_type}
Candidate's Answer: {transcript}

Analyze the response and provide scores (0-100) for each dimension:

1. **Technical Accuracy** (0-100): Is the information correct and well-informed?
2. **Structure** (0-100): Is the answer well-organized with clear flow?
3. **Completeness** (0-100): Did they fully address all parts of the question?
4. **Relevance** (0-100): Did they stay on topic and answer what was asked?

{star_instruction}

Also provide:
- **Strengths**: 2-3 specific things the candidate did well
- **Improvements**: 2-3 actionable suggestions for improvement
- **Detailed Feedback**: A paragraph of constructive feedback

Respond in this exact JSON format:
{{
    "technical_accuracy": <score>,
    "star_adherence": <score or 0 if not behavioral>,
    "answer_structure": <score>,
    "completeness": <score>,
    "relevance": <score>,
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "detailed_feedback": "<paragraph of feedback>"
}}"""

    STAR_INSTRUCTION = """
For behavioral questions, also evaluate:
5. **STAR Adherence** (0-100): Did they use the STAR method effectively?
   - Situation: Did they set the context?
   - Task: Did they explain their responsibility?
   - Action: Did they describe specific actions they took?
   - Result: Did they share the outcome with metrics if possible?
"""

    def __init__(self) -> None:
        """Initialize the content analyzer based on configured provider."""
        self.provider = settings.content_analysis_provider

        if self.provider == "openrouter":
            self.openrouter_client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            self.anthropic_client = None
            logger.info("ContentAnalyzer using OpenRouter provider")
        else:
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.openrouter_client = None
            logger.info("ContentAnalyzer using Anthropic provider")

    async def analyze(
        self,
        question: str,
        transcript: str,
        question_type: str,
    ) -> ContentMetrics:
        """Analyze response content using Claude.

        Args:
            question: The interview question
            transcript: The candidate's transcribed response
            question_type: Type of question (behavioral, technical, system_design)

        Returns:
            ContentMetrics with analysis results
        """
        star_instruction = self.STAR_INSTRUCTION if question_type == "behavioral" else ""

        prompt = self.ANALYSIS_PROMPT.format(
            question=question,
            question_type=question_type,
            transcript=transcript,
            star_instruction=star_instruction,
        )

        try:
            if self.provider == "openrouter":
                # Use OpenRouter with Claude via OpenAI-compatible API
                response = await self.openrouter_client.chat.completions.create(
                    model="anthropic/claude-haiku-4.5",
                    max_tokens=2048,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content
            else:
                # Use Anthropic directly
                response = await self.anthropic_client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=2048,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                first_block = response.content[0]
                if not hasattr(first_block, "text"):
                    raise ValueError("Response does not contain text content")
                content = first_block.text
            logger.debug(f"Raw Claude response: {content}")

            # Extract JSON from the response (it might be wrapped in markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            metrics = ContentMetrics(
                technical_accuracy=float(data.get("technical_accuracy", 50)),
                star_adherence=float(data.get("star_adherence", 0)),
                answer_structure=float(data.get("answer_structure", 50)),
                completeness=float(data.get("completeness", 50)),
                relevance=float(data.get("relevance", 50)),
                strengths=data.get("strengths", []),
                improvements=data.get("improvements", []),
                detailed_feedback=data.get("detailed_feedback", ""),
            )

            logger.info(
                f"Analysis complete: type={question_type}, "
                f"accuracy={metrics.technical_accuracy:.1f}, "
                f"structure={metrics.answer_structure:.1f}"
            )

            return metrics

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Claude: {e}")
            logger.error(f"Raw content: {content if 'content' in locals() else 'N/A'}")
            return ContentMetrics(
                technical_accuracy=50.0,
                star_adherence=0.0,
                answer_structure=50.0,
                completeness=50.0,
                relevance=50.0,
                strengths=["Unable to analyze due to parsing error"],
                improvements=["Please try again"],
                detailed_feedback=f"JSON parsing failed: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Analysis failed with error: {e}", exc_info=True)
            # Return default metrics on error
            return ContentMetrics(
                technical_accuracy=50.0,
                star_adherence=0.0,
                answer_structure=50.0,
                completeness=50.0,
                relevance=50.0,
                strengths=["Unable to analyze due to error"],
                improvements=["Please try again"],
                detailed_feedback=f"Analysis failed: {str(e)}",
            )

    def calculate_overall_score(self, metrics: ContentMetrics, question_type: str) -> float:
        """Calculate weighted overall content score.

        Args:
            metrics: ContentMetrics from analysis
            question_type: Type of question for weight adjustment

        Returns:
            Overall score from 0-100
        """
        if question_type == "behavioral":
            # For behavioral: STAR method is important
            weights = {
                "technical_accuracy": 0.15,
                "star_adherence": 0.30,
                "answer_structure": 0.20,
                "completeness": 0.20,
                "relevance": 0.15,
            }
            return (
                metrics.technical_accuracy * weights["technical_accuracy"]
                + metrics.star_adherence * weights["star_adherence"]
                + metrics.answer_structure * weights["answer_structure"]
                + metrics.completeness * weights["completeness"]
                + metrics.relevance * weights["relevance"]
            )
        else:
            # For technical/system design: accuracy is paramount
            weights = {
                "technical_accuracy": 0.40,
                "answer_structure": 0.20,
                "completeness": 0.25,
                "relevance": 0.15,
            }
            return (
                metrics.technical_accuracy * weights["technical_accuracy"]
                + metrics.answer_structure * weights["answer_structure"]
                + metrics.completeness * weights["completeness"]
                + metrics.relevance * weights["relevance"]
            )
