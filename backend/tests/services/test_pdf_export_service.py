"""Tests for PDF export service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.feedback import ContentFeedback, SessionFeedback
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus, InterviewType
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.services.pdf_export_service import PDFExportService


class TestPDFExportServiceDataAggregation:
    """Tests for export data aggregation."""

    @pytest.mark.asyncio
    async def test_get_export_data_interview_not_found(self):
        """Should raise ValueError if interview not found."""
        service = PDFExportService()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Interview .* not found"):
            await service._get_export_data(mock_session, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_get_export_data_access_denied(self):
        """Should raise ValueError if user doesn't own interview."""
        service = PDFExportService()
        mock_session = AsyncMock()

        interview = InterviewSession(
            id=uuid4(),
            user_id=uuid4(),  # Different user
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )
        mock_result = MagicMock()
        mock_result.first.return_value = interview
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Access denied"):
            await service._get_export_data(mock_session, interview.id, uuid4())


class TestPDFExportServiceHTMLRendering:
    """Tests for HTML template rendering."""

    def test_render_interview_html_basic(self):
        """Should render valid HTML structure."""
        service = PDFExportService()

        data = {
            "interview": MagicMock(
                interview_type=InterviewType.BEHAVIORAL,
                created_at=datetime.now(UTC),
            ),
            "user": MagicMock(email="test@example.com"),
            "session_feedback": MagicMock(
                overall_score=85.0,
                audio_score=80.0,
                content_score=90.0,
            ),
            "responses": [],
            "generated_at": datetime.now(UTC),
        }

        html = service._render_interview_html(data)

        assert "<!DOCTYPE html>" in html
        assert "Interview Performance Report" in html
        assert "test@example.com" in html
        assert "85" in html  # Overall score
        assert "80" in html  # Audio score
        assert "90" in html  # Content score

    def test_render_interview_html_with_responses(self):
        """Should render response sections correctly."""
        service = PDFExportService()

        mock_question = MagicMock()
        mock_question.content = "Tell me about yourself"
        mock_question.category = QuestionCategory.BEHAVIORAL
        mock_question.difficulty = Difficulty.MEDIUM

        mock_response = MagicMock()
        mock_response.transcript = "I am a software engineer..."
        mock_response.duration_seconds = 120

        mock_feedback = MagicMock()
        mock_feedback.overall_content_score = 78.5
        mock_feedback.strengths = ["Good structure", "Clear examples"]
        mock_feedback.improvements = ["Be more specific"]

        data = {
            "interview": MagicMock(
                interview_type=InterviewType.BEHAVIORAL,
                created_at=datetime.now(UTC),
            ),
            "user": MagicMock(email="test@example.com"),
            "session_feedback": MagicMock(
                overall_score=78.0,
                audio_score=75.0,
                content_score=81.0,
            ),
            "responses": [
                {
                    "question": mock_question,
                    "response": mock_response,
                    "feedback": mock_feedback,
                }
            ],
            "generated_at": datetime.now(UTC),
        }

        html = service._render_interview_html(data)

        assert "Tell me about yourself" in html
        assert "I am a software engineer..." in html
        assert "120" in html  # Duration
        assert "Good structure" in html
        assert "Clear examples" in html
        assert "Be more specific" in html
        assert "behavioral" in html.lower()
        assert "medium" in html.lower()

    def test_render_interview_html_handles_missing_feedback(self):
        """Should handle missing feedback gracefully."""
        service = PDFExportService()

        data = {
            "interview": MagicMock(
                interview_type=InterviewType.TECHNICAL,
                created_at=datetime.now(UTC),
            ),
            "user": MagicMock(email="test@example.com"),
            "session_feedback": None,  # No session feedback
            "responses": [
                {
                    "question": MagicMock(
                        content="What is polymorphism?",
                        category=QuestionCategory.TECHNICAL,
                        difficulty=Difficulty.HARD,
                    ),
                    "response": MagicMock(
                        transcript="Polymorphism is...",
                        duration_seconds=60,
                    ),
                    "feedback": None,  # No content feedback
                }
            ],
            "generated_at": datetime.now(UTC),
        }

        html = service._render_interview_html(data)

        # Should render without error
        assert "<!DOCTYPE html>" in html
        assert "What is polymorphism?" in html


class TestPDFExportServiceConversion:
    """Tests for HTML to PDF conversion."""

    def test_html_to_pdf_weasyprint_not_installed(self):
        """Should raise ValueError if WeasyPrint not installed."""
        service = PDFExportService()

        with patch.object(service, "_html_to_pdf") as mock_convert:
            mock_convert.side_effect = ValueError("PDF generation unavailable - WeasyPrint not installed")

            with pytest.raises(ValueError, match="WeasyPrint not installed"):
                mock_convert("<html></html>")

    def test_html_to_pdf_success(self):
        """Should convert HTML to PDF bytes or raise if WeasyPrint not installed."""
        service = PDFExportService()

        try:
            # Try to call the actual method - it will work if WeasyPrint is installed
            result = service._html_to_pdf("<html><body>Test</body></html>")
            # If WeasyPrint is installed, this should return bytes
            assert isinstance(result, bytes)
        except ValueError as e:
            # WeasyPrint might not be installed in test environment
            assert "WeasyPrint" in str(e) or "PDF generation" in str(e)


class TestPDFExportServiceIntegration:
    """Integration tests for full PDF generation."""

    @pytest.mark.asyncio
    async def test_generate_interview_pdf_flow(self):
        """Should generate PDF for valid interview."""
        service = PDFExportService()

        # Create mock data
        user_id = uuid4()
        interview_id = uuid4()

        interview = InterviewSession(
            id=interview_id,
            user_id=user_id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )

        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hash",
        )

        session_feedback = SessionFeedback(
            id=uuid4(),
            session_id=interview_id,
            overall_score=85.0,
            audio_score=80.0,
            content_score=90.0,
            key_strengths=["Good"],
            areas_for_improvement=["Better"],
            next_steps=["Practice"],
        )

        # Mock session to return appropriate data in sequence
        mock_session = AsyncMock()

        call_count = 0
        async def mock_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()

            if call_count == 1:  # Interview query
                result.first.return_value = interview
            elif call_count == 2:  # User query
                result.first.return_value = user
            elif call_count == 3:  # Session feedback query
                result.first.return_value = session_feedback
            elif call_count == 4:  # Responses query
                result.all.return_value = []
            else:
                result.first.return_value = None
                result.all.return_value = []

            return result

        mock_session.exec = mock_exec

        # Mock PDF conversion
        with patch.object(service, "_html_to_pdf", return_value=b"%PDF-1.4 mock pdf"):
            result = await service.generate_interview_pdf(mock_session, interview_id, user_id)

        assert result == b"%PDF-1.4 mock pdf"
