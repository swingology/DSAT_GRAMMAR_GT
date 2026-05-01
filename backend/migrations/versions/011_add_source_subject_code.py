"""Add source_subject_code to questions and assets.

Revision ID: 011
Revises: 010
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("source_subject_code", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "question_assets",
        sa.Column("source_subject_code", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("question_assets", "source_subject_code")
    op.drop_column("questions", "source_subject_code")
