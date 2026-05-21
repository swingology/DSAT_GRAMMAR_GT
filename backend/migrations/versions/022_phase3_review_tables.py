"""Phase 3: review_runs and llm_review_results tables for the review swarm.

Revision ID: 022
Revises: 021
Create Date: 2026-05-20

This migration lands the review rubric storage and per-reviewer result
tracking for TASKS_GENERATION Phase 3:

  * `review_runs` — one row per review pass against a question. All reviewer
    rows from that pass plus the resulting consensus row share a single
    review_run_id.
  * `llm_review_results` — one row per reviewer model per run. Stores
    structured scores, verdict, latency, and raw response.

Four new PG enum types:
  * `review_run_status_enum` (running, complete, partial, failed)
  * `review_status_enum` (ok, transient_failed, permanent_failed)
  * `triggered_by_enum` (auto_on_save, manual_question, manual_batch,
    recalibration, rubric_bump)
  * `verdict_enum` (accept, needs_human_review, reject)

`ALTER TYPE ... ADD VALUE` runs in autocommit blocks so the new values
are visible to subsequent statements in the same migration.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade():
    # Create PG enum types before any column uses them. Use explicit
    # existence checks because PostgreSQL has no CREATE TYPE IF NOT EXISTS.
    with op.get_context().autocommit_block():
        op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_run_status_enum') THEN
                CREATE TYPE review_run_status_enum AS ENUM ('running', 'complete', 'partial', 'failed');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_status_enum') THEN
                CREATE TYPE review_status_enum AS ENUM ('ok', 'transient_failed', 'permanent_failed');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'triggered_by_enum') THEN
                CREATE TYPE triggered_by_enum AS ENUM (
                    'auto_on_save', 'manual_question', 'manual_batch',
                    'recalibration', 'rubric_bump'
                );
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'verdict_enum') THEN
                CREATE TYPE verdict_enum AS ENUM ('accept', 'needs_human_review', 'reject');
            END IF;
        END $$;
        """)

    # --- review_runs ---
    op.create_table(
        "review_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("question_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("generation_batch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_batches.id"), nullable=True),
        sa.Column("triggered_by", postgresql.ENUM(
            "auto_on_save", "manual_question", "manual_batch",
            "recalibration", "rubric_bump",
            name="triggered_by_enum", create_type=False), nullable=False),
        sa.Column("triggered_by_admin_token", sa.String(length=128), nullable=True),
        sa.Column("rubric_version", sa.String(length=20), nullable=False),
        sa.Column("rules_versions_jsonb", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", postgresql.ENUM(
            "running", "complete", "partial", "failed",
            name="review_run_status_enum", create_type=False), nullable=False,
            server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_review_runs_question_id", "review_runs", ["question_id"])
    op.create_index("ix_review_runs_status", "review_runs", ["status"])
    op.create_index("ix_review_runs_generation_batch_id",
                    "review_runs", ["generation_batch_id"])

    # --- llm_review_results ---
    op.create_table(
        "llm_review_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("question_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("question_jobs.id"), nullable=True),
        sa.Column("generation_batch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_batches.id"), nullable=True),
        sa.Column("review_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("review_runs.id"), nullable=False),
        sa.Column("provider_name", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("task_type", sa.String(length=20), nullable=False,
                  server_default="generation_realism_review"),
        sa.Column("rubric_version", sa.String(length=20), nullable=False),
        sa.Column("rules_versions_jsonb", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("scores_jsonb", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("verdict", postgresql.ENUM(
            "accept", "needs_human_review", "reject",
            name="verdict_enum", create_type=False), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("raw_response_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_usage_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("review_status", postgresql.ENUM(
            "ok", "transient_failed", "permanent_failed",
            name="review_status_enum", create_type=False), nullable=False,
            server_default="ok"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )
    op.create_index("ix_llm_review_results_question_id",
                    "llm_review_results", ["question_id"])
    op.create_index("ix_llm_review_results_review_run_id",
                    "llm_review_results", ["review_run_id"])
    op.create_index("ix_llm_review_results_provider_model",
                    "llm_review_results", ["provider_name", "model_name"])


def downgrade():
    # Drop tables in reverse FK dependency order.
    op.drop_index("ix_llm_review_results_provider_model",
                  table_name="llm_review_results")
    op.drop_index("ix_llm_review_results_review_run_id",
                  table_name="llm_review_results")
    op.drop_index("ix_llm_review_results_question_id",
                  table_name="llm_review_results")
    op.drop_table("llm_review_results")

    op.drop_index("ix_review_runs_generation_batch_id",
                  table_name="review_runs")
    op.drop_index("ix_review_runs_status", table_name="review_runs")
    op.drop_index("ix_review_runs_question_id", table_name="review_runs")
    op.drop_table("review_runs")

    # PG enum types cannot be dropped cleanly if any values are in use.
    # In a clean dev environment these can be dropped; in production,
    # ensure no rows reference these enum values before downgrade.
    op.execute("DROP TYPE IF EXISTS verdict_enum")
    op.execute("DROP TYPE IF EXISTS triggered_by_enum")
    op.execute("DROP TYPE IF EXISTS review_status_enum")
    op.execute("DROP TYPE IF EXISTS review_run_status_enum")
