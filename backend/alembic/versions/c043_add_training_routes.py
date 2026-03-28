"""Add training_routes table (#508).

Revision ID: c043
Revises: c042
"""

import sqlalchemy as sa
from alembic import op

revision = "c043"
down_revision = "c042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_routes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("elevation_gain_m", sa.Float(), server_default="0", nullable=False),
        sa.Column("elevation_loss_m", sa.Float(), server_default="0", nullable=False),
        sa.Column("location_name", sa.String(200), nullable=True),
        sa.Column("surface_json", sa.Text(), nullable=True),
        sa.Column("waypoints_json", sa.Text(), nullable=False),
        sa.Column("route_segments_json", sa.Text(), nullable=True),
        sa.Column("pacing_strategy", sa.String(50), nullable=True),
        sa.Column(
            "linked_session_template_id",
            sa.Integer(),
            sa.ForeignKey("session_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_training_routes_id", "training_routes", ["id"])
    op.create_index("ix_training_routes_is_favorite", "training_routes", ["is_favorite"])


def downgrade() -> None:
    op.drop_index("ix_training_routes_is_favorite", table_name="training_routes")
    op.drop_index("ix_training_routes_id", table_name="training_routes")
    op.drop_table("training_routes")
