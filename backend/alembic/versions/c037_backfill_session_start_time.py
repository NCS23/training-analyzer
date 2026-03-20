"""Backfill echte Startzeit aus hr_timeseries_json in date-Spalte.

Sessions wurden bisher immer mit 00:00 gespeichert, obwohl FIT-Dateien
eine echte Startzeit enthalten. Diese Migration liest den ersten Timestamp
aus hr_timeseries_json und aktualisiert die date-Spalte.

Revision ID: c037
Revises: c036
Create Date: 2026-03-20
"""

import json
from datetime import datetime

import sqlalchemy as sa

from alembic import op

revision = "c037"
down_revision = "c036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, date, hr_timeseries_json FROM workouts WHERE hr_timeseries_json IS NOT NULL"
        )
    ).fetchall()

    for row in rows:
        workout_id, current_date, ts_json = row
        if not ts_json:
            continue

        # Nur Sessions mit 00:00 Uhrzeit korrigieren
        if isinstance(current_date, datetime) and (
            current_date.hour != 0 or current_date.minute != 0
        ):
            continue

        try:
            timeseries = json.loads(ts_json)
            if not timeseries:
                continue

            first_ts = timeseries[0].get("timestamp")
            if not first_ts:
                continue

            parsed_dt = datetime.fromisoformat(first_ts)
            # Uhrzeit aus Timeseries auf bestehendes Datum setzen
            base_date = (
                current_date
                if isinstance(current_date, datetime)
                else datetime.combine(current_date, datetime.min.time())
            )
            new_date = base_date.replace(
                hour=parsed_dt.hour,
                minute=parsed_dt.minute,
                second=parsed_dt.second,
            )

            conn.execute(
                sa.text("UPDATE workouts SET date = :new_date WHERE id = :id"),
                {"new_date": new_date, "id": workout_id},
            )
        except (json.JSONDecodeError, ValueError, KeyError, IndexError):
            continue


def downgrade() -> None:
    # Nicht reversibel — Uhrzeit kann nicht wieder auf 00:00 gesetzt werden
    # ohne Information zu verlieren
    pass
