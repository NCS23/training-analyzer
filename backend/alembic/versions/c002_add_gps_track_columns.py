"""add GPS track columns

Revision ID: c002
Revises: c001
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c002"
down_revision: Union[str, Sequence[str], None] = "c001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add gps_track_json and has_gps columns if missing."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = [c["name"] for c in inspector.get_columns("workouts")]

    if "gps_track_json" not in existing:
        op.add_column("workouts", sa.Column("gps_track_json", sa.Text(), nullable=True))
    if "has_gps" not in existing:
        op.add_column(
            "workouts",
            sa.Column("has_gps", sa.Boolean(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    """Remove GPS columns."""
    op.drop_column("workouts", "has_gps")
    op.drop_column("workouts", "gps_track_json")
