"""Migrate strength exercise details from day.notes to session.notes.

The plan generator originally stored strength exercise details (e.g.
"Kniebeugen 2x6@16kg, Bankdruecken 2x6@18kg") in day-level notes
instead of session-level notes. This migration moves them to the
correct location in both:
  1. Phase template JSON (training_phases.weekly_template_json / weekly_templates_json)
  2. Generated weekly plans (weekly_plan_days.notes → planned_sessions.notes)

Revision ID: c024
Revises: c023
"""

import json

import sqlalchemy as sa

from alembic import op

revision = "c024"
down_revision = "c023"
branch_labels = None
depends_on = None


def _migrate_template_json(raw_json: str) -> tuple[str, bool]:
    """Migrate a single weekly_template_json blob.

    For each day that has a strength session AND day.notes is set
    but the session has no notes → move day.notes to session.notes.

    Returns (new_json, changed).
    """
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return raw_json, False

    days = data.get("days", [])
    changed = False

    for day in days:
        day_notes = day.get("notes")
        if not day_notes:
            continue

        sessions = day.get("sessions", [])
        # Find first strength session with no notes
        for session in sessions:
            if session.get("training_type") == "strength" and not session.get("notes"):
                session["notes"] = day_notes
                day["notes"] = None
                changed = True
                break  # Only move to first strength session

    if changed:
        return json.dumps(data), True
    return raw_json, False


def _migrate_templates_json(raw_json: str) -> tuple[str, bool]:
    """Migrate weekly_templates_json (per-week variants)."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return raw_json, False

    weeks = data.get("weeks", {})
    any_changed = False

    for week_key, template in weeks.items():
        new_json, changed = _migrate_template_json(json.dumps(template))
        if changed:
            weeks[week_key] = json.loads(new_json)
            any_changed = True

    if any_changed:
        return json.dumps(data), True
    return raw_json, False


def upgrade() -> None:
    """Move strength details from day.notes to session.notes."""
    conn = op.get_bind()

    # --- 1. Fix phase template JSON ---
    phases = conn.execute(
        sa.text(
            "SELECT id, weekly_template_json, weekly_templates_json "
            "FROM training_phases"
        )
    ).fetchall()

    for phase in phases:
        phase_id, tmpl_json, tmpls_json = phase

        if tmpl_json:
            new_json, changed = _migrate_template_json(tmpl_json)
            if changed:
                conn.execute(
                    sa.text(
                        "UPDATE training_phases "
                        "SET weekly_template_json = :json "
                        "WHERE id = :id"
                    ),
                    {"json": new_json, "id": phase_id},
                )

        if tmpls_json:
            new_json, changed = _migrate_templates_json(tmpls_json)
            if changed:
                conn.execute(
                    sa.text(
                        "UPDATE training_phases "
                        "SET weekly_templates_json = :json "
                        "WHERE id = :id"
                    ),
                    {"json": new_json, "id": phase_id},
                )

    # --- 2. Fix generated weekly plan data ---
    # Find days that have notes and contain a strength session without notes
    days_with_notes = conn.execute(
        sa.text(
            "SELECT d.id, d.notes "
            "FROM weekly_plan_days d "
            "WHERE d.notes IS NOT NULL AND d.notes != ''"
        )
    ).fetchall()

    for day in days_with_notes:
        day_id, day_notes = day

        # Check if this day has a strength session without notes
        strength_session = conn.execute(
            sa.text(
                "SELECT id FROM planned_sessions "
                "WHERE day_id = :day_id "
                "  AND training_type = 'strength' "
                "  AND (notes IS NULL OR notes = '') "
                "ORDER BY position "
                "LIMIT 1"
            ),
            {"day_id": day_id},
        ).fetchone()

        if strength_session:
            session_id = strength_session[0]
            # Move day.notes → session.notes
            conn.execute(
                sa.text(
                    "UPDATE planned_sessions SET notes = :notes WHERE id = :id"
                ),
                {"notes": day_notes, "id": session_id},
            )
            conn.execute(
                sa.text(
                    "UPDATE weekly_plan_days SET notes = NULL WHERE id = :id"
                ),
                {"id": day_id},
            )


def downgrade() -> None:
    """Move strength details back from session.notes to day.notes.

    This is a best-effort reverse — only moves back for strength sessions
    where the day currently has no notes.
    """
    conn = op.get_bind()

    # Reverse for weekly plan data
    strength_sessions = conn.execute(
        sa.text(
            "SELECT ps.id, ps.day_id, ps.notes "
            "FROM planned_sessions ps "
            "JOIN weekly_plan_days d ON d.id = ps.day_id "
            "WHERE ps.training_type = 'strength' "
            "  AND ps.notes IS NOT NULL AND ps.notes != '' "
            "  AND (d.notes IS NULL OR d.notes = '')"
        )
    ).fetchall()

    for sess in strength_sessions:
        sess_id, day_id, notes = sess
        conn.execute(
            sa.text("UPDATE weekly_plan_days SET notes = :notes WHERE id = :id"),
            {"notes": notes, "id": day_id},
        )
        conn.execute(
            sa.text("UPDATE planned_sessions SET notes = NULL WHERE id = :id"),
            {"id": sess_id},
        )
