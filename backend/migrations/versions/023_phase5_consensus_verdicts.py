"""Phase 5: consensus_verdicts table for deterministic review-swarm verdicts.

Revision ID: 023
Revises: 022
Create Date: 2026-05-20

This migration lands the consensus verdict table for TASKS_GENERATION Phase 5.

  * `consensus_verdicts` — one row per review run, storing the deterministic
    consensus derived from all reviewer scores. Includes per-dimension averages,
    vote counts, disagreement metric, and the final consensus_verdict enum.

One new PG enum type:
  * `consensus_verdict_enum` (admin_review_ready, reject_recommended,
    regenerate_recommended, blocked_overlap, insufficient_reviews)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade():
    # Create PG enum type for consensus verdicts.
    with op.get_context().autocommit_block():
        op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'consensus_verdict_enum') THEN
                CREATE TYPE consensus_verdict_enum AS ENUM (
                    'admin_review_ready', 'reject_recommended',
                    'regenerate_recommended', 'blocked_overlap', 'insufficient_reviews'
                );
            END IF;
        END $$;
        """)

    op.create_table(
        "consensus_verdicts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column(
            "review_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("review_runs.id"),
            nullable=False,
        ),
        sa.Column(
            "generation_batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("generation_batches.id"),
            nullable=True,
        ),
        sa.Column("reviewer_count", sa.Integer, nullable=False),
        sa.Column("average_realism", sa.Float, nullable=True),
        sa.Column("average_sat_fidelity", sa.Float, nullable=True),
        sa.Column("average_difficulty_match", sa.Float, nullable=True),
        sa.Column("average_distractor_quality", sa.Float, nullable=True),
        sa.Column("average_taxonomy_match", sa.Float, nullable=True),
        sa.Column("max_copy_risk", sa.Float, nullable=True),
        sa.Column("accept_votes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("needs_review_votes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reject_votes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reviewer_disagreement", sa.Float, nullable=True),
        sa.Column("high_disagreement_flag", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "consensus_verdict",
            postgresql.ENUM(
                "admin_review_ready",
                "reject_recommended",
                "regenerate_recommended",
                "blocked_overlap",
                "insufficient_reviews",
                name="consensus_verdict_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("reasons_jsonb", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_consensus_verdicts_question_id", "consensus_verdicts", ["question_id"])
    op.create_index("ix_consensus_verdicts_review_run_id", "consensus_verdicts", ["review_run_id"])
    op.create_index("ix_consensus_verdicts_generation_batch_id", "consensus_verdicts", ["generation_batch_id"])
    op.create_index("ix_consensus_verdicts_consensus_verdict", "consensus_verdicts", ["consensus_verdict"])


def downgrade():
    op.drop_table("consensus_verdicts")

    with op.get_context().autocommit_block():
        op.execute("DROP TYPE IF EXISTS consensus_verdict_enum")
