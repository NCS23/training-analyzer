"""add race_goals table

Revision ID: c003
Revises: c002
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c003"
down_revision: Union[str, Sequence[str], None] = "c002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create race_goals table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "race_goals" not in inspector.get_table_names():
        op.create_table(
            "race_goals",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("race_date", sa.DateTime(), nullable=False, index=True),
            sa.Column("distance_km", sa.Float(), nullable=False),
            sa.Column("target_time_seconds", sa.Integer(), nullable=False),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default="1",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )


def downgrade() -> None:
    """Drop race_goals table."""
    op.drop_table("race_goals")
