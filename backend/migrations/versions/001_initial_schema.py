"""Initial schema: all 10 tables with enums.

Revision ID: 001
Revises: None
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

# ── Enum value tuples (must match app/models/ontology.py) ──────────────

JOB_TYPE_VALUES = ("ingest", "generate", "reannotate", "overlap_check")
CONTENT_ORIGIN_VALUES = ("official", "unofficial", "generated")
JOB_STATUS_VALUES = (
    "pending", "parsing", "extracting", "generating",
    "annotating", "overlap_checking", "validating",
    "approved", "needs_review", "failed",
)
PRACTICE_STATUS_VALUES = ("draft", "active", "retired")
OVERLAP_STATUS_VALUES = ("none", "possible", "confirmed")
RELATION_TYPE_VALUES = (
    "overlaps_official", "derived_from", "near_duplicate",
    "generated_from", "adapted_from",
)
ASSET_TYPE_VALUES = ("pdf", "image", "screenshot", "markdown", "json", "text")
CHANGE_SOURCE_VALUES = ("ingest", "generate", "admin_edit", "reprocess")


def upgrade() -> None:
    # ── Create PostgreSQL ENUM types ────────────────────────────────────
    # Each enum name must match what SQLAlchemy generates in the ORM.
    enums = [
        ("job_type_enum", JOB_TYPE_VALUES),
        ("content_origin_enum", CONTENT_ORIGIN_VALUES),
        ("content_origin_enum2", CONTENT_ORIGIN_VALUES),
        ("content_origin_enum3", CONTENT_ORIGIN_VALUES),
        ("job_status_enum", JOB_STATUS_VALUES),
        ("practice_status_enum", PRACTICE_STATUS_VALUES),
        ("overlap_status_enum", OVERLAP_STATUS_VALUES),
        ("relation_type_enum", RELATION_TYPE_VALUES),
        ("asset_type_enum", ASSET_TYPE_VALUES),
        ("change_source_enum", CHANGE_SOURCE_VALUES),
    ]
    for name, values in enums:
        postgresql.ENUM(*values, name=name).create(op.get_bind(), checkfirst=True)

    # ── Create tables in dependency order ────────────────────────────────

    # 1. question_assets (FK → questions, but questions doesn't exist yet;
    #    we create the FK without the referenced table first and add it
    #    after questions is created. SQLAlchemy ORM has this same circularity.)
    op.create_table(
        "question_assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=True),
        sa.Column("content_origin", postgresql.ENUM("official", "unofficial", "generated", name="content_origin_enum3", create_type=False), nullable=False),
        sa.Column("asset_type", postgresql.ENUM("pdf", "image", "screenshot", "markdown", "json", "text", name="asset_type_enum", create_type=False), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("source_exam_code", sa.String(20), nullable=True),
        sa.Column("source_module_code", sa.String(10), nullable=True),
        sa.Column("source_question_number", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. question_jobs (FK → question_assets, questions)
    op.create_table(
        "question_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_type", postgresql.ENUM("ingest", "generate", "reannotate", "overlap_check", name="job_type_enum", create_type=False), nullable=False),
        sa.Column("content_origin", postgresql.ENUM("official", "unofficial", "generated", name="content_origin_enum", create_type=False), nullable=False),
        sa.Column("input_format", sa.String(20), nullable=False),
        sa.Column("status", postgresql.ENUM("pending", "parsing", "extracting", "generating", "annotating", "overlap_checking", "validating", "approved", "needs_review", "failed", name="job_status_enum", create_type=False), nullable=False),
        sa.Column("provider_name", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(20), nullable=False),
        sa.Column("rules_version", sa.String(100), nullable=False),
        sa.Column("raw_asset_id", sa.Uuid(), sa.ForeignKey("question_assets.id"), nullable=True),
        sa.Column("pass1_json", postgresql.JSONB(), nullable=True),
        sa.Column("pass2_json", postgresql.JSONB(), nullable=True),
        sa.Column("validation_errors_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("comparison_group_id", sa.Uuid(), nullable=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 3. questions (self-referential FKs, FK → question_annotations, question_versions)
    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("content_origin", postgresql.ENUM("official", "unofficial", "generated", name="content_origin_enum2", create_type=False), nullable=False),
        sa.Column("source_exam_code", sa.String(20), nullable=True),
        sa.Column("source_module_code", sa.String(10), nullable=True),
        sa.Column("source_question_number", sa.Integer(), nullable=True),
        sa.Column("stimulus_mode_key", sa.String(30), nullable=True),
        sa.Column("stem_type_key", sa.String(40), nullable=True),
        sa.Column("current_question_text", sa.Text(), nullable=False),
        sa.Column("current_passage_text", sa.Text(), nullable=True),
        sa.Column("current_correct_option_label", sa.String(1), nullable=False),
        sa.Column("current_explanation_text", sa.Text(), nullable=True),
        sa.Column("practice_status", postgresql.ENUM("draft", "active", "retired", name="practice_status_enum", create_type=False), nullable=False),
        sa.Column("official_overlap_status", postgresql.ENUM("none", "possible", "confirmed", name="overlap_status_enum", create_type=False), nullable=False),
        sa.Column("canonical_official_question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=True),
        sa.Column("derived_from_question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=True),
        sa.Column("generation_source_set", postgresql.JSONB(), nullable=True),
        sa.Column("is_admin_edited", sa.Boolean(), nullable=False),
        sa.Column("metadata_managed_by_llm", sa.Boolean(), nullable=False),
        sa.Column("latest_annotation_id", sa.Uuid(), sa.ForeignKey("question_annotations.id"), nullable=True),
        sa.Column("latest_version_id", sa.Uuid(), sa.ForeignKey("question_versions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 4. question_versions (FK → questions)
    op.create_table(
        "question_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("change_source", postgresql.ENUM("ingest", "generate", "admin_edit", "reprocess", name="change_source_enum", create_type=False), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("passage_text", sa.Text(), nullable=True),
        sa.Column("choices_jsonb", postgresql.JSONB(), nullable=False),
        sa.Column("correct_option_label", sa.String(1), nullable=False),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("editor_user_id", sa.String(50), nullable=True),
        sa.Column("change_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 5. question_annotations (FK → questions, question_versions)
    op.create_table(
        "question_annotations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("question_version_id", sa.Uuid(), sa.ForeignKey("question_versions.id"), nullable=False),
        sa.Column("provider_name", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(20), nullable=False),
        sa.Column("rules_version", sa.String(100), nullable=False),
        sa.Column("annotation_jsonb", postgresql.JSONB(), nullable=False),
        sa.Column("explanation_jsonb", postgresql.JSONB(), nullable=False),
        sa.Column("generation_profile_jsonb", postgresql.JSONB(), nullable=True),
        sa.Column("confidence_jsonb", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 6. question_options (FK → questions, question_versions)
    op.create_table(
        "question_options",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("question_version_id", sa.Uuid(), sa.ForeignKey("question_versions.id"), nullable=False),
        sa.Column("option_label", sa.String(1), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("option_role", sa.String(10), nullable=False),
        sa.Column("distractor_type_key", sa.String(30), nullable=True),
        sa.Column("semantic_relation_key", sa.String(40), nullable=True),
        sa.Column("plausibility_source_key", sa.String(30), nullable=True),
        sa.Column("option_error_focus_key", sa.String(40), nullable=True),
        sa.Column("why_plausible", sa.Text(), nullable=True),
        sa.Column("why_wrong", sa.Text(), nullable=True),
        sa.Column("grammar_fit", sa.String(3), nullable=True),
        sa.Column("tone_match", sa.String(3), nullable=True),
        sa.Column("precision_score", sa.SmallInteger(), nullable=True),
        sa.Column("student_failure_mode_key", sa.String(30), nullable=True),
        sa.Column("distractor_distance", sa.String(10), nullable=True),
        sa.Column("distractor_competition_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 7. question_relations (FK → questions x2)
    op.create_table(
        "question_relations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("from_question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("to_question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("relation_type", postgresql.ENUM("overlaps_official", "derived_from", "near_duplicate", "generated_from", "adapted_from", name="relation_type_enum", create_type=False), nullable=False),
        sa.Column("relation_strength", sa.Float(), nullable=True),
        sa.Column("detection_method", sa.String(30), nullable=True),
        sa.Column("is_human_confirmed", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 8. llm_evaluations (FK → question_jobs, questions)
    op.create_table(
        "llm_evaluations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("question_jobs.id"), nullable=False),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=True),
        sa.Column("provider_name", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("task_type", sa.String(20), nullable=False),
        sa.Column("score_overall", sa.Float(), nullable=True),
        sa.Column("score_metadata", sa.Float(), nullable=True),
        sa.Column("score_explanation", sa.Float(), nullable=True),
        sa.Column("score_generation", sa.Float(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("recommended_for_default", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 9. users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"])

    # 10. user_progress (FK → users, questions)
    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("selected_option_label", sa.String(1), nullable=False),
        sa.Column("missed_grammar_focus_key", sa.String(50), nullable=True),
        sa.Column("missed_syntactic_trap_key", sa.String(50), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_progress_id", "user_progress", ["id"])


def downgrade() -> None:
    # ── Drop tables in reverse creation order ───────────────────────────
    op.drop_table("user_progress")
    op.drop_table("users")
    op.drop_table("llm_evaluations")
    op.drop_table("question_relations")
    op.drop_table("question_options")
    op.drop_table("question_annotations")
    op.drop_table("question_versions")
    op.drop_table("questions")
    op.drop_table("question_jobs")
    op.drop_table("question_assets")

    # ── Drop ENUM types ─────────────────────────────────────────────────
    for name, _ in reversed(enums):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)