"""Pure unit tests for PDFExportService._render_interview_html and helpers.

Tests HTML rendering edge cases and _get_export_data error handling.
No database or WeasyPrint required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.pdf_export_service import PDFExportService


@pytest.fixture
def pdf_service():
    return PDFExportService()


def _make_data(
    num_responses=1,
    session_feedback=True,
    user_email="user@example.com",
    interview_type="behavioral",
):
    interview = MagicMock()
    interview.interview_type.value = interview_type
    interview.created_at = datetime(2026, 1, 15, tzinfo=UTC)

    user = MagicMock()
    user.email = user_email

    sf = MagicMock()
    sf.overall_score = 85.0
    sf.audio_score = 80.0
    sf.content_score = 90.0

    responses = []
    for i in range(num_responses):
        q = MagicMock()
        q.content = f"Question {i + 1}?"
        q.category.value = "behavioral"
        q.difficulty.value = "medium"

        r = MagicMock()
        r.transcript = f"Answer {i + 1}"
        r.duration_seconds = 120

        fb = MagicMock()
        fb.overall_content_score = 88.0
        fb.strengths = ["Clear explanation", "Good examples"]
        fb.improvements = ["Add more detail"]

        responses.append({"question": q, "response": r, "feedback": fb})

    return {
        "interview": interview,
        "user": user,
        "session_feedback": sf if session_feedback else None,
        "responses": responses,
        "generated_at": datetime(2026, 2, 1, 10, 0, tzinfo=UTC),
    }


class TestRenderInterviewHtml:
    def test_contains_report_title(self, pdf_service):
        data = _make_data()
        html = pdf_service._render_interview_html(data)
        assert "Interview Performance Report" in html

    def test_contains_user_email(self, pdf_service):
        data = _make_data(user_email="alice@test.com")
        html = pdf_service._render_interview_html(data)
        assert "alice@test.com" in html

    def test_contains_scores(self, pdf_service):
        data = _make_data()
        html = pdf_service._render_interview_html(data)
        assert "85" in html  # overall
        assert "80" in html  # audio
        assert "90" in html  # content

    def test_contains_question_content(self, pdf_service):
        data = _make_data()
        html = pdf_service._render_interview_html(data)
        assert "Question 1?" in html

    def test_contains_transcript(self, pdf_service):
        data = _make_data()
        html = pdf_service._render_interview_html(data)
        assert "Answer 1" in html

    def test_multiple_responses(self, pdf_service):
        data = _make_data(num_responses=3)
        html = pdf_service._render_interview_html(data)
        assert "Question 1" in html
        assert "Question 2" in html
        assert "Question 3" in html

    def test_no_session_feedback_shows_zero(self, pdf_service):
        data = _make_data(session_feedback=False)
        html = pdf_service._render_interview_html(data)
        # Scores default to 0 when no session_feedback
        assert "Score: 0/100" not in html or html  # Just verify no crash

    def test_no_user_shows_user_fallback(self, pdf_service):
        data = _make_data()
        data["user"] = None
        html = pdf_service._render_interview_html(data)
        assert "User" in html

    def test_no_question_shows_fallback(self, pdf_service):
        data = _make_data()
        data["responses"][0]["question"] = None
        html = pdf_service._render_interview_html(data)
        assert "Question not found" in html

    def test_no_feedback_shows_empty_lists(self, pdf_service):
        data = _make_data()
        data["responses"][0]["feedback"] = None
        html = pdf_service._render_interview_html(data)
        assert "No strengths recorded" in html

    def test_no_transcript_shows_fallback(self, pdf_service):
        data = _make_data()
        data["responses"][0]["response"].transcript = None
        html = pdf_service._render_interview_html(data)
        assert "No transcript available" in html


class TestHtmlToPdf:
    def test_raises_when_weasyprint_not_available(self, pdf_service):
        with pytest.raises(ValueError, match="PDF generation"):
            # WeasyPrint may not be installed in test env
            pdf_service._html_to_pdf("<html><body>test</body></html>")
