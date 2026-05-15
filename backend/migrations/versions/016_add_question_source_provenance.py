"""Add question source provenance and stimulus asset tables.

Revision ID: 016
Revises: 015
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "question_source_spans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("question_job_id", sa.Uuid(), sa.ForeignKey("question_jobs.id"), nullable=True),
        sa.Column("raw_asset_id", sa.Uuid(), sa.ForeignKey("question_assets.id"), nullable=True),
        sa.Column("source_page_number", sa.Integer(), nullable=False),
        sa.Column("source_region_role", sa.String(40), nullable=False),
        sa.Column("extraction_method", sa.String(50), nullable=False),
        sa.Column("rendered_page_path", sa.Text(), nullable=True),
        sa.Column("crop_path", sa.Text(), nullable=True),
        sa.Column("ocr_text_path", sa.Text(), nullable=True),
        sa.Column("layout_json_path", sa.Text(), nullable=True),
        sa.Column("pymupdf_text", sa.Text(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("diagnostics_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("confidence_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_question_source_spans_question_id", "question_source_spans", ["question_id"])
    op.create_index("ix_question_source_spans_job_id", "question_source_spans", ["question_job_id"])
    op.create_index("ix_question_source_spans_raw_asset_id", "question_source_spans", ["raw_asset_id"])
    op.create_index("ix_question_source_spans_region_role", "question_source_spans", ["source_region_role"])
    op.create_index("ix_question_source_spans_extraction_method", "question_source_spans", ["extraction_method"])

    op.create_table(
        "question_stimulus_assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("question_job_id", sa.Uuid(), sa.ForeignKey("question_jobs.id"), nullable=True),
        sa.Column("raw_asset_id", sa.Uuid(), sa.ForeignKey("question_assets.id"), nullable=True),
        sa.Column("stimulus_type", sa.String(40), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("source_page_number", sa.Integer(), nullable=True),
        sa.Column("source_span_id", sa.Uuid(), sa.ForeignKey("question_source_spans.id"), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("structured_data_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("render_hints_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_question_stimulus_assets_question_id", "question_stimulus_assets", ["question_id"])
    op.create_index("ix_question_stimulus_assets_job_id", "question_stimulus_assets", ["question_job_id"])
    op.create_index("ix_question_stimulus_assets_raw_asset_id", "question_stimulus_assets", ["raw_asset_id"])
    op.create_index("ix_question_stimulus_assets_source_span_id", "question_stimulus_assets", ["source_span_id"])
    op.create_index("ix_question_stimulus_assets_type", "question_stimulus_assets", ["stimulus_type"])


def downgrade():
    op.drop_index("ix_question_stimulus_assets_type", table_name="question_stimulus_assets")
    op.drop_index("ix_question_stimulus_assets_source_span_id", table_name="question_stimulus_assets")
    op.drop_index("ix_question_stimulus_assets_raw_asset_id", table_name="question_stimulus_assets")
    op.drop_index("ix_question_stimulus_assets_job_id", table_name="question_stimulus_assets")
    op.drop_index("ix_question_stimulus_assets_question_id", table_name="question_stimulus_assets")
    op.drop_table("question_stimulus_assets")

    op.drop_index("ix_question_source_spans_extraction_method", table_name="question_source_spans")
    op.drop_index("ix_question_source_spans_region_role", table_name="question_source_spans")
    op.drop_index("ix_question_source_spans_raw_asset_id", table_name="question_source_spans")
    op.drop_index("ix_question_source_spans_job_id", table_name="question_source_spans")
    op.drop_index("ix_question_source_spans_question_id", table_name="question_source_spans")
    op.drop_table("question_source_spans")
