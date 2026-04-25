"""Add server_default=now() to all timestamp columns.

Revision ID: 008
Revises: 007
Create Date: 2026-04-25

Gap 4: ORM uses Python-side defaults for timestamps but migrations declare
those columns nullable=True with no server_default, making raw SQL inserts
produce NULL timestamps. Adding server_default=now() closes the gap without
changing nullability (so existing rows are unaffected).

Note: detection_method was already widened to Text in migration 002.
"""

from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None

# (table, column) pairs whose created_at / updated_at / timestamp columns
# need a server_default.
_TIMESTAMP_COLUMNS = [
    ("users", "created_at"),
    ("question_assets", "created_at"),
    ("questions", "created_at"),
    ("questions", "updated_at"),
    ("question_versions", "created_at"),
    ("question_annotations", "created_at"),
    ("question_options", "created_at"),
    ("question_relations", "created_at"),
    ("question_jobs", "created_at"),
    ("question_jobs", "updated_at"),
    ("llm_evaluations", "created_at"),
    ("user_progress", "timestamp"),
]


def upgrade() -> None:
    for table, column in _TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            server_default=sa.text("now()"),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=True,
        )

def downgrade() -> None:
    for table, column in reversed(_TIMESTAMP_COLUMNS):
        op.alter_column(
            table,
            column,
            server_default=None,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=True,
        )
