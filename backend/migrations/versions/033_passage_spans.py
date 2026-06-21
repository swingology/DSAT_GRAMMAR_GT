"""Add passage_spans columns to question_annotations and span_review_queue table.

Revision ID: 033
Revises: 032
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "033"
down_revision = "032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("question_annotations", sa.Column("passage_spans", JSONB, nullable=True))
    op.add_column("question_annotations", sa.Column("span_annotated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("question_annotations", sa.Column("span_model_name", sa.String(100), nullable=True))

    op.execute(
        "CREATE INDEX ix_qa_passage_spans_gin ON question_annotations USING GIN (passage_spans)"
    )

    op.create_table(
        "span_review_queue",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("question_id", sa.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("annotation_id", sa.UUID(as_uuid=True), sa.ForeignKey("question_annotations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_type", sa.String(80), nullable=False),
        sa.Column("error_detail", sa.Text, nullable=True),
        sa.Column("raw_llm_output", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(100), nullable=True),
        sa.Column("resolution_note", sa.Text, nullable=True),
    )

    op.create_index("ix_srq_question_id", "span_review_queue", ["question_id"])
    op.create_index("ix_srq_error_type", "span_review_queue", ["error_type"])
    op.execute(
        "CREATE INDEX ix_srq_unresolved ON span_review_queue (created_at) WHERE resolved_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_srq_unresolved")
    op.drop_index("ix_srq_error_type", table_name="span_review_queue")
    op.drop_index("ix_srq_question_id", table_name="span_review_queue")
    op.drop_table("span_review_queue")
    op.execute("DROP INDEX IF EXISTS ix_qa_passage_spans_gin")
    op.drop_column("question_annotations", "span_model_name")
    op.drop_column("question_annotations", "span_annotated_at")
    op.drop_column("question_annotations", "passage_spans")
