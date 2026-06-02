"""Add source release year and test name metadata.

Revision ID: 029
Revises: 028
"""
from alembic import op
import sqlalchemy as sa

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("source_release_year", sa.Integer(), nullable=True))
    op.add_column("questions", sa.Column("source_test_name", sa.String(100), nullable=True))
    op.add_column("question_assets", sa.Column("source_release_year", sa.Integer(), nullable=True))
    op.add_column("question_assets", sa.Column("source_test_name", sa.String(100), nullable=True))

    op.execute(
        """
        UPDATE questions
        SET source_test_name = 'Test ' || source_exam_code
        WHERE source_test_name IS NULL
          AND source_exam_code IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE question_assets
        SET source_test_name = COALESCE(
            NULLIF(regexp_replace(regexp_replace(source_name, '_digital_.*$', ''), '_+', ' ', 'g'), ''),
            'Test ' || source_exam_code
        )
        WHERE source_test_name IS NULL
          AND (source_name IS NOT NULL OR source_exam_code IS NOT NULL)
        """
    )

    op.drop_index("uq_official_question_canonical_identity", table_name="questions")
    op.execute(
        """
        CREATE UNIQUE INDEX uq_official_question_canonical_identity
        ON questions (
            COALESCE(source_release_year, 0),
            COALESCE(source_test_name, ''),
            source_exam_code,
            source_subject_code,
            source_section_code,
            source_module_code,
            source_question_number
        )
        WHERE content_origin = 'official'
        """
    )

    op.create_index(
        "ix_questions_source_release_sort",
        "questions",
        [
            "source_release_year",
            "source_test_name",
            "source_exam_code",
            "source_subject_code",
            "source_section_code",
            "source_module_code",
            "source_question_number",
        ],
    )
    op.create_index(
        "ix_question_assets_source_release",
        "question_assets",
        [
            "source_release_year",
            "source_test_name",
            "source_exam_code",
            "source_subject_code",
            "source_section_code",
            "source_module_code",
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_question_assets_source_release", table_name="question_assets")
    op.drop_index("ix_questions_source_release_sort", table_name="questions")
    op.drop_index("uq_official_question_canonical_identity", table_name="questions")
    op.create_index(
        "uq_official_question_canonical_identity",
        "questions",
        [
            "source_exam_code",
            "source_subject_code",
            "source_section_code",
            "source_module_code",
            "source_question_number",
        ],
        unique=True,
        postgresql_where="content_origin = 'official'",
    )
    op.drop_column("question_assets", "source_test_name")
    op.drop_column("question_assets", "source_release_year")
    op.drop_column("questions", "source_test_name")
    op.drop_column("questions", "source_release_year")
