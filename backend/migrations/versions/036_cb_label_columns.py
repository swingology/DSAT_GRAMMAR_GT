"""Store College Board's own labels as first-class columns.

Adds cb_domain_key, cb_skill_key and cb_difficulty next to cb_question_id, so
CB's authoritative values live apart from the LLM-derived annotation_jsonb.

Also relaxes cb_question_id from UNIQUE to a plain index. The database holds the
same CB question more than once (2024 and 2025 releases of a practice test, plus
re-imports), and every copy must carry its CB labels, so the ID cannot be unique.

Revision ID: 036
Revises: 035
"""

from alembic import op
import sqlalchemy as sa


revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("cb_domain_key", sa.String(length=50), nullable=True))
    op.add_column("questions", sa.Column("cb_skill_key", sa.String(length=50), nullable=True))
    op.add_column("questions", sa.Column("cb_difficulty", sa.String(length=10), nullable=True))
    op.drop_constraint("uq_questions_cb_question_id", "questions", type_="unique")
    op.create_index("ix_questions_cb_question_id", "questions", ["cb_question_id"])
    op.create_index("ix_questions_cb_skill_key", "questions", ["cb_skill_key"])


def downgrade() -> None:
    op.drop_index("ix_questions_cb_skill_key", table_name="questions")
    op.drop_index("ix_questions_cb_question_id", table_name="questions")
    # Re-imposing uniqueness is only possible with one row per CB ID, so keep the
    # ID on the oldest copy and clear it from the rest before adding the constraint.
    op.execute(
        """
        update questions q set cb_question_id = null
        where cb_question_id is not null and exists (
            select 1 from questions o
            where o.cb_question_id = q.cb_question_id
              and (o.created_at, o.id) < (q.created_at, q.id))
        """
    )
    op.create_unique_constraint("uq_questions_cb_question_id", "questions", ["cb_question_id"])
    op.drop_column("questions", "cb_difficulty")
    op.drop_column("questions", "cb_skill_key")
    op.drop_column("questions", "cb_domain_key")
