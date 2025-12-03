"""Tests for content analysis service using Claude API."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.content_analyzer import ContentAnalyzer, ContentMetrics


@pytest.fixture
def mock_settings():
    """Mock settings to use anthropic provider."""
    with patch("app.ai.content_analyzer.settings") as mock:
        mock.content_analysis_provider = "anthropic"
        mock.anthropic_api_key = "test_key"
        yield mock


@pytest.fixture
def mock_anthropic_response():
    """Create a mock Anthropic API response."""

    def _create_response(
        technical_accuracy: float = 85.0,
        star_adherence: float = 75.0,
        answer_structure: float = 80.0,
        completeness: float = 90.0,
        relevance: float = 88.0,
    ) -> MagicMock:
        response_data = {
            "technical_accuracy": technical_accuracy,
            "star_adherence": star_adherence,
            "answer_structure": answer_structure,
            "completeness": completeness,
            "relevance": relevance,
            "strengths": [
                "Clear and well-structured response",
                "Good use of specific examples",
                "Strong technical understanding",
            ],
            "improvements": [
                "Could add more quantifiable results",
                "Consider mentioning trade-offs",
                "Elaborate on the impact",
            ],
            "detailed_feedback": "Your response demonstrates strong technical knowledge and good "
            "communication skills. You effectively used specific examples to illustrate your points.",
        }

        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps(response_data)
        mock_response.content = [mock_content]

        return mock_response

    return _create_response


@pytest.mark.asyncio
async def test_analyze_behavioral_question(mock_settings, mock_anthropic_response):
    """Test analyzing a behavioral question with STAR method."""
    analyzer = ContentAnalyzer()

    mock_response = mock_anthropic_response(star_adherence=85.0)

    with patch.object(analyzer.anthropic_client.messages, "create", new=AsyncMock(return_value=mock_response)):
        metrics = await analyzer.analyze(
            question="Tell me about a time you faced a challenging project deadline.",
            transcript="In my previous role, we had a critical feature release scheduled. "
            "I coordinated with the team, broke down tasks, and we delivered on time.",
            question_type="behavioral",
        )

    assert isinstance(metrics, ContentMetrics)
    assert metrics.technical_accuracy == 85.0
    assert metrics.star_adherence == 85.0
    assert metrics.answer_structure == 80.0
    assert metrics.completeness == 90.0
    assert metrics.relevance == 88.0
    assert len(metrics.strengths) == 3
    assert len(metrics.improvements) == 3
    assert "demonstrates strong technical knowledge" in metrics.detailed_feedback.lower()


@pytest.mark.asyncio
async def test_analyze_technical_question(mock_settings, mock_anthropic_response):
    """Test analyzing a technical question."""
    analyzer = ContentAnalyzer()

    mock_response = mock_anthropic_response(
        technical_accuracy=90.0,
        star_adherence=0.0,  # Not applicable for technical questions
    )

    with patch.object(analyzer.anthropic_client.messages, "create", new=AsyncMock(return_value=mock_response)):
        metrics = await analyzer.analyze(
            question="Explain the difference between SQL and NoSQL databases.",
            transcript="SQL databases are relational with structured schemas, while NoSQL "
            "databases offer flexible data models. SQL uses ACID transactions, NoSQL prioritizes "
            "scalability and availability.",
            question_type="technical",
        )

    assert isinstance(metrics, ContentMetrics)
    assert metrics.technical_accuracy == 90.0
    assert metrics.star_adherence == 0.0  # Not used for technical questions
    assert metrics.answer_structure == 80.0
    assert metrics.completeness == 90.0


@pytest.mark.asyncio
async def test_analyze_system_design_question(mock_settings, mock_anthropic_response):
    """Test analyzing a system design question."""
    analyzer = ContentAnalyzer()

    mock_response = mock_anthropic_response(
        technical_accuracy=88.0,
        completeness=85.0,
        star_adherence=0.0,
    )

    with patch.object(analyzer.anthropic_client.messages, "create", new=AsyncMock(return_value=mock_response)):
        metrics = await analyzer.analyze(
            question="Design a URL shortening service like bit.ly.",
            transcript="I would use a hash function to generate short codes, store mappings in "
            "a distributed database for scalability, implement caching for frequently accessed URLs, "
            "and use load balancers for high availability.",
            question_type="system_design",
        )

    assert isinstance(metrics, ContentMetrics)
    assert metrics.technical_accuracy == 88.0
    assert metrics.completeness == 85.0
    assert metrics.star_adherence == 0.0


@pytest.mark.asyncio
async def test_analyze_handles_json_in_markdown(mock_settings):
    """Test that analyzer correctly extracts JSON from markdown code blocks."""
    analyzer = ContentAnalyzer()

    response_data = {
        "technical_accuracy": 75.0,
        "star_adherence": 0.0,
        "answer_structure": 70.0,
        "completeness": 80.0,
        "relevance": 85.0,
        "strengths": ["Good start", "Clear explanation"],
        "improvements": ["Add more details", "Include examples"],
        "detailed_feedback": "Solid response with room for improvement.",
    }

    # Simulate response wrapped in markdown
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = f"```json\n{json.dumps(response_data)}\n```"
    mock_response.content = [mock_content]

    with patch.object(analyzer.anthropic_client.messages, "create", new=AsyncMock(return_value=mock_response)):
        metrics = await analyzer.analyze(
            question="Test question",
            transcript="Test answer",
            question_type="technical",
        )

    assert metrics.technical_accuracy == 75.0
    assert metrics.answer_structure == 70.0


@pytest.mark.asyncio
async def test_analyze_handles_api_errors(mock_settings):
    """Test that analyzer gracefully handles API errors."""
    analyzer = ContentAnalyzer()

    with patch.object(
        analyzer.anthropic_client.messages,
        "create",
        side_effect=Exception("API connection failed"),
    ):
        metrics = await analyzer.analyze(
            question="Test question",
            transcript="Test answer",
            question_type="technical",
        )

    # Should return default error metrics
    assert metrics.technical_accuracy == 50.0
    assert metrics.star_adherence == 0.0
    assert metrics.answer_structure == 50.0
    assert metrics.completeness == 50.0
    assert metrics.relevance == 50.0
    assert "Unable to analyze due to error" in metrics.strengths
    assert "Please try again" in metrics.improvements
    assert "Analysis failed" in metrics.detailed_feedback


@pytest.mark.asyncio
async def test_analyze_handles_malformed_json(mock_settings):
    """Test that analyzer handles malformed JSON responses gracefully."""
    analyzer = ContentAnalyzer()

    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is not valid JSON at all"
    mock_response.content = [mock_content]

    with patch.object(analyzer.anthropic_client.messages, "create", new=AsyncMock(return_value=mock_response)):
        metrics = await analyzer.analyze(
            question="Test question",
            transcript="Test answer",
            question_type="technical",
        )

    # Should return default error metrics
    assert metrics.technical_accuracy == 50.0
    assert "JSON parsing failed" in metrics.detailed_feedback


def test_calculate_overall_score_behavioral():
    """Test overall score calculation for behavioral questions."""
    analyzer = ContentAnalyzer()

    metrics = ContentMetrics(
        technical_accuracy=80.0,
        star_adherence=90.0,
        answer_structure=85.0,
        completeness=88.0,
        relevance=82.0,
        strengths=["Good"],
        improvements=["Better"],
        detailed_feedback="Feedback",
    )

    score = analyzer.calculate_overall_score(metrics, "behavioral")

    # For behavioral: STAR method has 30% weight, should be significant
    # 80*0.15 + 90*0.30 + 85*0.20 + 88*0.20 + 82*0.15 = 85.9
    assert 85.0 <= score <= 86.5


def test_calculate_overall_score_technical():
    """Test overall score calculation for technical questions."""
    analyzer = ContentAnalyzer()

    metrics = ContentMetrics(
        technical_accuracy=90.0,
        star_adherence=0.0,  # Not used for technical
        answer_structure=80.0,
        completeness=85.0,
        relevance=88.0,
        strengths=["Good"],
        improvements=["Better"],
        detailed_feedback="Feedback",
    )

    score = analyzer.calculate_overall_score(metrics, "technical")

    # For technical: accuracy has 40% weight
    # 90*0.40 + 80*0.20 + 85*0.25 + 88*0.15 = 86.45
    assert 86.0 <= score <= 87.0


def test_calculate_overall_score_system_design():
    """Test overall score calculation for system design questions."""
    analyzer = ContentAnalyzer()

    metrics = ContentMetrics(
        technical_accuracy=88.0,
        star_adherence=0.0,
        answer_structure=82.0,
        completeness=90.0,
        relevance=85.0,
        strengths=["Good"],
        improvements=["Better"],
        detailed_feedback="Feedback",
    )

    score = analyzer.calculate_overall_score(metrics, "system_design")

    # System design uses same weights as technical
    # 88*0.40 + 82*0.20 + 90*0.25 + 85*0.15 = 86.5
    assert 86.0 <= score <= 87.0


@pytest.mark.asyncio
async def test_prompt_includes_star_instruction_for_behavioral(mock_settings):
    """Test that STAR instruction is included for behavioral questions."""
    analyzer = ContentAnalyzer()

    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(
        {
            "technical_accuracy": 80,
            "star_adherence": 85,
            "answer_structure": 80,
            "completeness": 80,
            "relevance": 80,
            "strengths": ["test"],
            "improvements": ["test"],
            "detailed_feedback": "test",
        }
    )
    mock_response.content = [mock_content]

    create_mock = AsyncMock(return_value=mock_response)

    with patch.object(analyzer.anthropic_client.messages, "create", new=create_mock):
        await analyzer.analyze(
            question="Tell me about a challenge",
            transcript="I faced a challenge...",
            question_type="behavioral",
        )

    # Check that the prompt included STAR instruction
    call_args = create_mock.call_args
    prompt_content = call_args[1]["messages"][0]["content"]
    assert "STAR" in prompt_content
    assert "Situation" in prompt_content
    assert "Task" in prompt_content
    assert "Action" in prompt_content
    assert "Result" in prompt_content


@pytest.mark.asyncio
async def test_prompt_excludes_star_instruction_for_technical(mock_settings):
    """Test that STAR instruction is excluded for technical questions."""
    analyzer = ContentAnalyzer()

    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(
        {
            "technical_accuracy": 80,
            "star_adherence": 0,
            "answer_structure": 80,
            "completeness": 80,
            "relevance": 80,
            "strengths": ["test"],
            "improvements": ["test"],
            "detailed_feedback": "test",
        }
    )
    mock_response.content = [mock_content]

    create_mock = AsyncMock(return_value=mock_response)

    with patch.object(analyzer.anthropic_client.messages, "create", new=create_mock):
        await analyzer.analyze(
            question="What is polymorphism?",
            transcript="Polymorphism is...",
            question_type="technical",
        )

    # Check that the prompt did not include STAR instruction
    call_args = create_mock.call_args
    prompt_content = call_args[1]["messages"][0]["content"]
    assert "STAR" not in prompt_content or "STAR Adherence" not in prompt_content


@pytest.mark.asyncio
async def test_prompt_includes_junior_experience_context(mock_settings):
    """Test that junior experience level context is included in the prompt."""
    analyzer = ContentAnalyzer()

    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(
        {
            "technical_accuracy": 80,
            "star_adherence": 0,
            "answer_structure": 80,
            "completeness": 80,
            "relevance": 80,
            "strengths": ["test"],
            "improvements": ["test"],
            "detailed_feedback": "test",
        }
    )
    mock_response.content = [mock_content]

    create_mock = AsyncMock(return_value=mock_response)

    with patch.object(analyzer.anthropic_client.messages, "create", new=create_mock):
        await analyzer.analyze(
            question="What is a REST API?",
            transcript="A REST API is...",
            question_type="technical",
            experience_level="junior",
        )

    # Check that the prompt includes junior context
    call_args = create_mock.call_args
    prompt_content = call_args[1]["messages"][0]["content"]
    assert "JUNIOR engineer" in prompt_content
    assert "0-2 years experience" in prompt_content
    assert "encouraging" in prompt_content.lower()


@pytest.mark.asyncio
async def test_prompt_includes_senior_experience_context(mock_settings):
    """Test that senior experience level context is included in the prompt."""
    analyzer = ContentAnalyzer()

    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(
        {
            "technical_accuracy": 80,
            "star_adherence": 0,
            "answer_structure": 80,
            "completeness": 80,
            "relevance": 80,
            "strengths": ["test"],
            "improvements": ["test"],
            "detailed_feedback": "test",
        }
    )
    mock_response.content = [mock_content]

    create_mock = AsyncMock(return_value=mock_response)

    with patch.object(analyzer.anthropic_client.messages, "create", new=create_mock):
        await analyzer.analyze(
            question="Design a distributed cache system",
            transcript="I would use consistent hashing...",
            question_type="system_design",
            experience_level="senior",
        )

    # Check that the prompt includes senior context
    call_args = create_mock.call_args
    prompt_content = call_args[1]["messages"][0]["content"]
    assert "SENIOR engineer" in prompt_content
    assert "5+ years experience" in prompt_content
    assert "direct" in prompt_content.lower()
    assert "leadership" in prompt_content.lower()


@pytest.mark.asyncio
async def test_prompt_includes_mid_experience_context_by_default(mock_settings):
    """Test that mid experience level context is used by default."""
    analyzer = ContentAnalyzer()

    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(
        {
            "technical_accuracy": 80,
            "star_adherence": 0,
            "answer_structure": 80,
            "completeness": 80,
            "relevance": 80,
            "strengths": ["test"],
            "improvements": ["test"],
            "detailed_feedback": "test",
        }
    )
    mock_response.content = [mock_content]

    create_mock = AsyncMock(return_value=mock_response)

    with patch.object(analyzer.anthropic_client.messages, "create", new=create_mock):
        # Don't pass experience_level - should default to mid
        await analyzer.analyze(
            question="What is polymorphism?",
            transcript="Polymorphism is...",
            question_type="technical",
        )

    # Check that the prompt includes mid-level context
    call_args = create_mock.call_args
    prompt_content = call_args[1]["messages"][0]["content"]
    assert "MID-LEVEL engineer" in prompt_content
    assert "2-5 years experience" in prompt_content


@pytest.mark.asyncio
async def test_prompt_uses_mid_for_unknown_experience_level(mock_settings):
    """Test that unknown experience levels fall back to mid."""
    analyzer = ContentAnalyzer()

    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = json.dumps(
        {
            "technical_accuracy": 80,
            "star_adherence": 0,
            "answer_structure": 80,
            "completeness": 80,
            "relevance": 80,
            "strengths": ["test"],
            "improvements": ["test"],
            "detailed_feedback": "test",
        }
    )
    mock_response.content = [mock_content]

    create_mock = AsyncMock(return_value=mock_response)

    with patch.object(analyzer.anthropic_client.messages, "create", new=create_mock):
        await analyzer.analyze(
            question="What is polymorphism?",
            transcript="Polymorphism is...",
            question_type="technical",
            experience_level="expert",  # Unknown level
        )

    # Should fall back to mid-level context
    call_args = create_mock.call_args
    prompt_content = call_args[1]["messages"][0]["content"]
    assert "MID-LEVEL engineer" in prompt_content
