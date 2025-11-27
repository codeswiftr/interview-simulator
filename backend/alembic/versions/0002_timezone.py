"""Make timestamp columns timezone-aware."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_timezone"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tz = sa.DateTime(timezone=True)
    tables_columns = {
        "users": ["subscription_expires_at", "created_at", "updated_at", "last_login_at"],
        "questions": ["created_at", "updated_at"],
        "interview_sessions": ["scheduled_at", "started_at", "ended_at", "created_at", "updated_at"],
        "interview_questions": ["asked_at"],
        "interview_responses": ["created_at"],
        "audio_feedback": ["created_at"],
        "content_feedback": ["created_at"],
        "session_feedback": ["created_at"],
    }
    for table, columns in tables_columns.items():
        for col in columns:
            op.alter_column(
                table,
                col,
                type_=tz,
                postgresql_using=f"{col} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    tz_naive = sa.DateTime(timezone=False)
    tables_columns = {
        "users": ["subscription_expires_at", "created_at", "updated_at", "last_login_at"],
        "questions": ["created_at", "updated_at"],
        "interview_sessions": ["scheduled_at", "started_at", "ended_at", "created_at", "updated_at"],
        "interview_questions": ["asked_at"],
        "interview_responses": ["created_at"],
        "audio_feedback": ["created_at"],
        "content_feedback": ["created_at"],
        "session_feedback": ["created_at"],
    }
    for table, columns in tables_columns.items():
        for col in columns:
            op.alter_column(
                table,
                col,
                type_=tz_naive,
                postgresql_using=f"{col}",
            )
