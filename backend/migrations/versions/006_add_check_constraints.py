"""Add DB-level check constraints mirroring Pydantic validation.

Revision ID: 006
Revises: 005
Create Date: 2026-04-25
"""

from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Option labels must be A–D
    op.create_check_constraint(
        "ck_question_options_option_label_a_to_d",
        "question_options",
        "option_label IN ('A', 'B', 'C', 'D')",
    )
    op.create_check_constraint(
        "ck_question_versions_correct_option_label_a_to_d",
        "question_versions",
        "correct_option_label IN ('A', 'B', 'C', 'D')",
    )
    op.create_check_constraint(
        "ck_questions_current_correct_option_label_a_to_d",
        "questions",
        "current_correct_option_label IN ('A', 'B', 'C', 'D')",
    )

    # LLM evaluation scores are 0–10 (NULL allowed — scores are optional)
    op.create_check_constraint(
        "ck_llm_evaluations_scores_range",
        "llm_evaluations",
        "(score_overall IS NULL OR score_overall BETWEEN 0 AND 10) AND "
        "(score_metadata IS NULL OR score_metadata BETWEEN 0 AND 10) AND "
        "(score_explanation IS NULL OR score_explanation BETWEEN 0 AND 10) AND "
        "(score_generation IS NULL OR score_generation BETWEEN 0 AND 10)",
    )

    # Relation strength is 0–1 (NULL allowed — strength is optional)
    op.create_check_constraint(
        "ck_question_relations_relation_strength_range",
        "question_relations",
        "relation_strength IS NULL OR relation_strength BETWEEN 0 AND 1",
    )


def downgrade() -> None:
    op.drop_constraint("ck_question_relations_relation_strength_range", "question_relations", type_="check")
    op.drop_constraint("ck_llm_evaluations_scores_range", "llm_evaluations", type_="check")
    op.drop_constraint("ck_questions_current_correct_option_label_a_to_d", "questions", type_="check")
    op.drop_constraint("ck_question_versions_correct_option_label_a_to_d", "question_versions", type_="check")
    op.drop_constraint("ck_question_options_option_label_a_to_d", "question_options", type_="check")
