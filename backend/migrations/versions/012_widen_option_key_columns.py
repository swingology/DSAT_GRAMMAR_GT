"""Widen VARCHAR(30/40) key columns in question_options that LLM values can overflow.

Revision ID: 012
Revises: 011
Create Date: 2026-05-01
"""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("question_options") as batch_op:
        batch_op.alter_column("distractor_type_key", type_=sa.String(100))
        batch_op.alter_column("plausibility_source_key", type_=sa.String(100))
        batch_op.alter_column("student_failure_mode_key", type_=sa.String(100))
        batch_op.alter_column("semantic_relation_key", type_=sa.String(100))
        batch_op.alter_column("option_error_focus_key", type_=sa.String(100))
        batch_op.alter_column("distractor_distance", type_=sa.String(50))


def downgrade() -> None:
    with op.batch_alter_table("question_options") as batch_op:
        batch_op.alter_column("distractor_type_key", type_=sa.String(30))
        batch_op.alter_column("plausibility_source_key", type_=sa.String(30))
        batch_op.alter_column("student_failure_mode_key", type_=sa.String(30))
        batch_op.alter_column("semantic_relation_key", type_=sa.String(40))
        batch_op.alter_column("option_error_focus_key", type_=sa.String(40))
        batch_op.alter_column("distractor_distance", type_=sa.String(10))
