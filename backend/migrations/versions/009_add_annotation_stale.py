"""Add annotation_stale flag to questions.

Revision ID: 009
Revises: 008
Create Date: 2026-04-25

Set to True by admin edits so the queue can surface questions whose
LLM-generated annotation is no longer consistent with the edited text.
Cleared to False after a successful reannotation run.
"""

from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column(
            "annotation_stale",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("questions", "annotation_stale")
