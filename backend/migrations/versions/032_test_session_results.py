"""Add test_session_results table for adaptive module 2 routing.

Revision ID: 032
Revises: 031
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = "032"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "test_session_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_1_results", JSONB, nullable=False),
        sa.Column("module_1_accuracy", sa.Float, nullable=False),
        sa.Column("module_1_duration_seconds", sa.Integer, nullable=True),
        sa.Column("module_2_difficulty", sa.String(20), nullable=False),
        sa.Column("routing_rationale", sa.Text, nullable=True),
        sa.Column("module_2_results", JSONB, nullable=True),
        sa.Column("estimated_score", sa.Integer, nullable=True),
        sa.Column("test_mode", sa.String(20), nullable=False, server_default="practice"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_test_session_results_user_id", "test_session_results", ["user_id"])
    op.create_index("ix_test_session_results_created_at", "test_session_results", ["created_at"])


def downgrade():
    op.drop_table("test_session_results")
