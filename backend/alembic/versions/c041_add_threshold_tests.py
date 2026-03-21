"""Add threshold_tests table for lactate threshold field tests.

Stores results from 30-min Friel tests (LTHR, max HR, pace)
with optional reference to imported workout session.

Revision ID: c041
Revises: c040
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "c041"
down_revision = "c040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "threshold_tests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("lthr", sa.Integer(), nullable=False),
        sa.Column("max_hr_measured", sa.Integer(), nullable=True),
        sa.Column("avg_pace_sec", sa.Float(), nullable=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("workouts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("threshold_tests")
