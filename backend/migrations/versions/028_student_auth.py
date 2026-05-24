"""Student auth — add email, password_hash, role, is_active, refresh_token columns.

Revision ID: 028
Revises: 027
"""
from alembic import op
import sqlalchemy as sa

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("role", sa.String(20), server_default="student", nullable=False))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("users", sa.Column("refresh_token", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("refresh_token_expires", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email")
    op.drop_column("users", "refresh_token_expires")
    op.drop_column("users", "refresh_token")
    op.drop_column("users", "is_active")
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")