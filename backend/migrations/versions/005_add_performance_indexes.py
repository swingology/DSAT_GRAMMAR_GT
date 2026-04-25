"""Add performance indexes for common query paths.

Revision ID: 005
Revises: 004
Create Date: 2026-04-25
"""

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # questions — filtered by status/origin, joined via latest_annotation
    op.create_index("ix_questions_practice_status", "questions", ["practice_status"])
    op.create_index("ix_questions_content_origin", "questions", ["content_origin"])
    op.create_index("ix_questions_latest_annotation_id", "questions", ["latest_annotation_id"])

    # question_jobs — polled by status, ordered by created_at
    op.create_index("ix_question_jobs_status", "question_jobs", ["status"])
    op.create_index("ix_question_jobs_created_at", "question_jobs", ["created_at"])

    # user_progress — looked up by user and by question
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"])
    op.create_index("ix_user_progress_question_id", "user_progress", ["question_id"])

    # question_relations — traversed from both ends
    op.create_index("ix_question_relations_from_question_id", "question_relations", ["from_question_id"])
    op.create_index("ix_question_relations_to_question_id", "question_relations", ["to_question_id"])


def downgrade() -> None:
    op.drop_index("ix_question_relations_to_question_id", table_name="question_relations")
    op.drop_index("ix_question_relations_from_question_id", table_name="question_relations")
    op.drop_index("ix_user_progress_question_id", table_name="user_progress")
    op.drop_index("ix_user_progress_user_id", table_name="user_progress")
    op.drop_index("ix_question_jobs_created_at", table_name="question_jobs")
    op.drop_index("ix_question_jobs_status", table_name="question_jobs")
    op.drop_index("ix_questions_latest_annotation_id", table_name="questions")
    op.drop_index("ix_questions_content_origin", table_name="questions")
    op.drop_index("ix_questions_practice_status", table_name="questions")
