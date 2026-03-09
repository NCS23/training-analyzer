"""Ensure segments[] exists in all run_details JSON data.

Every RunDetails now uses segments as single source of truth.
This migration backfills existing JSON data so that run_details
always contains a segments array, even for simple single-segment runs.

Tables updated:
- planned_sessions.run_details_json
- session_templates.run_details_json
- training_phases.weekly_template_json / weekly_templates_json

No schema change — only JSON data update.

Revision ID: c026
Revises: c025
"""

import json
import logging

import sqlalchemy as sa

from alembic import op

revision = "c026"
down_revision = "c025"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def _ensure_segments_in_run_details(rd: dict) -> dict:
    """Add segments[] to a run_details dict if missing."""
    if not isinstance(rd, dict):
        return rd

    segments = rd.get("segments")
    if segments and isinstance(segments, list) and len(segments) > 0:
        # Already has segments — nothing to do
        return rd

    # Build a steady segment from top-level fields
    segment: dict = {
        "position": 0,
        "segment_type": "steady",
        "repeats": 1,
        "target_duration_minutes": rd.get("target_duration_minutes"),
        "target_pace_min": rd.get("target_pace_min"),
        "target_pace_max": rd.get("target_pace_max"),
        "target_hr_min": rd.get("target_hr_min"),
        "target_hr_max": rd.get("target_hr_max"),
        "target_distance_km": None,
        "notes": None,
    }
    rd["segments"] = [segment]
    return rd


def _ensure_segments_in_phase_template(template_json: str) -> str:
    """Walk through a PhaseWeeklyTemplate JSON and ensure segments in run_details."""
    data = json.loads(template_json)
    if not isinstance(data, dict):
        return template_json

    days = data.get("days", [])
    changed = False
    for day in days:
        # Multi-session format: day.sessions[].run_details
        for session in day.get("sessions", []):
            rd = session.get("run_details")
            if rd and isinstance(rd, dict):
                updated = _ensure_segments_in_run_details(rd)
                session["run_details"] = updated
                changed = True

        # Legacy flat format: day.run_details
        rd = day.get("run_details")
        if rd and isinstance(rd, dict):
            updated = _ensure_segments_in_run_details(rd)
            day["run_details"] = updated
            changed = True

    if changed:
        return json.dumps(data)
    return template_json


def upgrade() -> None:
    """Backfill segments in all run_details JSON."""
    conn = op.get_bind()

    # 1. planned_sessions.run_details_json
    rows = conn.execute(
        sa.text("SELECT id, run_details_json FROM planned_sessions WHERE run_details_json IS NOT NULL")
    ).fetchall()
    updated = 0
    for row in rows:
        try:
            rd = json.loads(row[1])
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(rd, dict):
            continue
        old_segments = rd.get("segments")
        if old_segments and isinstance(old_segments, list) and len(old_segments) > 0:
            continue
        rd = _ensure_segments_in_run_details(rd)
        conn.execute(
            sa.text("UPDATE planned_sessions SET run_details_json = :json WHERE id = :id"),
            {"json": json.dumps(rd), "id": row[0]},
        )
        updated += 1
    logger.info("planned_sessions: updated %d rows with segments", updated)

    # 2. session_templates.run_details_json
    rows = conn.execute(
        sa.text("SELECT id, run_details_json FROM session_templates WHERE run_details_json IS NOT NULL")
    ).fetchall()
    updated = 0
    for row in rows:
        try:
            rd = json.loads(row[1])
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(rd, dict):
            continue
        old_segments = rd.get("segments")
        if old_segments and isinstance(old_segments, list) and len(old_segments) > 0:
            continue
        rd = _ensure_segments_in_run_details(rd)
        conn.execute(
            sa.text("UPDATE session_templates SET run_details_json = :json WHERE id = :id"),
            {"json": json.dumps(rd), "id": row[0]},
        )
        updated += 1
    logger.info("session_templates: updated %d rows with segments", updated)

    # 3. training_phases.weekly_template_json
    rows = conn.execute(
        sa.text("SELECT id, weekly_template_json FROM training_phases WHERE weekly_template_json IS NOT NULL")
    ).fetchall()
    updated = 0
    for row in rows:
        try:
            new_json = _ensure_segments_in_phase_template(row[1])
        except (json.JSONDecodeError, TypeError):
            continue
        if new_json != row[1]:
            conn.execute(
                sa.text("UPDATE training_phases SET weekly_template_json = :json WHERE id = :id"),
                {"json": new_json, "id": row[0]},
            )
            updated += 1
    logger.info("training_phases.weekly_template_json: updated %d rows", updated)

    # 4. training_phases.weekly_templates_json (per-week overrides)
    rows = conn.execute(
        sa.text("SELECT id, weekly_templates_json FROM training_phases WHERE weekly_templates_json IS NOT NULL")
    ).fetchall()
    updated = 0
    for row in rows:
        try:
            templates = json.loads(row[1])
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(templates, dict):
            continue
        changed = False
        # Structure: { "weeks": { "1": { "days": [...] }, "2": { ... } } }
        weeks = templates.get("weeks", {})
        for week_key, week_template in weeks.items():
            if not isinstance(week_template, dict):
                continue
            old_json = json.dumps(week_template)
            new_json = _ensure_segments_in_phase_template(old_json)
            if new_json != old_json:
                weeks[week_key] = json.loads(new_json)
                changed = True
        if changed:
            conn.execute(
                sa.text("UPDATE training_phases SET weekly_templates_json = :json WHERE id = :id"),
                {"json": json.dumps(templates), "id": row[0]},
            )
            updated += 1
    logger.info("training_phases.weekly_templates_json: updated %d rows", updated)


def downgrade() -> None:
    """No-op: segments are always valid, removing them would lose data."""
    pass
