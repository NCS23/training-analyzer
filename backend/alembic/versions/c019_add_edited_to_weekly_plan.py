"""Add edited flag to weekly_plan_entries.

Tracks whether a generated entry was manually modified.
Default False for all existing entries.

Revision ID: c019
Revises: c018
"""

import sqlalchemy as sa
from alembic import op

revision = "c019"
down_revision = "c018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "weekly_plan_entries",
        sa.Column(
            "edited",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("weekly_plan_entries", "edited")
