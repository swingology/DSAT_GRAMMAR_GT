"""Add unique constraints on question_versions, question_options, question_relations.

Revision ID: 004
Revises: 003
Create Date: 2026-04-25
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Prevent duplicate version numbers within the same question
    op.create_unique_constraint(
        "uq_question_versions_question_version_number",
        "question_versions",
        ["question_id", "version_number"],
    )

    # Prevent duplicate option labels within the same question version
    op.create_unique_constraint(
        "uq_question_options_version_label",
        "question_options",
        ["question_version_id", "option_label"],
    )

    # Prevent duplicate (from, to, relation_type) triples
    op.create_unique_constraint(
        "uq_question_relations_pair_type",
        "question_relations",
        ["from_question_id", "to_question_id", "relation_type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_question_relations_pair_type", "question_relations", type_="unique")
    op.drop_constraint("uq_question_options_version_label", "question_options", type_="unique")
    op.drop_constraint("uq_question_versions_question_version_number", "question_versions", type_="unique")
