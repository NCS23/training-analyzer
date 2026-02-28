"""add rpe column to workouts table

Revision ID: c008
Revises: c007
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c008"
down_revision: Union[str, Sequence[str], None] = "c007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rpe column to workouts table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c["name"] for c in inspector.get_columns("workouts")}

    if "rpe" not in existing_columns:
        op.add_column("workouts", sa.Column("rpe", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove rpe column from workouts table."""
    op.drop_column("workouts", "rpe")
