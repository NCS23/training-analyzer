"""Add plan_changelog table for audit trail.

Tracks all changes made to training plans (create, update, phase changes,
generation, back-sync, manual edits, YAML imports).

Revision ID: c020
Revises: c019
"""

import sqlalchemy as sa
from alembic import op

revision = "c020"
down_revision = "c019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plan_changelog",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("plan_id", sa.Integer, nullable=False, index=True),
        sa.Column("change_type", sa.String(30), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("details_json", sa.Text, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("plan_changelog")
