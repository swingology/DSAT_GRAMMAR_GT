"""Unique constraint on official question canonical identity.

Official College Board questions are uniquely identified by:
  (exam_code, subject_code, section_code, module_code, question_number)

The partial index enforces this only for content_origin = 'official', leaving
unofficial/generated questions free of the constraint.
"""
from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    op.drop_index(
        "uq_official_question_canonical_identity",
        table_name="questions",
    )
