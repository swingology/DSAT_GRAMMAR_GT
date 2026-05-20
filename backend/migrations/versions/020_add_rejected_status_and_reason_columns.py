"""Phase 0: add `rejected` practice_status value and rejection reason columns.

Revision ID: 020
Revises: 019
Create Date: 2026-05-19

The generation/review/self-study factory needs rejection to be a distinct,
audit-preserved terminal state separate from `retired` (post-active removal).
This migration:

  * Adds `"rejected"` to the `practice_status_enum` PostgreSQL type.
  * Adds three nullable columns on `questions` to record why and by whom a
    question was rejected: `rejection_reason`, `rejected_at`,
    `rejected_by_admin_token`.

`ALTER TYPE ... ADD VALUE` cannot run inside a transaction on older
PostgreSQL versions, so the enum extension is issued with an autocommit
connection.
"""

from alembic import op
import sqlalchemy as sa


revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade():
    # Extend the enum first, with autocommit so the new value is visible to
    # subsequent statements in the same migration.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE practice_status_enum ADD VALUE IF NOT EXISTS 'rejected'"
        )

    op.add_column(
        "questions",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("rejected_by_admin_token", sa.String(length=128), nullable=True),
    )


def downgrade():
    # Drop the reason columns. The enum value cannot be removed cleanly on
    # PostgreSQL without rebuilding the type; leave it in place. Any rows
    # currently using `rejected` must be migrated to another status before
    # downgrade if a strict rollback is required.
    op.drop_column("questions", "rejected_by_admin_token")
    op.drop_column("questions", "rejected_at")
    op.drop_column("questions", "rejection_reason")
