"""Add questions.source_pt_number — the canonical practice-test number.

410 official rows have a blank source_test_name and carry the PT# only in
source_exam_code ("4", "04"); 57 others have a non-numeric exam code ("verbal",
"SAT") and carry it in source_test_name. The raw fields stay as provenance. This
column is what grouping, filtering and labels use, and the Question model's
insert/update listeners keep it set (app.models.db.derive_pt_number). The backfill
below is the SQL form of that function.

Revision ID: 039
Revises: 038
"""

from alembic import op
import sqlalchemy as sa


revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("source_pt_number", sa.SmallInteger(), nullable=True))
    op.create_index("ix_questions_source_pt_number", "questions", ["source_pt_number"])
    op.execute(
        """
        UPDATE questions q SET source_pt_number = d.pt
        FROM (
            SELECT id, coalesce(
                nullif(regexp_replace(coalesce(source_exam_code, ''), '[^0-9]', '', 'g'), ''),
                substring(coalesce(source_test_name, '') from '[0-9]+')
            )::bigint AS pt
            FROM questions
        ) d
        WHERE d.id = q.id AND d.pt BETWEEN 1 AND 99
        """
    )


def downgrade() -> None:
    op.drop_index("ix_questions_source_pt_number", table_name="questions")
    op.drop_column("questions", "source_pt_number")
