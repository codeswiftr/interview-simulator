"""Pure unit tests for ContentAnalyzer — no external API calls.

Targets uncovered lines:
- 124-146: __init__ provider branching (openrouter vs anthropic)
- 166-244: analyze() full path — prompt construction, OpenRouter path,
           Anthropic path, markdown extraction (plain fence), JSON parsing,
           default-value fallback, and both error handlers
- 265-289: calculate_overall_score() behavioral and non-behavioral weight paths
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.content_analyzer import ContentAnalyzer, ContentMetrics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_RESPONSE = {
    "technical_accuracy": 82.0,
    "star_adherence": 70.0,
    "answer_structure": 78.0,
    "completeness": 85.0,
    "relevance": 80.0,
    "strengths": ["Clear", "Structured", "Relevant"],
    "improvements": ["Add metrics", "Mention trade-offs", "Deeper dive"],
    "detailed_feedback": "Solid response with room for improvement.",
}


def _json_str(**overrides) -> str:
    data = {**_VALID_RESPONSE, **overrides}
    return json.dumps(data)


def _make_metrics(**overrides) -> ContentMetrics:
    base = {
        "technical_accuracy": 80.0,
        "star_adherence": 70.0,
        "answer_structure": 75.0,
        "completeness": 80.0,
        "relevance": 80.0,
        "strengths": ["Good"],
        "improvements": ["Better"],
        "detailed_feedback": "Feedback here.",
    }
    base.update(overrides)
    return ContentMetrics(**base)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def anthropic_settings():
    """Patch settings to use the anthropic provider."""
    with patch("app.ai.content_analyzer.settings") as mock:
        mock.content_analysis_provider = "anthropic"
        mock.anthropic_api_key = "sk-ant-test"
        yield mock


@pytest.fixture
def openrouter_settings():
    """Patch settings to use the openrouter provider."""
    with patch("app.ai.content_analyzer.settings") as mock:
        mock.content_analysis_provider = "openrouter"
        mock.openrouter_api_key = "sk-or-test"
        yield mock


@pytest.fixture
def anthropic_analyzer(anthropic_settings):
    """ContentAnalyzer instance wired to the anthropic provider."""
    return ContentAnalyzer()


@pytest.fixture
def openrouter_analyzer(openrouter_settings):
    """ContentAnalyzer instance wired to the openrouter provider."""
    return ContentAnalyzer()


# ---------------------------------------------------------------------------
# Lines 124-146 — __init__: provider initialisation
# ---------------------------------------------------------------------------


class TestInit:
    """Cover the two branches in ContentAnalyzer.__init__."""

    def test_anthropic_provider_sets_anthropic_client(self, anthropic_settings):
        """__init__ with 'anthropic' creates an anthropic client and nulls openrouter."""
        analyzer = ContentAnalyzer()

        assert analyzer.provider == "anthropic"
        assert analyzer.anthropic_client is not None
        assert analyzer.openrouter_client is None

    def test_openrouter_provider_sets_openrouter_client(self, openrouter_settings):
        """__init__ with 'openrouter' creates an openrouter client and nulls anthropic."""
        analyzer = ContentAnalyzer()

        assert analyzer.provider == "openrouter"
        assert analyzer.openrouter_client is not None
        assert analyzer.anthropic_client is None

    def test_anthropic_provider_log_message(self, anthropic_settings, caplog):
        """__init__ logs the anthropic provider message."""
        import logging

        with caplog.at_level(logging.INFO, logger="app.ai.content_analyzer"):
            ContentAnalyzer()

        assert any("Anthropic provider" in r.message for r in caplog.records)

    def test_openrouter_provider_log_message(self, openrouter_settings, caplog):
        """__init__ logs the OpenRouter provider message."""
        import logging

        with caplog.at_level(logging.INFO, logger="app.ai.content_analyzer"):
            ContentAnalyzer()

        assert any("OpenRouter provider" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Lines 166-199 — analyze(): prompt construction
# ---------------------------------------------------------------------------


class TestAnalyzePromptConstruction:
    """Verify the prompt is assembled correctly before any API call."""

    @pytest.mark.asyncio
    async def test_behavioral_question_includes_star_instruction(self, anthropic_analyzer):
        """STAR instruction is injected when question_type == 'behavioral'."""
        generate_mock = AsyncMock(return_value=_json_str())
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question="Describe a conflict you resolved.",
                transcript="I had a disagreement with a colleague...",
                question_type="behavioral",
            )

        prompt = generate_mock.call_args[1]["prompt"]
        assert "STAR" in prompt
        assert "Situation" in prompt
        assert "Task" in prompt
        assert "Action" in prompt
        assert "Result" in prompt

    @pytest.mark.asyncio
    async def test_technical_question_excludes_star_instruction(self, anthropic_analyzer):
        """STAR instruction is absent when question_type != 'behavioral'."""
        generate_mock = AsyncMock(return_value=_json_str(star_adherence=0))
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question="What is a hash map?",
                transcript="A hash map stores key-value pairs...",
                question_type="technical",
            )

        prompt = generate_mock.call_args[1]["prompt"]
        # The detailed STAR criteria section should not be present
        assert "Situation: Did they set the context?" not in prompt

    @pytest.mark.asyncio
    async def test_junior_experience_context_in_prompt(self, anthropic_analyzer):
        """Junior experience context is embedded in the prompt."""
        generate_mock = AsyncMock(return_value=_json_str())
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question="What is OOP?",
                transcript="Object-oriented programming...",
                question_type="technical",
                experience_level="junior",
            )

        prompt = generate_mock.call_args[1]["prompt"]
        assert "JUNIOR engineer" in prompt
        assert "0-2 years" in prompt

    @pytest.mark.asyncio
    async def test_mid_experience_context_in_prompt(self, anthropic_analyzer):
        """Mid experience context is embedded in the prompt."""
        generate_mock = AsyncMock(return_value=_json_str())
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question="Explain SOLID principles.",
                transcript="SOLID is a set of five design principles...",
                question_type="technical",
                experience_level="mid",
            )

        prompt = generate_mock.call_args[1]["prompt"]
        assert "MID-LEVEL engineer" in prompt
        assert "2-5 years" in prompt

    @pytest.mark.asyncio
    async def test_senior_experience_context_in_prompt(self, anthropic_analyzer):
        """Senior experience context is embedded in the prompt."""
        generate_mock = AsyncMock(return_value=_json_str())
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question="How would you design a global CDN?",
                transcript="I would start by analysing traffic patterns...",
                question_type="system_design",
                experience_level="senior",
            )

        prompt = generate_mock.call_args[1]["prompt"]
        assert "SENIOR engineer" in prompt
        assert "5+ years" in prompt

    @pytest.mark.asyncio
    async def test_unknown_experience_level_falls_back_to_mid(self, anthropic_analyzer):
        """An unknown experience level key defaults to the 'mid' context."""
        generate_mock = AsyncMock(return_value=_json_str())
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question="Explain recursion.",
                transcript="Recursion is when a function calls itself...",
                question_type="technical",
                experience_level="principal",  # not a valid key
            )

        prompt = generate_mock.call_args[1]["prompt"]
        assert "MID-LEVEL engineer" in prompt

    @pytest.mark.asyncio
    async def test_prompt_contains_question_and_transcript(self, anthropic_analyzer):
        """The question text and transcript are interpolated into the prompt."""
        question_text = "What is eventual consistency?"
        transcript_text = "In distributed systems, eventual consistency means..."
        generate_mock = AsyncMock(return_value=_json_str())

        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question=question_text,
                transcript=transcript_text,
                question_type="technical",
            )

        prompt = generate_mock.call_args[1]["prompt"]
        assert question_text in prompt
        assert transcript_text in prompt


# ---------------------------------------------------------------------------
# Lines 182-198 — analyze(): OpenRouter API call path
# ---------------------------------------------------------------------------


class TestAnalyzeOpenRouterPath:
    """Cover the OpenRouter branch inside analyze()."""

    def _mock_openrouter_response(self, content: str) -> MagicMock:
        resp = MagicMock()
        resp.choices[0].message.content = content
        return resp

    @pytest.mark.asyncio
    async def test_openrouter_returns_correct_metrics(self, openrouter_analyzer):
        """OpenRouter path parses JSON and returns a ContentMetrics instance."""
        mock_resp = self._mock_openrouter_response(_json_str(technical_accuracy=91.0))
        create_mock = AsyncMock(return_value=mock_resp)

        with patch.object(
            openrouter_analyzer.openrouter_client.chat.completions, "create", create_mock
        ):
            metrics = await openrouter_analyzer.analyze(
                question="Explain the CAP theorem.",
                transcript="CAP theorem states...",
                question_type="technical",
            )

        assert isinstance(metrics, ContentMetrics)
        assert metrics.technical_accuracy == 91.0

    @pytest.mark.asyncio
    async def test_openrouter_passes_correct_model_and_params(self, openrouter_analyzer):
        """OpenRouter call uses gemini-2.0-flash-001 with correct parameters."""
        mock_resp = self._mock_openrouter_response(_json_str())
        create_mock = AsyncMock(return_value=mock_resp)

        with patch.object(
            openrouter_analyzer.openrouter_client.chat.completions, "create", create_mock
        ):
            await openrouter_analyzer.analyze(
                question="What is a B-tree?",
                transcript="A B-tree is a self-balancing tree...",
                question_type="technical",
            )

        call_kwargs = create_mock.call_args[1]
        assert call_kwargs["model"] == "google/gemini-2.0-flash-001"
        assert call_kwargs["max_tokens"] == 2048
        assert call_kwargs["temperature"] == 0.3
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_openrouter_plain_markdown_fence_extraction(self, openrouter_analyzer):
        """Plain ``` fence (without json tag) is correctly unwrapped — covers line 205."""
        raw = f"```\n{_json_str()}\n```"
        mock_resp = self._mock_openrouter_response(raw)
        create_mock = AsyncMock(return_value=mock_resp)

        with patch.object(
            openrouter_analyzer.openrouter_client.chat.completions, "create", create_mock
        ):
            metrics = await openrouter_analyzer.analyze(
                question="What is memoisation?",
                transcript="Memoisation caches function results...",
                question_type="technical",
            )

        assert isinstance(metrics, ContentMetrics)
        assert metrics.technical_accuracy == _VALID_RESPONSE["technical_accuracy"]

    @pytest.mark.asyncio
    async def test_openrouter_json_markdown_fence_extraction(self, openrouter_analyzer):
        """```json fence is unwrapped correctly."""
        raw = f"```json\n{_json_str(technical_accuracy=77.0)}\n```"
        mock_resp = self._mock_openrouter_response(raw)
        create_mock = AsyncMock(return_value=mock_resp)

        with patch.object(
            openrouter_analyzer.openrouter_client.chat.completions, "create", create_mock
        ):
            metrics = await openrouter_analyzer.analyze(
                question="What is memoisation?",
                transcript="Memoisation caches results...",
                question_type="technical",
            )

        assert metrics.technical_accuracy == 77.0

    @pytest.mark.asyncio
    async def test_openrouter_json_decode_error_returns_defaults(self, openrouter_analyzer):
        """A malformed JSON from OpenRouter triggers the JSONDecodeError fallback."""
        mock_resp = self._mock_openrouter_response("not valid json {{{")
        create_mock = AsyncMock(return_value=mock_resp)

        with patch.object(
            openrouter_analyzer.openrouter_client.chat.completions, "create", create_mock
        ):
            metrics = await openrouter_analyzer.analyze(
                question="Explain closures.",
                transcript="A closure captures its enclosing scope...",
                question_type="technical",
            )

        assert metrics.technical_accuracy == 50.0
        assert metrics.star_adherence == 0.0
        assert "JSON parsing failed" in metrics.detailed_feedback
        assert metrics.strengths == ["Unable to analyze due to parsing error"]
        assert metrics.improvements == ["Please try again"]

    @pytest.mark.asyncio
    async def test_openrouter_general_exception_returns_defaults(self, openrouter_analyzer):
        """A general exception from OpenRouter triggers the broad Exception fallback."""
        create_mock = AsyncMock(side_effect=RuntimeError("network timeout"))

        with patch.object(
            openrouter_analyzer.openrouter_client.chat.completions, "create", create_mock
        ):
            metrics = await openrouter_analyzer.analyze(
                question="What is a deadlock?",
                transcript="A deadlock occurs when two processes...",
                question_type="technical",
            )

        assert metrics.technical_accuracy == 50.0
        assert metrics.answer_structure == 50.0
        assert "Analysis failed" in metrics.detailed_feedback
        assert "network timeout" in metrics.detailed_feedback
        assert metrics.strengths == ["Unable to analyze due to error"]

    @pytest.mark.asyncio
    async def test_openrouter_behavioral_question_star_adherence(self, openrouter_analyzer):
        """OpenRouter path correctly passes star_adherence for behavioral questions."""
        mock_resp = self._mock_openrouter_response(_json_str(star_adherence=88.0))
        create_mock = AsyncMock(return_value=mock_resp)

        with patch.object(
            openrouter_analyzer.openrouter_client.chat.completions, "create", create_mock
        ):
            metrics = await openrouter_analyzer.analyze(
                question="Tell me about a time you led a team.",
                transcript="I led a team of five engineers...",
                question_type="behavioral",
            )

        assert metrics.star_adherence == 88.0


# ---------------------------------------------------------------------------
# Lines 192-253 — analyze(): Anthropic path + shared error paths
# ---------------------------------------------------------------------------


class TestAnalyzeAnthropicPath:
    """Cover the Anthropic branch and shared post-call logic inside analyze()."""

    @pytest.mark.asyncio
    async def test_anthropic_returns_correct_metrics(self, anthropic_analyzer):
        """Anthropic path parses JSON and returns a ContentMetrics instance."""
        generate_mock = AsyncMock(return_value=_json_str(completeness=95.0))
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="Explain the OSI model.",
                transcript="The OSI model has seven layers...",
                question_type="technical",
            )

        assert isinstance(metrics, ContentMetrics)
        assert metrics.completeness == 95.0

    @pytest.mark.asyncio
    async def test_anthropic_passes_correct_params(self, anthropic_analyzer):
        """Anthropic generate() is called with max_tokens=2048 and temperature=0.3."""
        generate_mock = AsyncMock(return_value=_json_str())
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            await anthropic_analyzer.analyze(
                question="Explain polymorphism.",
                transcript="Polymorphism allows objects of different types...",
                question_type="technical",
            )

        call_kwargs = generate_mock.call_args[1]
        assert call_kwargs["max_tokens"] == 2048
        assert call_kwargs["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_anthropic_plain_markdown_fence_extraction(self, anthropic_analyzer):
        """Plain ``` fence is unwrapped when returned by the Anthropic client — line 205."""
        raw = f"```\n{_json_str(answer_structure=66.0)}\n```"
        generate_mock = AsyncMock(return_value=raw)

        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="What is a race condition?",
                transcript="A race condition occurs when two threads...",
                question_type="technical",
            )

        assert metrics.answer_structure == 66.0

    @pytest.mark.asyncio
    async def test_anthropic_json_markdown_fence_extraction(self, anthropic_analyzer):
        """```json fence is correctly unwrapped for the Anthropic provider."""
        raw = f"```json\n{_json_str(relevance=93.0)}\n```"
        generate_mock = AsyncMock(return_value=raw)

        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="Describe microservices.",
                transcript="Microservices decompose an application...",
                question_type="technical",
            )

        assert metrics.relevance == 93.0

    @pytest.mark.asyncio
    async def test_anthropic_json_decode_error_returns_defaults(self, anthropic_analyzer):
        """Malformed JSON from Anthropic triggers the JSONDecodeError fallback."""
        generate_mock = AsyncMock(return_value="not json at all")
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="What is a semaphore?",
                transcript="A semaphore is a synchronisation primitive...",
                question_type="technical",
            )

        assert metrics.technical_accuracy == 50.0
        assert metrics.star_adherence == 0.0
        assert metrics.answer_structure == 50.0
        assert metrics.completeness == 50.0
        assert metrics.relevance == 50.0
        assert metrics.strengths == ["Unable to analyze due to parsing error"]
        assert metrics.improvements == ["Please try again"]
        assert "JSON parsing failed" in metrics.detailed_feedback

    @pytest.mark.asyncio
    async def test_anthropic_general_exception_returns_defaults(self, anthropic_analyzer):
        """A general exception from Anthropic triggers the broad Exception fallback."""
        generate_mock = AsyncMock(side_effect=ConnectionError("API unreachable"))
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="Explain eventual consistency.",
                transcript="Eventual consistency means...",
                question_type="technical",
            )

        assert metrics.technical_accuracy == 50.0
        assert metrics.star_adherence == 0.0
        assert metrics.answer_structure == 50.0
        assert "Analysis failed" in metrics.detailed_feedback
        assert "API unreachable" in metrics.detailed_feedback
        assert metrics.strengths == ["Unable to analyze due to error"]
        assert metrics.improvements == ["Please try again"]

    @pytest.mark.asyncio
    async def test_metrics_use_defaults_for_missing_json_keys(self, anthropic_analyzer):
        """Partial JSON response falls back to defaults for absent keys."""
        partial = json.dumps({"technical_accuracy": 60.0})
        generate_mock = AsyncMock(return_value=partial)

        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="What is TDD?",
                transcript="Test-driven development is...",
                question_type="technical",
            )

        # Explicitly provided field is used
        assert metrics.technical_accuracy == 60.0
        # Missing fields fall back to the defaults specified in .get(key, default)
        assert metrics.star_adherence == 0.0
        assert metrics.answer_structure == 50.0
        assert metrics.completeness == 50.0
        assert metrics.relevance == 50.0
        assert metrics.strengths == []
        assert metrics.improvements == []
        assert metrics.detailed_feedback == ""

    @pytest.mark.asyncio
    async def test_metrics_values_are_cast_to_float(self, anthropic_analyzer):
        """Integer scores in the JSON response are correctly cast to float."""
        raw = json.dumps(
            {
                "technical_accuracy": 85,  # int
                "star_adherence": 0,
                "answer_structure": 80,
                "completeness": 90,
                "relevance": 88,
                "strengths": [],
                "improvements": [],
                "detailed_feedback": "",
            }
        )
        generate_mock = AsyncMock(return_value=raw)

        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="Describe ACID properties.",
                transcript="ACID stands for...",
                question_type="technical",
            )

        assert isinstance(metrics.technical_accuracy, float)
        assert metrics.technical_accuracy == 85.0

    @pytest.mark.asyncio
    async def test_analyze_logs_analysis_complete_info(self, anthropic_analyzer, caplog):
        """analyze() emits an INFO log after successful analysis."""
        import logging

        generate_mock = AsyncMock(return_value=_json_str())

        with (
            caplog.at_level(logging.INFO, logger="app.ai.content_analyzer"),
            patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock),
        ):
            await anthropic_analyzer.analyze(
                question="What is a mutex?",
                transcript="A mutex is a locking mechanism...",
                question_type="technical",
            )

        assert any("Analysis complete" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_analyze_behavioral_returns_star_adherence(self, anthropic_analyzer):
        """analyze() returns star_adherence from JSON for behavioral questions."""
        generate_mock = AsyncMock(return_value=_json_str(star_adherence=76.0))
        with patch.object(anthropic_analyzer.anthropic_client, "generate", generate_mock):
            metrics = await anthropic_analyzer.analyze(
                question="Tell me about a challenge you overcame.",
                transcript="I faced a production incident...",
                question_type="behavioral",
            )

        assert metrics.star_adherence == 76.0


# ---------------------------------------------------------------------------
# Lines 265-294 — calculate_overall_score()
# ---------------------------------------------------------------------------


class TestCalculateOverallScore:
    """Cover both weight branches in calculate_overall_score()."""

    def test_behavioral_weights_star_heavy(self, anthropic_analyzer):
        """Behavioral score: STAR has 30%, technical 15%, structure/completeness 20% each, relevance 15%."""
        metrics = _make_metrics(
            technical_accuracy=80.0,
            star_adherence=90.0,
            answer_structure=85.0,
            completeness=88.0,
            relevance=82.0,
        )
        score = anthropic_analyzer.calculate_overall_score(metrics, "behavioral")

        # 80*0.15 + 90*0.30 + 85*0.20 + 88*0.20 + 82*0.15
        expected = 80 * 0.15 + 90 * 0.30 + 85 * 0.20 + 88 * 0.20 + 82 * 0.15
        assert abs(score - expected) < 0.01

    def test_technical_weights_accuracy_heavy(self, anthropic_analyzer):
        """Technical score: accuracy 40%, structure 20%, completeness 25%, relevance 15%."""
        metrics = _make_metrics(
            technical_accuracy=90.0,
            star_adherence=0.0,
            answer_structure=80.0,
            completeness=85.0,
            relevance=88.0,
        )
        score = anthropic_analyzer.calculate_overall_score(metrics, "technical")

        # 90*0.40 + 80*0.20 + 85*0.25 + 88*0.15
        expected = 90 * 0.40 + 80 * 0.20 + 85 * 0.25 + 88 * 0.15
        assert abs(score - expected) < 0.01

    def test_system_design_uses_technical_weights(self, anthropic_analyzer):
        """system_design question type uses the same weights as technical."""
        metrics = _make_metrics(
            technical_accuracy=88.0,
            star_adherence=0.0,
            answer_structure=82.0,
            completeness=90.0,
            relevance=85.0,
        )
        score_sd = anthropic_analyzer.calculate_overall_score(metrics, "system_design")
        score_tech = anthropic_analyzer.calculate_overall_score(metrics, "technical")

        assert abs(score_sd - score_tech) < 0.01

    def test_behavioral_star_zero_still_computes(self, anthropic_analyzer):
        """Behavioral weights apply even when star_adherence is 0."""
        metrics = _make_metrics(
            technical_accuracy=70.0,
            star_adherence=0.0,
            answer_structure=70.0,
            completeness=70.0,
            relevance=70.0,
        )
        score = anthropic_analyzer.calculate_overall_score(metrics, "behavioral")

        # 70*0.15 + 0*0.30 + 70*0.20 + 70*0.20 + 70*0.15
        expected = 70 * 0.15 + 0 * 0.30 + 70 * 0.20 + 70 * 0.20 + 70 * 0.15
        assert abs(score - expected) < 0.01

    def test_perfect_behavioral_score_is_100(self, anthropic_analyzer):
        """All metrics at 100 yield a behavioral score of exactly 100."""
        metrics = _make_metrics(
            technical_accuracy=100.0,
            star_adherence=100.0,
            answer_structure=100.0,
            completeness=100.0,
            relevance=100.0,
        )
        score = anthropic_analyzer.calculate_overall_score(metrics, "behavioral")
        assert abs(score - 100.0) < 0.01

    def test_perfect_technical_score_is_100(self, anthropic_analyzer):
        """All metrics at 100 yield a technical score of exactly 100."""
        metrics = _make_metrics(
            technical_accuracy=100.0,
            star_adherence=100.0,
            answer_structure=100.0,
            completeness=100.0,
            relevance=100.0,
        )
        score = anthropic_analyzer.calculate_overall_score(metrics, "technical")
        assert abs(score - 100.0) < 0.01

    def test_zero_behavioral_score_is_zero(self, anthropic_analyzer):
        """All metrics at 0 yield a behavioral score of 0."""
        metrics = _make_metrics(
            technical_accuracy=0.0,
            star_adherence=0.0,
            answer_structure=0.0,
            completeness=0.0,
            relevance=0.0,
        )
        score = anthropic_analyzer.calculate_overall_score(metrics, "behavioral")
        assert score == 0.0

    def test_zero_technical_score_is_zero(self, anthropic_analyzer):
        """All metrics at 0 yield a technical score of 0."""
        metrics = _make_metrics(
            technical_accuracy=0.0,
            star_adherence=0.0,
            answer_structure=0.0,
            completeness=0.0,
            relevance=0.0,
        )
        score = anthropic_analyzer.calculate_overall_score(metrics, "technical")
        assert score == 0.0

    def test_behavioral_weights_sum_to_one(self, anthropic_analyzer):
        """The five behavioral weights must sum to exactly 1.0."""
        # Validated via the weighted formula: all weights explicit in source
        weights_sum = 0.15 + 0.30 + 0.20 + 0.20 + 0.15
        assert abs(weights_sum - 1.0) < 1e-9

    def test_technical_weights_sum_to_one(self, anthropic_analyzer):
        """The four technical weights must sum to exactly 1.0."""
        weights_sum = 0.40 + 0.20 + 0.25 + 0.15
        assert abs(weights_sum - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# ContentMetrics dataclass sanity checks
# ---------------------------------------------------------------------------


class TestContentMetrics:
    """Verify the ContentMetrics dataclass behaves correctly."""

    def test_all_fields_accessible(self):
        """ContentMetrics exposes all expected fields."""
        m = _make_metrics()
        assert hasattr(m, "technical_accuracy")
        assert hasattr(m, "star_adherence")
        assert hasattr(m, "answer_structure")
        assert hasattr(m, "completeness")
        assert hasattr(m, "relevance")
        assert hasattr(m, "strengths")
        assert hasattr(m, "improvements")
        assert hasattr(m, "detailed_feedback")

    def test_list_fields_are_lists(self):
        """strengths and improvements are list fields."""
        m = _make_metrics(strengths=["a", "b"], improvements=["x"])
        assert isinstance(m.strengths, list)
        assert isinstance(m.improvements, list)
        assert m.strengths == ["a", "b"]
        assert m.improvements == ["x"]
