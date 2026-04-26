"""Add passage_group_id to questions.

Revision ID: 010
Revises: 009
Create Date: 2026-04-25

Groups questions that belong to the same passage (e.g., multiple questions
sharing one passage in official SAT practice tests). A future Passage table
may use this UUID as its primary key.
"""

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("passage_group_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        "ix_questions_passage_group_id",
        "questions",
        ["passage_group_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_questions_passage_group_id")
    op.drop_column("questions", "passage_group_id")
