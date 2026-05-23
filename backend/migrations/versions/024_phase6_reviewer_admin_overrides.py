"""Phase 6: reviewer admin override audit table.

Revision ID: 024
Revises: 023
Create Date: 2026-05-20

This migration lands the append-only audit table used by the generated
question review dashboard. Approve/reject clicks write one row per reviewer
result in the latest completed review run, sharing a single admin_decision_id.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reviewer_admin_overrides",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("admin_decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column(
            "llm_review_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("llm_review_results.id"),
            nullable=False,
        ),
        sa.Column("reviewer_verdict", sa.String(length=40), nullable=False),
        sa.Column("admin_verdict", sa.String(length=40), nullable=False),
        sa.Column("override_direction", sa.String(length=40), nullable=False),
        sa.Column("admin_token", sa.String(length=128), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "admin_decision_id",
            "llm_review_result_id",
            name="uq_reviewer_admin_override_decision_result",
        ),
    )
    op.create_index(
        "ix_reviewer_admin_overrides_question_id",
        "reviewer_admin_overrides",
        ["question_id"],
    )
    op.create_index(
        "ix_reviewer_admin_overrides_llm_review_result_id",
        "reviewer_admin_overrides",
        ["llm_review_result_id"],
    )
    op.create_index(
        "ix_reviewer_admin_overrides_admin_decision_id",
        "reviewer_admin_overrides",
        ["admin_decision_id"],
    )
    op.create_index(
        "ix_reviewer_admin_overrides_override_direction",
        "reviewer_admin_overrides",
        ["override_direction"],
    )


def downgrade():
    op.drop_index(
        "ix_reviewer_admin_overrides_override_direction",
        table_name="reviewer_admin_overrides",
    )
    op.drop_index(
        "ix_reviewer_admin_overrides_admin_decision_id",
        table_name="reviewer_admin_overrides",
    )
    op.drop_index(
        "ix_reviewer_admin_overrides_llm_review_result_id",
        table_name="reviewer_admin_overrides",
    )
    op.drop_index(
        "ix_reviewer_admin_overrides_question_id",
        table_name="reviewer_admin_overrides",
    )
    op.drop_table("reviewer_admin_overrides")
