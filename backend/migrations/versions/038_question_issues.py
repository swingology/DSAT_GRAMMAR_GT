"""Add question_issues — problems flagged on a question by admins or students.

A flag never changes the question; it stays live until an admin resolves the
issue as approved (no change needed), edited, or rejected.

Revision ID: 038
Revises: 037
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_issues",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_type", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("reported_by_role", sa.String(length=10), nullable=False),
        sa.Column("reporter_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reported_by_admin_token", sa.String(length=128), nullable=True),
        sa.Column("resolution", sa.String(length=20), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_by_admin_token", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_question_issues_question_status", "question_issues", ["question_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_question_issues_question_status", table_name="question_issues")
    op.drop_table("question_issues")
