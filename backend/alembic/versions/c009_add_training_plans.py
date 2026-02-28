"""Add training plans table for strength session planning.

Revision ID: c009
Revises: c008_add_rpe_column
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "c009"
down_revision = "c008_add_rpe_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_plans",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "session_type",
            sa.String(30),
            nullable=False,
            server_default="strength",
        ),
        sa.Column("exercises_json", sa.Text(), nullable=True),
        sa.Column(
            "is_template",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("training_plans")
