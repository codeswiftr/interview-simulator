"""Share service for managing interview share links."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.feedback import ContentFeedback, SessionFeedback
from app.models.interview import InterviewResponse, InterviewSession
from app.models.interview_share import InterviewShare, SharedInterviewRead
from app.models.question import Question
from app.models.user import User

logger = logging.getLogger(__name__)


class ShareService:
    """Service for managing interview share links."""

    async def create_share_link(
        self, session: AsyncSession, interview_id: UUID, user_id: UUID
    ) -> InterviewShare:
        """Create a share link for an interview.

        Args:
            session: Database session
            interview_id: UUID of the interview to share
            user_id: UUID of the user creating the share

        Returns:
            InterviewShare object with token

        Raises:
            ValueError: If interview not found or user doesn't own it
        """
        # Verify interview exists and belongs to user
        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        )
        interview = interview_result.first()

        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.user_id != user_id:
            raise ValueError("Cannot share interview: access denied")

        # Check for existing active share
        existing_result = await session.exec(
            select(InterviewShare)
            .where(InterviewShare.interview_id == interview_id)
            .where(InterviewShare.expires_at > datetime.now(UTC))
        )
        existing = existing_result.first()

        if existing:
            # Return existing share link
            return existing

        # Create new share
        share = InterviewShare(
            interview_id=interview_id,
            created_by=user_id,
        )
        session.add(share)
        await session.commit()
        await session.refresh(share)

        logger.info(f"Created share link for interview {interview_id}")
        return share

    async def get_shared_interview(
        self, session: AsyncSession, token: str
    ) -> SharedInterviewRead:
        """Get interview data via share token.

        Args:
            session: Database session
            token: Share token from URL

        Returns:
            SharedInterviewRead with interview data

        Raises:
            ValueError: If token invalid or expired
        """
        # Find share by token
        share_result = await session.exec(
            select(InterviewShare).where(InterviewShare.token == token)
        )
        share = share_result.first()

        if not share:
            raise ValueError("Share link not found")

        if share.is_expired:
            raise ValueError("Share link has expired")

        # Increment view count
        share.view_count += 1
        await session.commit()

        # Get interview data
        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == share.interview_id)
        )
        interview = interview_result.first()

        if not interview:
            raise ValueError("Interview not found")

        # Get user who created share (for display name)
        user_result = await session.exec(
            select(User).where(User.id == share.created_by)
        )
        user = user_result.first()

        # Get anonymous display name
        if user:
            if user.full_name:
                shared_by = user.full_name.split()[0]  # First name only
            else:
                shared_by = user.email.split("@")[0]  # Email prefix
        else:
            shared_by = "A user"

        # Get session feedback
        feedback_result = await session.exec(
            select(SessionFeedback).where(SessionFeedback.session_id == interview.id)
        )
        session_feedback = feedback_result.first()

        # Get responses with feedback
        responses_result = await session.exec(
            select(InterviewResponse)
            .where(InterviewResponse.session_id == interview.id)
            .order_by(InterviewResponse.created_at)
        )
        responses = list(responses_result.all())

        response_data = []
        for response in responses:
            question_result = await session.exec(
                select(Question).where(Question.id == response.question_id)
            )
            question = question_result.first()

            feedback_result = await session.exec(
                select(ContentFeedback).where(ContentFeedback.response_id == response.id)
            )
            content_feedback = feedback_result.first()

            response_data.append({
                "question": question.content if question else "",
                "category": question.category.value if question else "",
                "difficulty": question.difficulty.value if question else "",
                "transcript": response.transcript or "",
                "duration_seconds": response.duration_seconds,
                "score": content_feedback.overall_content_score if content_feedback else 0,
                "strengths": content_feedback.strengths[:3] if content_feedback else [],
                "improvements": content_feedback.improvements[:3] if content_feedback else [],
            })

        return SharedInterviewRead(
            interview_type=interview.interview_type.value,
            overall_score=session_feedback.overall_score if session_feedback else None,
            audio_score=session_feedback.audio_score if session_feedback else None,
            content_score=session_feedback.content_score if session_feedback else None,
            question_count=len(responses),
            created_at=interview.created_at,
            shared_by=shared_by,
            responses=response_data,
        )

    async def revoke_share_link(
        self, session: AsyncSession, share_id: UUID, user_id: UUID
    ) -> bool:
        """Revoke (delete) a share link.

        Args:
            session: Database session
            share_id: UUID of the share to revoke
            user_id: UUID of the user revoking

        Returns:
            True if revoked successfully

        Raises:
            ValueError: If share not found or user doesn't own it
        """
        share_result = await session.exec(
            select(InterviewShare).where(InterviewShare.id == share_id)
        )
        share = share_result.first()

        if not share:
            raise ValueError(f"Share {share_id} not found")

        if share.created_by != user_id:
            raise ValueError("Cannot revoke share: access denied")

        await session.delete(share)
        await session.commit()

        logger.info(f"Revoked share link {share_id}")
        return True

    async def get_shares_for_interview(
        self, session: AsyncSession, interview_id: UUID, user_id: UUID
    ) -> list[InterviewShare]:
        """Get all share links for an interview.

        Args:
            session: Database session
            interview_id: UUID of the interview
            user_id: UUID of the requesting user

        Returns:
            List of InterviewShare objects
        """
        # Verify user owns the interview
        interview_result = await session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        )
        interview = interview_result.first()

        if not interview or interview.user_id != user_id:
            return []

        shares_result = await session.exec(
            select(InterviewShare)
            .where(InterviewShare.interview_id == interview_id)
            .order_by(InterviewShare.created_at.desc())
        )
        return list(shares_result.all())
