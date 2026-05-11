"""Add index on question_jobs.comparison_group_id for benchmark poll queries."""
from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_question_jobs_comparison_group_id",
        "question_jobs",
        ["comparison_group_id"],
    )


def downgrade():
    op.drop_index("ix_question_jobs_comparison_group_id", table_name="question_jobs")
