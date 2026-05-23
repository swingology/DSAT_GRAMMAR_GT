"""Phase 10: auto_release_audit_logs table for controlled auto-release audit trail.

Revision ID: 026
Revises: 025
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auto_release_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id",
            UUID(as_uuid=True),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column(
            "generation_batch_id",
            UUID(as_uuid=True),
            sa.ForeignKey("generation_batches.id"),
            nullable=True,
        ),
        sa.Column(
            "review_run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("review_runs.id"),
            nullable=True,
        ),
        sa.Column(
            "consensus_verdict_id",
            UUID(as_uuid=True),
            sa.ForeignKey("consensus_verdicts.id"),
            nullable=True,
        ),
        sa.Column("generator_provider_name", sa.String(50), nullable=True),
        sa.Column("generator_model_name", sa.String(100), nullable=True),
        sa.Column("generator_accept_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("generator_total_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("generator_accept_rate", sa.Float, nullable=True),
        sa.Column("release_policy", sa.String(40), nullable=True),
        sa.Column("reasons_jsonb", JSONB, nullable=True),
        sa.Column(
            "released_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_auto_release_audit_question_id",
        "auto_release_audit_logs",
        ["question_id"],
    )
    op.create_index(
        "ix_auto_release_audit_released_at",
        "auto_release_audit_logs",
        ["released_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_auto_release_audit_released_at", table_name="auto_release_audit_logs")
    op.drop_index("ix_auto_release_audit_question_id", table_name="auto_release_audit_logs")
    op.drop_table("auto_release_audit_logs")
