"""Add source_section_code to questions table.

Revision ID: 003
Revises: 002
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("source_section_code", sa.String(10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("questions", "source_section_code")
