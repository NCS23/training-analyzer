"""Add users and refresh_tokens tables for auth system.

Revision ID: c045_add_users_and_refresh_tokens
Revises: c044_add_pacing_strategies
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa

revision = "c045_add_users_and_refresh_tokens"
down_revision = "c044_add_pacing_strategies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("apple_sub", sa.String(255), unique=True, nullable=True),
        sa.Column("google_sub", sa.String(255), unique=True, nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "token_hash", sa.String(255), unique=True, index=True, nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("users")
