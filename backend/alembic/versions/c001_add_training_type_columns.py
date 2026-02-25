"""add training type classification columns

Revision ID: c001
Revises: b88ba9d87040
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c001"
down_revision: Union[str, Sequence[str], None] = "b88ba9d87040"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add training_type columns if missing."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = [c["name"] for c in inspector.get_columns("workouts")]

    if "training_type_auto" not in existing:
        op.add_column("workouts", sa.Column("training_type_auto", sa.String(30), nullable=True))
    if "training_type_confidence" not in existing:
        op.add_column(
            "workouts", sa.Column("training_type_confidence", sa.Integer(), nullable=True)
        )
    if "training_type_override" not in existing:
        op.add_column(
            "workouts", sa.Column("training_type_override", sa.String(30), nullable=True)
        )


def downgrade() -> None:
    """Remove training_type columns."""
    op.drop_column("workouts", "training_type_override")
    op.drop_column("workouts", "training_type_confidence")
    op.drop_column("workouts", "training_type_auto")
