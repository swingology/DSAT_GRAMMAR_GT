"""Admin question audit log table.

Revision ID: 027
Revises: 026
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_question_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", UUID(as_uuid=True),
                  sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("admin_token", sa.String(128), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("fields_changed", JSONB, nullable=True),
        sa.Column("before_jsonb", JSONB, nullable=True),
        sa.Column("after_jsonb", JSONB, nullable=True),
        sa.Column("change_notes", sa.Text, nullable=True),
        sa.Column("question_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("question_versions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_admin_audit_question_id",
                    "admin_question_audit_logs", ["question_id"])
    op.create_index("ix_admin_audit_created_at",
                    "admin_question_audit_logs", ["created_at"])
    op.create_index("ix_admin_audit_action",
                    "admin_question_audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_admin_audit_action",      table_name="admin_question_audit_logs")
    op.drop_index("ix_admin_audit_created_at",  table_name="admin_question_audit_logs")
    op.drop_index("ix_admin_audit_question_id", table_name="admin_question_audit_logs")
    op.drop_table("admin_question_audit_logs")
