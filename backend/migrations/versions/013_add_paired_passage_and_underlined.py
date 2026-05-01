"""Add paired_passage_text and underlined_text to questions and question_versions.

Revision ID: 013
Revises: 012
Create Date: 2026-05-01
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("current_paired_passage_text", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("current_underlined_text", sa.Text(), nullable=True))
    op.add_column("question_versions", sa.Column("paired_passage_text", sa.Text(), nullable=True))
    op.add_column("question_versions", sa.Column("underlined_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("question_versions", "underlined_text")
    op.drop_column("question_versions", "paired_passage_text")
    op.drop_column("questions", "current_underlined_text")
    op.drop_column("questions", "current_paired_passage_text")
