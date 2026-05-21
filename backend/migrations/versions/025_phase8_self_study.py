"""Phase 8: add denormalized target columns to user_progress.

Revision ID: 025
Revises: 024
Create Date: 2026-05-20

Adds four columns to user_progress so the weakness-profile computation
can group by target dimensions without joining question_annotations:

  * missed_reading_focus_key   — reading focus key for the answered question
  * missed_reading_skill_family_key — reading skill family for the question
  * question_domain            — 'grammar' or 'reading' (always set at submit)
  * question_difficulty        — difficulty_overall of the question

These fields are populated at submit time from the question's latest
annotation JSONB, enabling the self-study weakness profile to group
by target without a runtime join.
"""

from alembic import op
import sqlalchemy as sa


revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_progress",
        sa.Column("missed_reading_focus_key", sa.String(100), nullable=True),
    )
    op.add_column(
        "user_progress",
        sa.Column("missed_reading_skill_family_key", sa.String(100), nullable=True),
    )
    op.add_column(
        "user_progress",
        sa.Column("question_domain", sa.String(20), nullable=True),
    )
    op.add_column(
        "user_progress",
        sa.Column("question_difficulty", sa.String(20), nullable=True),
    )

    op.create_index(
        "ix_user_progress_question_domain", "user_progress", ["question_domain"]
    )
    op.create_index(
        "ix_user_progress_timestamp", "user_progress", ["timestamp"]
    )


def downgrade():
    op.drop_index("ix_user_progress_timestamp", "user_progress")
    op.drop_index("ix_user_progress_question_domain", "user_progress")
    op.drop_column("user_progress", "question_difficulty")
    op.drop_column("user_progress", "question_domain")
    op.drop_column("user_progress", "missed_reading_skill_family_key")
    op.drop_column("user_progress", "missed_reading_focus_key")
