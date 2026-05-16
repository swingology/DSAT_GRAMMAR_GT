"""Add question_job_questions junction table.

Revision ID: 017
Revises: 016
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "question_job_questions",
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("question_jobs.id"), primary_key=True, nullable=False),
        sa.Column("question_id", sa.Uuid(), sa.ForeignKey("questions.id"), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_qjq_job_id", "question_job_questions", ["job_id"])
    op.create_index("ix_qjq_question_id", "question_job_questions", ["question_id"])


def downgrade():
    op.drop_index("ix_qjq_question_id", table_name="question_job_questions")
    op.drop_index("ix_qjq_job_id", table_name="question_job_questions")
    op.drop_table("question_job_questions")
