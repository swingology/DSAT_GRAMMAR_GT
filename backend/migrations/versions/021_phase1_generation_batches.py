"""Phase 1: generation batches, idempotency keys, job batch linkage.

Revision ID: 021
Revises: 020
Create Date: 2026-05-20

This migration lands the structural pieces of TASKS_GENERATION Phase 1:

  * `generation_batches` — one row per batch request, with denormalized
    counters for the admin dashboard.
  * `generation_batch_idempotency_keys` — separate table holding the
    `Idempotency-Key` -> `batch_id` mapping with a 24h TTL. Expired rows
    are deleted before lookup/create so the same key can be reused after
    the TTL.
  * `question_jobs` gains:
      - `generation_batch_id` (FK to generation_batches, nullable so
        legacy/non-batch jobs keep working)
      - `generation_request_jsonb` (durable per-job request snapshot so
        retries don't depend on a saved Question row)
      - `retry_count`, `last_retry_at`
  * `questions.is_canonical_source` boolean for the source-example
    fallback pool (Q9 in the locked decisions).
  * `job_status_enum` gains `failed_transient`, `failed_permanent`,
    `retrying`.

`ALTER TYPE ... ADD VALUE` runs in an autocommit block so the new values
are visible to subsequent statements in the same migration.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade():
    # Extend the job status enum with the three new transient/permanent/retry
    # states before any column writes them.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE job_status_enum ADD VALUE IF NOT EXISTS 'failed_transient'")
        op.execute("ALTER TYPE job_status_enum ADD VALUE IF NOT EXISTS 'failed_permanent'")
        op.execute("ALTER TYPE job_status_enum ADD VALUE IF NOT EXISTS 'retrying'")

    # --- generation_batches ---
    op.create_table(
        "generation_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("request_jsonb", postgresql.JSONB(), nullable=False),
        sa.Column("requested_by", sa.String(length=32), nullable=False),
        sa.Column("student_id", sa.Integer(),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("requested_by_user_token", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("release_policy", sa.String(length=40), nullable=False,
                  server_default="admin_review_required"),
        sa.Column("regenerate_source_batch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_batches.id"), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False,
                  server_default="pending"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("needs_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )
    op.create_index("ix_generation_batches_status", "generation_batches", ["status"])
    op.create_index("ix_generation_batches_student_id", "generation_batches", ["student_id"])
    op.create_index("ix_generation_batches_requested_by_user_token",
                    "generation_batches", ["requested_by_user_token"])
    op.create_index("ix_generation_batches_requested_by_created_at",
                    "generation_batches", ["requested_by", "created_at"])

    # --- generation_batch_idempotency_keys ---
    op.create_table(
        "generation_batch_idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=32), nullable=False),
        sa.Column("generation_batch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_batches.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.UniqueConstraint("idempotency_key", "requested_by",
                            name="uq_generation_batch_idem_per_requester"),
    )
    op.create_index("ix_generation_batch_idem_expires_at",
                    "generation_batch_idempotency_keys", ["expires_at"])

    # --- question_jobs additions ---
    op.add_column(
        "question_jobs",
        sa.Column("generation_batch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_batches.id"), nullable=True),
    )
    op.create_index("ix_question_jobs_generation_batch_id",
                    "question_jobs", ["generation_batch_id"])
    op.add_column(
        "question_jobs",
        sa.Column("generation_request_jsonb", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "question_jobs",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "question_jobs",
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- questions additions ---
    op.add_column(
        "questions",
        sa.Column("is_canonical_source", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
    )


def downgrade():
    op.drop_column("questions", "is_canonical_source")
    op.drop_column("question_jobs", "last_retry_at")
    op.drop_column("question_jobs", "retry_count")
    op.drop_column("question_jobs", "generation_request_jsonb")
    op.drop_index("ix_question_jobs_generation_batch_id", table_name="question_jobs")
    op.drop_column("question_jobs", "generation_batch_id")

    op.drop_index("ix_generation_batch_idem_expires_at",
                  table_name="generation_batch_idempotency_keys")
    op.drop_table("generation_batch_idempotency_keys")

    op.drop_index("ix_generation_batches_requested_by_created_at",
                  table_name="generation_batches")
    op.drop_index("ix_generation_batches_requested_by_user_token",
                  table_name="generation_batches")
    op.drop_index("ix_generation_batches_student_id", table_name="generation_batches")
    op.drop_index("ix_generation_batches_status", table_name="generation_batches")
    op.drop_table("generation_batches")
    # job_status_enum values cannot be cleanly removed without rebuilding the
    # type; leave them in place. Any rows currently using the new values must
    # be migrated to another status before downgrade.
