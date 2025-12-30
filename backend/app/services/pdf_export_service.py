"""PDF export service for interview results.

Generates professional PDF reports from interview sessions with feedback.
"""

import logging
from datetime import datetime
from io import BytesIO
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.feedback import ContentFeedback, SessionFeedback
from app.models.interview import InterviewResponse, InterviewSession
from app.models.question import Question
from app.models.user import User

logger = logging.getLogger(__name__)


class PDFExportService:
    """Service for generating PDF exports of interview sessions."""

    async def generate_interview_pdf(
        self, session: AsyncSession, interview_id: UUID, user_id: UUID
    ) -> bytes:
        """Generate a PDF report for an interview session.

        Args:
            session: Database session
            interview_id: UUID of the interview session
            user_id: UUID of the requesting user (for permission check)

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If interview not found or user doesn't have access
        """
        # Get export data
        data = await self._get_export_data(session, interview_id, user_id)

        # Render HTML template
        html_content = self._render_interview_html(data)

        # Convert to PDF
        pdf_bytes = self._html_to_pdf(html_content)

        return pdf_bytes

    async def _get_export_data(
        self, session: AsyncSession, interview_id: UUID, user_id: UUID
    ) -> dict:
        """Aggregate interview data for export.

        Returns dict with interview, user, responses, and feedback data.
        """
        # Get interview session
        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        )
        interview = interview_result.first()

        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.user_id != user_id:
            raise ValueError("Access denied: interview belongs to another user")

        # Get user info
        user_result = await session.exec(
            select(User).where(User.id == interview.user_id)
        )
        user = user_result.first()

        # Get session feedback
        feedback_result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == interview_id)
        )
        session_feedback = feedback_result.first()

        # Get responses with questions and feedback
        responses_result = await session.exec(
            select(InterviewResponse)
            .where(InterviewResponse.session_id == interview_id)
            .order_by(InterviewResponse.created_at)
        )
        responses = list(responses_result.all())

        # Build response data with questions and feedback
        response_data = []
        for response in responses:
            question_result = await session.exec(
                select(Question).where(Question.id == response.question_id)
            )
            question = question_result.first()

            content_feedback_result = await session.exec(
                select(ContentFeedback).where(ContentFeedback.response_id == response.id)
            )
            content_feedback = content_feedback_result.first()

            response_data.append({
                "question": question,
                "response": response,
                "feedback": content_feedback,
            })

        return {
            "interview": interview,
            "user": user,
            "session_feedback": session_feedback,
            "responses": response_data,
            "generated_at": datetime.utcnow(),
        }

    def _render_interview_html(self, data: dict) -> str:
        """Render interview data as HTML for PDF conversion."""
        interview = data["interview"]
        user = data["user"]
        session_feedback = data["session_feedback"]
        responses = data["responses"]
        generated_at = data["generated_at"]

        # Calculate scores
        overall_score = session_feedback.overall_score if session_feedback else 0
        audio_score = session_feedback.audio_score if session_feedback else 0
        content_score = session_feedback.content_score if session_feedback else 0

        # Build response sections
        response_sections = ""
        for i, resp_data in enumerate(responses, 1):
            question = resp_data["question"]
            response = resp_data["response"]
            feedback = resp_data["feedback"]

            q_content = question.content if question else "Question not found"
            q_category = question.category.value if question else "Unknown"
            q_difficulty = question.difficulty.value if question else "Unknown"

            transcript = response.transcript or "No transcript available"
            duration = response.duration_seconds or 0

            fb_score = feedback.overall_content_score if feedback else 0
            fb_strengths = feedback.strengths if feedback else []
            fb_improvements = feedback.improvements if feedback else []

            strengths_html = "".join(f"<li>{s}</li>" for s in fb_strengths[:3])
            improvements_html = "".join(f"<li>{s}</li>" for s in fb_improvements[:3])

            response_sections += f"""
            <div class="response-section">
                <div class="question-header">
                    <h3>Question {i}</h3>
                    <span class="badge category">{q_category}</span>
                    <span class="badge difficulty">{q_difficulty}</span>
                </div>
                <p class="question-text">{q_content}</p>

                <div class="answer-section">
                    <h4>Your Answer ({duration}s)</h4>
                    <p class="transcript">{transcript}</p>
                </div>

                <div class="feedback-section">
                    <div class="score-badge">Score: {fb_score:.0f}/100</div>
                    <div class="feedback-columns">
                        <div class="strengths">
                            <h5>Strengths</h5>
                            <ul>{strengths_html or '<li>No strengths recorded</li>'}</ul>
                        </div>
                        <div class="improvements">
                            <h5>Areas to Improve</h5>
                            <ul>{improvements_html or '<li>No improvements recorded</li>'}</ul>
                        </div>
                    </div>
                </div>
            </div>
            """

        # Build full HTML document
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Interview Report - {user.email if user else 'User'}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 11pt;
                    line-height: 1.5;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #2563eb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2563eb;
                    margin: 0 0 10px 0;
                }}
                .header .subtitle {{
                    color: #666;
                    font-size: 12pt;
                }}
                .summary-box {{
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 30px;
                }}
                .summary-box h2 {{
                    margin: 0 0 15px 0;
                    color: #1e40af;
                }}
                .scores {{
                    display: flex;
                    justify-content: space-around;
                    text-align: center;
                }}
                .score-item {{
                    padding: 10px 20px;
                }}
                .score-value {{
                    font-size: 24pt;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .score-label {{
                    font-size: 10pt;
                    color: #666;
                }}
                .response-section {{
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    page-break-inside: avoid;
                }}
                .question-header {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 10px;
                }}
                .question-header h3 {{
                    margin: 0;
                    color: #1e40af;
                }}
                .badge {{
                    font-size: 9pt;
                    padding: 2px 8px;
                    border-radius: 4px;
                    text-transform: uppercase;
                }}
                .badge.category {{
                    background: #dbeafe;
                    color: #1e40af;
                }}
                .badge.difficulty {{
                    background: #fef3c7;
                    color: #92400e;
                }}
                .question-text {{
                    font-style: italic;
                    color: #555;
                    margin-bottom: 15px;
                }}
                .answer-section h4 {{
                    color: #374151;
                    margin: 0 0 10px 0;
                }}
                .transcript {{
                    background: #f9fafb;
                    padding: 15px;
                    border-radius: 4px;
                    font-size: 10pt;
                }}
                .feedback-section {{
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px solid #e5e7eb;
                }}
                .score-badge {{
                    display: inline-block;
                    background: #2563eb;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .feedback-columns {{
                    display: flex;
                    gap: 20px;
                }}
                .feedback-columns > div {{
                    flex: 1;
                }}
                .feedback-columns h5 {{
                    margin: 0 0 5px 0;
                    color: #374151;
                }}
                .strengths ul {{
                    color: #059669;
                }}
                .improvements ul {{
                    color: #dc2626;
                }}
                ul {{
                    margin: 0;
                    padding-left: 20px;
                }}
                li {{
                    margin-bottom: 3px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 9pt;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Interview Performance Report</h1>
                <p class="subtitle">
                    {interview.interview_type.value.replace('_', ' ').title()} Interview
                    | {interview.created_at.strftime('%B %d, %Y') if interview.created_at else 'Date unknown'}
                </p>
            </div>

            <div class="summary-box">
                <h2>Overall Performance</h2>
                <div class="scores">
                    <div class="score-item">
                        <div class="score-value">{overall_score:.0f}</div>
                        <div class="score-label">Overall Score</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">{content_score:.0f}</div>
                        <div class="score-label">Content</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">{audio_score:.0f}</div>
                        <div class="score-label">Delivery</div>
                    </div>
                </div>
            </div>

            <h2>Question Responses</h2>
            {response_sections}

            <div class="footer">
                <p>Generated by CareerSwiftr Interview Simulator on {generated_at.strftime('%B %d, %Y at %H:%M UTC')}</p>
                <p>app.codeswiftr.com</p>
            </div>
        </body>
        </html>
        """

        return html

    def _html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML content to PDF bytes using WeasyPrint."""
        try:
            from weasyprint import HTML

            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            return pdf_buffer.read()
        except ImportError:
            logger.error("WeasyPrint not installed. Install with: pip install weasyprint")
            raise ValueError("PDF generation unavailable - WeasyPrint not installed")
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise ValueError(f"PDF generation failed: {str(e)}")
