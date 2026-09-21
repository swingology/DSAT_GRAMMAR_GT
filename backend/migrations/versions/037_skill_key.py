"""Add questions.skill_key — the universal College Board skill for every question.

A new column rather than a wider skill_family_key: several readers treat the mere
presence of skill_family_key as "this is a reading question" (derive_domain, the
diagnostic pool, the practice filter, auto-release), so filling that key on grammar
rows would misroute them. A new column cannot change what any existing reader sees.

Values are SKILL_FAMILY_KEYS (ontology.py). Where cb_skill_key is set, skill_key is
CB's label, with Command of Evidence split into textual / quantitative.

Revision ID: 037
Revises: 036
"""

from alembic import op
import sqlalchemy as sa


revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("skill_key", sa.String(length=50), nullable=True))
    op.add_column("questions", sa.Column("skill_key_source", sa.String(length=20), nullable=True))
    op.create_index("ix_questions_skill_key", "questions", ["skill_key"])


def downgrade() -> None:
    op.drop_index("ix_questions_skill_key", table_name="questions")
    op.drop_column("questions", "skill_key_source")
    op.drop_column("questions", "skill_key")
