"""Tests for interview-sim CLI."""

import json
import subprocess

import pytest


def run_cli(cmd: list[str], expect_success: bool = True) -> dict:
    """Run CLI command and return parsed JSON output.

    Args:
        cmd: Command and arguments (without --json, added automatically)
        expect_success: Whether to expect success=true in response

    Returns:
        Parsed JSON response

    Raises:
        AssertionError: If output doesn't match expectations
    """
    # Add --json if not present
    if "--json" not in cmd:
        cmd.append("--json")

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    # Parse JSON output
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(
            f"Failed to parse JSON output: {e}\nStdout: {result.stdout}\nStderr: {result.stderr}"
        )

    # Validate response structure
    assert "success" in response, "Response missing 'success' field"
    assert "data" in response, "Response missing 'data' field"
    assert "timestamp" in response, "Response missing 'timestamp' field"

    if expect_success:
        assert response["success"] is True, f"Expected success=true, got: {response}"
        assert response["error"] is None, f"Expected no error, got: {response['error']}"
    else:
        assert response["success"] is False, "Expected success=false"
        assert response["error"] is not None, "Expected error message"
        assert response["error_code"] is not None, "Expected error_code"

    return response


class TestCLIVersion:
    """Test version command."""

    def test_version_command(self):
        """Test that version command returns proper structure."""
        response = run_cli(["interview-sim", "version"])

        data = response["data"]
        assert "version" in data
        assert "app" in data
        assert data["app"] == "interview-simulator"


class TestGenerateQuestions:
    """Test generate-questions command."""

    def test_generate_questions_basic(self):
        """Test basic question generation."""
        response = run_cli(
            [
                "interview-sim",
                "generate-questions",
                "--topic",
                "leadership",
                "--count",
                "2",
            ]
        )

        data = response["data"]
        assert "questions" in data
        assert "count" in data
        assert data["topic"] == "leadership"
        assert isinstance(data["questions"], list)

    def test_generate_questions_with_difficulty(self):
        """Test question generation with difficulty."""
        response = run_cli(
            [
                "interview-sim",
                "generate-questions",
                "--topic",
                "arrays",
                "--count",
                "1",
                "--difficulty",
                "hard",
                "--category",
                "technical",
            ]
        )

        data = response["data"]
        assert data["difficulty"] == "hard"
        assert data["category"] == "technical"

    def test_generate_questions_invalid_difficulty(self):
        """Test that invalid difficulty returns error."""
        response = run_cli(
            [
                "interview-sim",
                "generate-questions",
                "--topic",
                "test",
                "--difficulty",
                "invalid",
            ],
            expect_success=False,
        )

        assert response["error_code"] == "INVALID_INPUT"
        assert "Invalid difficulty" in response["error"]

    def test_generate_questions_invalid_category(self):
        """Test that invalid category returns error."""
        response = run_cli(
            [
                "interview-sim",
                "generate-questions",
                "--topic",
                "test",
                "--category",
                "invalid",
            ],
            expect_success=False,
        )

        assert response["error_code"] == "INVALID_INPUT"
        assert "Invalid category" in response["error"]


class TestExportMetrics:
    """Test export-metrics command."""

    def test_export_metrics_weekly(self):
        """Test weekly metrics export."""
        response = run_cli(
            [
                "interview-sim",
                "export-metrics",
                "--period",
                "weekly",
            ]
        )

        data = response["data"]
        assert data["period"] == "weekly"
        assert "sessions" in data
        assert "responses" in data
        assert "performance" in data
        assert "category_breakdown" in data

    def test_export_metrics_monthly(self):
        """Test monthly metrics export."""
        response = run_cli(
            [
                "interview-sim",
                "export-metrics",
                "--period",
                "monthly",
            ]
        )

        data = response["data"]
        assert data["period"] == "monthly"

    def test_export_metrics_invalid_period(self):
        """Test that invalid period returns error."""
        response = run_cli(
            [
                "interview-sim",
                "export-metrics",
                "--period",
                "invalid",
            ],
            expect_success=False,
        )

        assert response["error_code"] == "INVALID_INPUT"
        assert "Invalid period" in response["error"]

    def test_export_metrics_to_file(self, tmp_path):
        """Test exporting metrics to file."""
        output_file = tmp_path / "metrics.json"

        response = run_cli(
            [
                "interview-sim",
                "export-metrics",
                "--period",
                "weekly",
                "--output",
                str(output_file),
            ]
        )

        # Check file was created
        assert output_file.exists()

        # Check file contains valid JSON
        with open(output_file) as f:
            file_data = json.load(f)
            assert "period" in file_data
            assert file_data["period"] == "weekly"


class TestAnalyzeTranscript:
    """Test analyze-transcript command."""

    def test_analyze_transcript_file_not_found(self):
        """Test that missing file returns error."""
        response = run_cli(
            [
                "interview-sim",
                "analyze-transcript",
                "--file",
                "/nonexistent/file.txt",
            ],
            expect_success=False,
        )

        assert response["error_code"] == "NOT_FOUND"
        assert "not found" in response["error"].lower()

    def test_analyze_transcript_standalone(self, tmp_path):
        """Test analyzing standalone transcript (no session)."""
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("This is a sample interview transcript.")

        response = run_cli(
            [
                "interview-sim",
                "analyze-transcript",
                "--file",
                str(transcript_file),
            ]
        )

        data = response["data"]
        assert "word_count" in data
        assert data["word_count"] == 6  # "This is a sample interview transcript"


class TestBatchFeedback:
    """Test batch-feedback command."""

    def test_batch_feedback_file_not_found(self):
        """Test that missing file returns error."""
        response = run_cli(
            [
                "interview-sim",
                "batch-feedback",
                "--session-ids",
                "/nonexistent/sessions.txt",
            ],
            expect_success=False,
        )

        assert response["error_code"] == "NOT_FOUND"
        assert "not found" in response["error"].lower()

    def test_batch_feedback_empty_file(self, tmp_path):
        """Test that empty file returns error."""
        sessions_file = tmp_path / "sessions.txt"
        sessions_file.write_text("")

        response = run_cli(
            [
                "interview-sim",
                "batch-feedback",
                "--session-ids",
                str(sessions_file),
            ],
            expect_success=False,
        )

        assert response["error_code"] == "INVALID_INPUT"
        assert "No session IDs" in response["error"]

    def test_batch_feedback_invalid_uuids(self, tmp_path):
        """Test batch processing with invalid UUIDs."""
        sessions_file = tmp_path / "sessions.txt"
        sessions_file.write_text("invalid-uuid-1\ninvalid-uuid-2")

        response = run_cli(
            [
                "interview-sim",
                "batch-feedback",
                "--session-ids",
                str(sessions_file),
            ]
        )

        data = response["data"]
        assert data["total"] == 2
        assert data["failed"] == 2  # Both should fail (invalid UUID)
        assert len(data["results"]) == 2

        # Check that results contain error info
        for result in data["results"]:
            assert result["success"] is False
            assert "error" in result


class TestJSONOutputStructure:
    """Test that all commands follow standard JSON schema."""

    @pytest.mark.parametrize(
        "cmd",
        [
            ["interview-sim", "version"],
            ["interview-sim", "generate-questions", "--topic", "test", "--count", "1"],
            ["interview-sim", "export-metrics", "--period", "weekly"],
        ],
    )
    def test_standard_json_schema(self, cmd):
        """Test that commands follow standard JSON response schema."""
        response = run_cli(cmd)

        # Required top-level fields
        assert "success" in response
        assert "data" in response
        assert "error" in response
        assert "error_code" in response
        assert "timestamp" in response
        assert "duration_ms" in response
        assert "metadata" in response

        # Metadata fields
        metadata = response["metadata"]
        assert "command" in metadata
        assert "version" in metadata

        # Type checks
        assert isinstance(response["success"], bool)
        assert isinstance(response["timestamp"], str)
        assert isinstance(response["duration_ms"], (int, float))
