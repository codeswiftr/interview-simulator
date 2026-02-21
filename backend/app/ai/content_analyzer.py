"""Content analysis service using Claude for semantic evaluation.

Supports multiple providers:
- Anthropic (via forge_shared.ai)
- OpenRouter (via OpenAI-compatible API)
"""

import json
import logging
from dataclasses import dataclass

from forge_shared.ai import RetryConfig, create_client
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
{experience_context}
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

    # Experience-level specific context for personalized feedback
    EXPERIENCE_CONTEXT = {
        "junior": """
CANDIDATE CONTEXT: This candidate is a JUNIOR engineer (0-2 years experience).

When providing feedback, please:
- Be encouraging and supportive in tone while still being constructive
- Acknowledge that they are building foundational skills
- Provide explicit, actionable tips they can apply immediately
- Focus on fundamental concepts rather than advanced nuances
- Celebrate what they did well before diving into improvements
- Score slightly more leniently on depth of technical knowledge, but maintain standards for clarity and structure
""",
        "mid": """
CANDIDATE CONTEXT: This candidate is a MID-LEVEL engineer (2-5 years experience).

When providing feedback, please:
- Balance encouragement with direct constructive criticism
- Focus on growth areas and next-level skills they should develop
- Expect solid fundamentals and look for emerging strategic thinking
- Provide actionable improvements focused on career advancement
- Point out opportunities to demonstrate more senior-level thinking
""",
        "senior": """
CANDIDATE CONTEXT: This candidate is a SENIOR engineer (5+ years experience).

When providing feedback, please:
- Be direct and concise - senior engineers appreciate candid feedback
- Hold to higher standards for depth, leadership qualities, and strategic thinking
- Focus on nuance, trade-offs, and system-wide implications
- Expect them to demonstrate mentorship mindset and sound decision-making
- Point out areas where they could better showcase their seniority
- Look for evidence of leadership, ownership, and technical depth
""",
    }

    def __init__(self) -> None:
        """Initialize the content analyzer based on configured provider."""
        self.provider = settings.content_analysis_provider

        if self.provider == "openrouter":
            self.openrouter_client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            self.anthropic_client = None
            logger.info("ContentAnalyzer using OpenRouter provider (Gemini 2.0 Flash)")
        else:
            # Use forge_shared.ai client with built-in retry
            self.anthropic_client = create_client(
                provider="anthropic",
                api_key=settings.anthropic_api_key,
                default_model="claude-3-5-haiku-20241022",
                retry_config=RetryConfig(
                    max_retries=3,
                    base_delay=2.0,
                    max_delay=10.0,
                ),
            )
            self.openrouter_client = None
            logger.info("ContentAnalyzer using Anthropic provider (via forge_shared.ai)")

    async def analyze(
        self,
        question: str,
        transcript: str,
        question_type: str,
        experience_level: str = "mid",
    ) -> ContentMetrics:
        """Analyze response content using Claude.

        Args:
            question: The interview question
            transcript: The candidate's transcribed response
            question_type: Type of question (behavioral, technical, system_design)
            experience_level: User's experience level (junior, mid, senior)

        Returns:
            ContentMetrics with analysis results
        """
        star_instruction = self.STAR_INSTRUCTION if question_type == "behavioral" else ""

        # Get experience-level-specific context
        experience_context = self.EXPERIENCE_CONTEXT.get(
            experience_level, self.EXPERIENCE_CONTEXT["mid"]
        )

        prompt = self.ANALYSIS_PROMPT.format(
            question=question,
            question_type=question_type,
            transcript=transcript,
            star_instruction=star_instruction,
            experience_context=experience_context,
        )

        try:
            if self.provider == "openrouter":
                # Use OpenRouter with Gemini 2.0 Flash (fast, cheap, high quality)
                # Pricing: $0.10/M input, $0.40/M output
                response = await self.openrouter_client.chat.completions.create(
                    model="google/gemini-2.0-flash-001",
                    max_tokens=2048,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content
            else:
                # Use forge_shared.ai client
                content = await self.anthropic_client.generate(
                    prompt=prompt,
                    max_tokens=2048,
                    temperature=0.3,
                )
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
