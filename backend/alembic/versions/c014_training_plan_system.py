"""Add training_plans, training_phases tables; extend race_goals and workouts.

Covers stories S07-S10 (#96-#99):
- S07: TrainingPlan entity (periodisierter Trainingsplan)
- S08: TrainingPhase entity (Phasen im Plan)
- S09: Goal <-> TrainingPlan bidirektionale Verknuepfung
- S10: Soll/Ist-Link (planned_entry_id auf workouts)

Revision ID: c014
Revises: c013
Create Date: 2026-03-01
"""

import sqlalchemy as sa

from alembic import op

revision = "c014"
down_revision = "c013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_plans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("goal_id", sa.Integer, nullable=True),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("target_event_date", sa.Date, nullable=True),
        sa.Column("weekly_structure_json", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_training_plans_id", "training_plans", ["id"])
    op.create_index("ix_training_plans_status", "training_plans", ["status"])

    op.create_table(
        "training_phases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("training_plan_id", sa.Integer, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phase_type", sa.String(30), nullable=False),
        sa.Column("start_week", sa.Integer, nullable=False),
        sa.Column("end_week", sa.Integer, nullable=False),
        sa.Column("focus_json", sa.Text, nullable=True),
        sa.Column("target_metrics_json", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_training_phases_id", "training_phases", ["id"])
    op.create_index(
        "ix_training_phases_plan_id", "training_phases", ["training_plan_id"]
    )

    # S09: Goal <-> Plan link
    op.add_column(
        "race_goals", sa.Column("training_plan_id", sa.Integer, nullable=True)
    )

    # S10: Soll/Ist link
    op.add_column(
        "workouts", sa.Column("planned_entry_id", sa.Integer, nullable=True)
    )


def downgrade() -> None:
    op.drop_column("workouts", "planned_entry_id")
    op.drop_column("race_goals", "training_plan_id")
    op.drop_index("ix_training_phases_plan_id", "training_phases")
    op.drop_index("ix_training_phases_id", "training_phases")
    op.drop_table("training_phases")
    op.drop_index("ix_training_plans_status", "training_plans")
    op.drop_index("ix_training_plans_id", "training_plans")
    op.drop_table("training_plans")
