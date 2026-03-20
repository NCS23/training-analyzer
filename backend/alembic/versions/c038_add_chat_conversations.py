"""Chat-Konversationen und Nachrichten fuer KI-Trainingsplan-Assistent.

Revision ID: c038
Revises: c037
Create Date: 2026-03-20
"""

import sqlalchemy as sa

from alembic import op

revision = "c038"
down_revision = "c037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "conversation_id",
            sa.Integer,
            sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")
