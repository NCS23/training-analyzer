"""Rename training_plans -> session_templates, plan_id -> template_id.

Revision ID: c013
Revises: c012
Create Date: 2026-03-01
"""

from alembic import op

revision = "c013"
down_revision = "c012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("training_plans", "session_templates")
    op.alter_column(
        "weekly_plan_entries",
        "plan_id",
        new_column_name="template_id",
    )


def downgrade() -> None:
    op.alter_column(
        "weekly_plan_entries",
        "template_id",
        new_column_name="plan_id",
    )
    op.rename_table("session_templates", "training_plans")
