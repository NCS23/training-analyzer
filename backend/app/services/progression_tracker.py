"""Krafttraining Progression-Tracking Service (Issue #17).

Analysiert Krafttraining-Sessions und berechnet:
- Gewichtsverlauf pro Uebung
- Persoenliche Bestleistungen (PRs)
- Tonnage-Trends pro Woche
"""

from datetime import datetime, timedelta
from typing import Any


def get_exercise_history(
    exercise_name: str,
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extrahiert die Historie einer Uebung aus allen Strength-Sessions.

    Args:
        exercise_name: Name der Uebung (case-insensitive)
        sessions: Liste von Session-Dicts mit keys: id, date, exercises_json

    Returns:
        Chronologisch sortierte Liste von Datenpunkten
    """
    history: list[dict[str, Any]] = []
    name_lower = exercise_name.lower()

    for session in sessions:
        exercises_raw = session.get("exercises", [])
        if not exercises_raw:
            continue

        for ex in exercises_raw:
            if ex["name"].lower() != name_lower:
                continue

            sets = ex.get("sets", [])
            if not sets:
                continue

            total_reps = 0
            total_sets = len(sets)
            completed_sets = 0
            tonnage = 0.0
            max_weight = 0.0
            best_set_weight = 0.0
            best_set_reps = 0

            for s in sets:
                status = s.get("status", "completed")
                reps = s.get("reps", 0)
                weight = s.get("weight_kg", 0.0)

                if status in ("completed", "reduced"):
                    completed_sets += 1
                    total_reps += reps
                    tonnage += reps * weight

                    if weight > max_weight:
                        max_weight = weight
                    if weight > best_set_weight or (
                        weight == best_set_weight and reps > best_set_reps
                    ):
                        best_set_weight = weight
                        best_set_reps = reps

            history.append(
                {
                    "date": session["date"],
                    "session_id": session["id"],
                    "max_weight_kg": max_weight,
                    "total_reps": total_reps,
                    "total_sets": total_sets,
                    "completed_sets": completed_sets,
                    "tonnage_kg": round(tonnage, 1),
                    "best_set_weight_kg": best_set_weight,
                    "best_set_reps": best_set_reps,
                }
            )

    # Sort by date
    history.sort(key=lambda x: x["date"])
    return history


def detect_personal_records(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Erkennt persoenliche Bestleistungen ueber alle Uebungen.

    PR-Typen:
    - max_weight: Hoechstes Gewicht in einem Satz
    - max_volume_set: Bester Satz (Gewicht x Reps)
    - max_tonnage_session: Hoechste Tonnage in einer Session fuer diese Uebung

    Args:
        sessions: Liste von Session-Dicts mit keys: id, date, exercises_json

    Returns:
        Liste von PR-Dicts
    """
    # Track bests per exercise
    exercise_bests: dict[str, dict[str, Any]] = {}

    for session in sorted(sessions, key=lambda s: s["date"]):
        exercises_raw = session.get("exercises", [])
        if not exercises_raw:
            continue

        for ex in exercises_raw:
            name = ex["name"]
            name_key = name.lower()
            sets = ex.get("sets", [])

            if name_key not in exercise_bests:
                exercise_bests[name_key] = {
                    "name": name,
                    "max_weight": 0.0,
                    "max_weight_date": None,
                    "max_weight_session_id": None,
                    "max_weight_detail": None,
                    "max_volume_set": 0.0,
                    "max_volume_set_date": None,
                    "max_volume_set_session_id": None,
                    "max_volume_set_detail": None,
                    "max_tonnage": 0.0,
                    "max_tonnage_date": None,
                    "max_tonnage_session_id": None,
                }

            bests = exercise_bests[name_key]
            tonnage = 0.0

            for s in sets:
                status = s.get("status", "completed")
                if status == "skipped":
                    continue

                reps = s.get("reps", 0)
                weight = s.get("weight_kg", 0.0)
                tonnage += reps * weight
                volume_set = reps * weight

                # Max weight PR
                if weight > bests["max_weight"]:
                    bests["max_weight"] = weight
                    bests["max_weight_date"] = session["date"]
                    bests["max_weight_session_id"] = session["id"]
                    bests["max_weight_detail"] = f"{weight}kg x {reps}"

                # Max volume set PR (single set: reps * weight)
                if volume_set > bests["max_volume_set"]:
                    bests["max_volume_set"] = volume_set
                    bests["max_volume_set_date"] = session["date"]
                    bests["max_volume_set_session_id"] = session["id"]
                    bests["max_volume_set_detail"] = (
                        f"{weight}kg x {reps} = {round(volume_set, 1)}kg"
                    )

            # Max tonnage session PR
            if tonnage > bests["max_tonnage"]:
                bests["max_tonnage"] = round(tonnage, 1)
                bests["max_tonnage_date"] = session["date"]
                bests["max_tonnage_session_id"] = session["id"]

    # Build PR list
    records: list[dict[str, Any]] = []
    for bests in exercise_bests.values():
        if bests["max_weight"] > 0 and bests["max_weight_date"]:
            records.append(
                {
                    "exercise_name": bests["name"],
                    "record_type": "max_weight",
                    "value": bests["max_weight"],
                    "unit": "kg",
                    "date": bests["max_weight_date"],
                    "session_id": bests["max_weight_session_id"],
                    "detail": bests["max_weight_detail"],
                }
            )
        if bests["max_volume_set"] > 0 and bests["max_volume_set_date"]:
            records.append(
                {
                    "exercise_name": bests["name"],
                    "record_type": "max_volume_set",
                    "value": bests["max_volume_set"],
                    "unit": "kg",
                    "date": bests["max_volume_set_date"],
                    "session_id": bests["max_volume_set_session_id"],
                    "detail": bests["max_volume_set_detail"],
                }
            )
        if bests["max_tonnage"] > 0 and bests["max_tonnage_date"]:
            records.append(
                {
                    "exercise_name": bests["name"],
                    "record_type": "max_tonnage_session",
                    "value": bests["max_tonnage"],
                    "unit": "kg",
                    "date": bests["max_tonnage_date"],
                    "session_id": bests["max_tonnage_session_id"],
                }
            )

    return records


def calculate_weekly_tonnage(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Berechnet die woechentliche Tonnage ueber alle Strength-Sessions.

    Args:
        sessions: Liste von Session-Dicts mit keys: id, date, exercises_json

    Returns:
        Woechentlich aggregierte Tonnage-Daten
    """
    weeks: dict[str, dict[str, Any]] = {}

    for session in sessions:
        exercises_raw = session.get("exercises", [])
        if not exercises_raw:
            continue

        session_date = session["date"]
        if isinstance(session_date, str):
            dt = datetime.strptime(session_date, "%Y-%m-%d")
        else:
            dt = session_date

        week_key = dt.strftime("%G-W%V")
        week_start = dt - timedelta(days=dt.weekday())

        if week_key not in weeks:
            weeks[week_key] = {
                "week": week_key,
                "week_start": week_start.strftime("%Y-%m-%d"),
                "total_tonnage_kg": 0.0,
                "session_count": 0,
                "exercise_names": set(),
            }

        w = weeks[week_key]
        w["session_count"] += 1

        for ex in exercises_raw:
            w["exercise_names"].add(ex["name"])
            for s in ex.get("sets", []):
                if s.get("status", "completed") != "skipped":
                    w["total_tonnage_kg"] += s.get("reps", 0) * s.get("weight_kg", 0.0)

    # Build result (convert sets to counts, sort by week)
    result = []
    for week_key in sorted(weeks.keys()):
        w = weeks[week_key]
        result.append(
            {
                "week": w["week"],
                "week_start": w["week_start"],
                "total_tonnage_kg": round(w["total_tonnage_kg"], 1),
                "session_count": w["session_count"],
                "exercise_count": len(w["exercise_names"]),
            }
        )

    return result


def get_all_exercise_names(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sammelt alle Uebungsnamen mit Metadaten aus allen Sessions.

    Returns:
        Liste von Uebungen mit name, category, session_count, last_date, last_max_weight
    """
    exercises: dict[str, dict[str, Any]] = {}

    for session in sorted(sessions, key=lambda s: s["date"]):
        exercises_raw = session.get("exercises", [])
        if not exercises_raw:
            continue

        for ex in exercises_raw:
            name_key = ex["name"].lower()
            if name_key not in exercises:
                exercises[name_key] = {
                    "name": ex["name"],
                    "category": ex.get("category", ""),
                    "session_count": 0,
                    "last_date": session["date"],
                    "last_max_weight_kg": 0.0,
                }

            entry = exercises[name_key]
            entry["session_count"] += 1
            entry["last_date"] = session["date"]

            for s in ex.get("sets", []):
                if s.get("status", "completed") != "skipped":
                    weight = s.get("weight_kg", 0.0)
                    if weight > entry["last_max_weight_kg"]:
                        entry["last_max_weight_kg"] = weight

    # Sort by session count (most used first)
    return sorted(exercises.values(), key=lambda x: x["session_count"], reverse=True)
