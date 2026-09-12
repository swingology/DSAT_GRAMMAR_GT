"""Add College Board question bank ID for dedup/sync.

Revision ID: 035
Revises: 034
"""

from alembic import op
import sqlalchemy as sa


revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("cb_question_id", sa.String(length=8), nullable=True),
    )
    op.create_unique_constraint(
        "uq_questions_cb_question_id", "questions", ["cb_question_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_questions_cb_question_id", "questions", type_="unique")
    op.drop_column("questions", "cb_question_id")
