"""Widen VARCHAR vocab key columns on the questions table.

Migration 012 widened these on question_options but missed the questions
table. stem_type_key (VARCHAR(40)) overflows when the LLM emits unknown
amendment-candidate keys like `identify_evidence_that_supports_conclusion`
(44 chars); the soft-validate path expects to record the value for review
but the column rejects it.

stimulus_mode_key (VARCHAR(30)) currently has 14 chars of headroom against
the longest canonical key but is widened proactively for the same reason.

Revision ID: 019
Revises: 018
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.alter_column("stem_type_key", type_=sa.String(100))
        batch_op.alter_column("stimulus_mode_key", type_=sa.String(100))


def downgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.alter_column("stem_type_key", type_=sa.String(40))
        batch_op.alter_column("stimulus_mode_key", type_=sa.String(30))
