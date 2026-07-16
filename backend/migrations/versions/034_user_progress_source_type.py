"""Add source type to user progress.

Revision ID: 034
Revises: 033
"""

from alembic import op
import sqlalchemy as sa


revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_progress",
        sa.Column("source_type", sa.String(length=20), nullable=True),
    )
    op.execute(
        """
        UPDATE user_progress
        SET source_type = CASE
            WHEN diagnostic_session_id IS NOT NULL THEN 'diagnostic'
            ELSE 'unknown'
        END
        WHERE source_type IS NULL
        """
    )
    op.create_index(
        "ix_user_progress_source_type",
        "user_progress",
        ["source_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_progress_source_type", table_name="user_progress")
    op.drop_column("user_progress", "source_type")
