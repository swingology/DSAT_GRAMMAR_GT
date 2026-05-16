"""Add user_token column to users table.

Revision ID: 018
Revises: 017
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "user_token",
            postgresql.UUID(as_uuid=True),
            nullable=True,  # temporarily nullable for backfill
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    # Backfill existing rows
    op.execute("UPDATE users SET user_token = gen_random_uuid() WHERE user_token IS NULL")
    # Now enforce NOT NULL and unique
    op.alter_column("users", "user_token", nullable=False)
    op.create_unique_constraint("uq_users_user_token", "users", ["user_token"])
    op.create_index("ix_users_user_token", "users", ["user_token"])


def downgrade():
    op.drop_index("ix_users_user_token", table_name="users")
    op.drop_constraint("uq_users_user_token", "users", type_="unique")
    op.drop_column("users", "user_token")
