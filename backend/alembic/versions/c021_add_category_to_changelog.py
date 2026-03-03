"""Add category column to plan_changelog.

Enables filtering changelog entries by category
(content, structure, technical, meta).

Revision ID: c021
Revises: c020
"""

import sqlalchemy as sa
from alembic import op

revision = "c021"
down_revision = "c020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plan_changelog",
        sa.Column("category", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plan_changelog", "category")
