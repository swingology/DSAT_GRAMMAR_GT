"""Add source_section_code to question_assets for asset-level provenance.

Revision ID: 007
Revises: 006
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "question_assets",
        sa.Column("source_section_code", sa.String(10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("question_assets", "source_section_code")
