"""Add diagnostic_sessions table and diagnostic_session_id FK on user_progress.

Revision ID: 030
Revises: 029
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=True, server_default=sa.func.now()),
        sa.Column("total_questions", sa.Integer(), nullable=False,
                  server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=False,
                  server_default="0"),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("question_ids", JSONB, nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("diagnostic_type", sa.String(20), nullable=True),
        sa.Column("focus_areas", JSONB, nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False,
                  server_default="false"),
    )
    op.create_index(
        "ix_diagnostic_sessions_user_id",
        "diagnostic_sessions",
        ["user_id"],
    )
    op.create_index(
        "ix_diagnostic_sessions_created_at",
        "diagnostic_sessions",
        ["created_at"],
    )

    op.add_column(
        "user_progress",
        sa.Column(
            "diagnostic_session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("diagnostic_sessions.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_user_progress_diagnostic_session_id",
        "user_progress",
        ["diagnostic_session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_progress_diagnostic_session_id",
        table_name="user_progress",
    )
    op.drop_column("user_progress", "diagnostic_session_id")

    op.drop_index("ix_diagnostic_sessions_created_at",
                  table_name="diagnostic_sessions")
    op.drop_index("ix_diagnostic_sessions_user_id",
                  table_name="diagnostic_sessions")
    op.drop_table("diagnostic_sessions")
