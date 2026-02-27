"""add exercises_json column for strength training

Revision ID: c004
Revises: c003
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c004"
down_revision: Union[str, Sequence[str], None] = "c003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add exercises_json column to workouts table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = [c["name"] for c in inspector.get_columns("workouts")]

    if "exercises_json" not in existing:
        op.add_column("workouts", sa.Column("exercises_json", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove exercises_json column."""
    op.drop_column("workouts", "exercises_json")
