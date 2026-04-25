"""Expand question_relations.detection_method to text.

Revision ID: 002
Revises: 001
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "question_relations",
        "detection_method",
        existing_type=sa.String(length=30),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "question_relations",
        "detection_method",
        existing_type=sa.Text(),
        type_=sa.String(length=30),
        existing_nullable=True,
    )
