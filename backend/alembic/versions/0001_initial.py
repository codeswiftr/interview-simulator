"""Initial database schema."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("subscription_tier", sa.String(), nullable=False, server_default="free"),
        sa.Column("subscription_status", sa.String(), nullable=True),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column("interviews_this_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_interviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()
        ),
        sa.Column(
            "is_verified", sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"])

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column(
            "company_tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        sa.Column("topic_tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("expected_duration_seconds", sa.Integer(), nullable=False, server_default="180"),
        sa.Column("sample_answer", sa.String(), nullable=True),
        sa.Column(
            "evaluation_criteria",
            postgresql.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_questions_category", "questions", ["category"])
    op.create_index("ix_questions_difficulty", "questions", ["difficulty"])

    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("interview_type", sa.String(), nullable=False),
        sa.Column("company_style", sa.String(), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("status", sa.String(), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("audio_score", sa.Float(), nullable=True),
        sa.Column("content_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("asked_at", sa.DateTime(), nullable=True),
        sa.Column("time_limit_seconds", sa.Integer(), nullable=False, server_default="180"),
    )
    op.create_index("ix_interview_questions_session_id", "interview_questions", ["session_id"])
    op.create_index("ix_interview_questions_question_id", "interview_questions", ["question_id"])

    op.create_table(
        "interview_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("video_url", sa.String(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("transcript_with_timestamps", postgresql.JSON(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("filler_word_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interview_responses_session_id", "interview_responses", ["session_id"])
    op.create_index("ix_interview_responses_question_id", "interview_responses", ["question_id"])

    op.create_table(
        "audio_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "response_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_responses.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("speech_rate_wpm", sa.Float(), nullable=False),
        sa.Column("speech_rate_score", sa.Float(), nullable=False),
        sa.Column(
            "filler_words", postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")
        ),
        sa.Column("filler_word_score", sa.Float(), nullable=False),
        sa.Column("volume_consistency", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("overall_audio_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "content_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "response_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_responses.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("technical_accuracy", sa.Float(), nullable=False),
        sa.Column("star_adherence", sa.Float(), nullable=False),
        sa.Column("answer_structure", sa.Float(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("relevance", sa.Float(), nullable=False),
        sa.Column("overall_content_score", sa.Float(), nullable=False),
        sa.Column("strengths", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column(
            "improvements", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        sa.Column("detailed_feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "session_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_sessions.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("audio_score", sa.Float(), nullable=False),
        sa.Column("content_score", sa.Float(), nullable=False),
        sa.Column(
            "top_strengths", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "top_improvements", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "recommended_practice_areas",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "next_question_ids", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("session_feedback")
    op.drop_table("content_feedback")
    op.drop_table("audio_feedback")
    op.drop_index("ix_interview_responses_question_id", table_name="interview_responses")
    op.drop_index("ix_interview_responses_session_id", table_name="interview_responses")
    op.drop_table("interview_responses")
    op.drop_index("ix_interview_questions_question_id", table_name="interview_questions")
    op.drop_index("ix_interview_questions_session_id", table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_index("ix_questions_difficulty", table_name="questions")
    op.drop_index("ix_questions_category", table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
