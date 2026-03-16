"""Krafttraining Progression-Tracking Service (Issue #17, #285).

Analysiert Krafttraining-Sessions und berechnet:
- Gewichtsverlauf pro Uebung (typ-differenziert)
- Persoenliche Bestleistungen (PRs) pro Set-Typ
- Tonnage-Trends pro Woche
"""

from datetime import datetime, timedelta
from typing import Any

from app.services.tonnage_calculator import (
    DISTANCE_TYPES,
    DURATION_TYPES,
    REP_BASED_TYPES,
    WEIGHTED_TYPES,
    _get_set_type,
    _is_active_set,
)


def _detect_exercise_set_type(exercise: dict[str, Any]) -> str:
    """Ermittelt den dominanten Set-Typ einer Übung."""
    sets = exercise.get("sets", [])
    if not sets:
        return "weight_reps"
    type_counts: dict[str, int] = {}
    for s in sets:
        t = _get_set_type(s)
        type_counts[t] = type_counts.get(t, 0) + 1
    return max(type_counts, key=lambda t: type_counts[t])


def _accumulate_set_metrics(s: dict[str, Any], acc: dict[str, Any]) -> None:
    """Akkumuliert Metriken eines aktiven Sets in den Accumulator."""
    set_type = _get_set_type(s)
    reps = s.get("reps", 0)
    weight = s.get("weight_kg", 0.0)

    if set_type in WEIGHTED_TYPES:
        acc["total_reps"] += reps
        acc["tonnage"] += reps * weight
        acc["max_weight"] = max(acc["max_weight"], weight)
        if weight > acc["best_set_weight"] or (
            weight == acc["best_set_weight"] and reps > acc["best_set_reps"]
        ):
            acc["best_set_weight"] = weight
            acc["best_set_reps"] = reps
    elif set_type in REP_BASED_TYPES:
        acc["total_reps"] += reps
    elif set_type in DURATION_TYPES:
        acc["total_duration_sec"] += s.get("duration_sec", 0)
    elif set_type in DISTANCE_TYPES:
        acc["total_distance_m"] += s.get("distance_m", 0)


def _build_history_entry(
    session: dict[str, Any],
    exercise_type: str,
    total_sets: int,
    completed_sets: int,
    acc: dict[str, Any],
) -> dict[str, Any]:
    """Baut einen History-Eintrag aus akkumulierten Metriken."""
    entry: dict[str, Any] = {
        "date": session["date"],
        "session_id": session["id"],
        "set_type": exercise_type,
        "total_sets": total_sets,
        "completed_sets": completed_sets,
    }
    if exercise_type in WEIGHTED_TYPES:
        entry.update(
            {
                "max_weight_kg": acc["max_weight"],
                "total_reps": acc["total_reps"],
                "tonnage_kg": round(acc["tonnage"], 1),
                "best_set_weight_kg": acc["best_set_weight"],
                "best_set_reps": acc["best_set_reps"],
            }
        )
    elif exercise_type in REP_BASED_TYPES:
        entry["total_reps"] = acc["total_reps"]
    elif exercise_type in DURATION_TYPES:
        entry["total_duration_sec"] = acc["total_duration_sec"]
    elif exercise_type in DISTANCE_TYPES:
        entry["total_distance_m"] = round(acc["total_distance_m"], 1)
    return entry


def get_exercise_history(
    exercise_name: str,
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extrahiert die Historie einer Uebung aus allen Strength-Sessions."""
    history: list[dict[str, Any]] = []
    name_lower = exercise_name.lower()

    for session in sessions:
        for ex in session.get("exercises", []):
            if ex["name"].lower() != name_lower:
                continue
            sets = ex.get("sets", [])
            if not sets:
                continue

            exercise_type = _detect_exercise_set_type(ex)
            acc = {
                "total_reps": 0,
                "tonnage": 0.0,
                "max_weight": 0.0,
                "best_set_weight": 0.0,
                "best_set_reps": 0,
                "total_duration_sec": 0,
                "total_distance_m": 0.0,
            }
            completed_sets = 0
            for s in sets:
                if _is_active_set(s):
                    completed_sets += 1
                    _accumulate_set_metrics(s, acc)

            history.append(
                _build_history_entry(session, exercise_type, len(sets), completed_sets, acc)
            )

    history.sort(key=lambda x: x["date"])
    return history


def _init_exercise_bests(name: str, exercise_type: str) -> dict[str, Any]:
    """Initialisiert den Bests-Tracker für eine Übung."""
    return {
        "name": name,
        "set_type": exercise_type,
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
        "max_reps_set": 0,
        "max_reps_set_date": None,
        "max_reps_set_session_id": None,
        "max_total_reps": 0,
        "max_total_reps_date": None,
        "max_total_reps_session_id": None,
        "max_duration": 0,
        "max_duration_date": None,
        "max_duration_session_id": None,
        "max_distance": 0.0,
        "max_distance_date": None,
        "max_distance_session_id": None,
    }


def _update_weighted_bests(
    bests: dict[str, Any], s: dict[str, Any], session: dict[str, Any]
) -> float:
    """Aktualisiert gewichtete PRs und gibt volume_set zurück."""
    reps = s.get("reps", 0)
    weight = s.get("weight_kg", 0.0)
    volume_set = reps * weight
    if weight > bests["max_weight"]:
        bests["max_weight"] = weight
        bests["max_weight_date"] = session["date"]
        bests["max_weight_session_id"] = session["id"]
        bests["max_weight_detail"] = f"{weight}kg x {reps}"
    if volume_set > bests["max_volume_set"]:
        bests["max_volume_set"] = volume_set
        bests["max_volume_set_date"] = session["date"]
        bests["max_volume_set_session_id"] = session["id"]
        bests["max_volume_set_detail"] = f"{weight}kg x {reps} = {round(volume_set, 1)}kg"
    return reps * weight


def _update_rep_bests(bests: dict[str, Any], reps: int, session: dict[str, Any]) -> None:
    """Aktualisiert rep-basierte PRs."""
    if reps > bests["max_reps_set"]:
        bests["max_reps_set"] = reps
        bests["max_reps_set_date"] = session["date"]
        bests["max_reps_set_session_id"] = session["id"]


def _update_duration_bests(bests: dict[str, Any], dur: int, session: dict[str, Any]) -> None:
    """Aktualisiert Dauer-PRs."""
    if dur > bests["max_duration"]:
        bests["max_duration"] = dur
        bests["max_duration_date"] = session["date"]
        bests["max_duration_session_id"] = session["id"]


def _update_distance_bests(bests: dict[str, Any], dist: float, session: dict[str, Any]) -> None:
    """Aktualisiert Distanz-PRs."""
    if dist > bests["max_distance"]:
        bests["max_distance"] = dist
        bests["max_distance_date"] = session["date"]
        bests["max_distance_session_id"] = session["id"]


def detect_personal_records(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Erkennt persoenliche Bestleistungen ueber alle Uebungen."""
    exercise_bests: dict[str, dict[str, Any]] = {}

    for session in sorted(sessions, key=lambda s: s["date"]):
        for ex in session.get("exercises", []):
            name = ex["name"]
            name_key = name.lower()
            exercise_type = _detect_exercise_set_type(ex)

            if name_key not in exercise_bests:
                exercise_bests[name_key] = _init_exercise_bests(name, exercise_type)

            bests = exercise_bests[name_key]
            bests["set_type"] = exercise_type
            tonnage = 0.0
            session_reps = 0

            for s in ex.get("sets", []):
                if not _is_active_set(s):
                    continue
                set_type = _get_set_type(s)
                reps = s.get("reps", 0)
                if set_type in WEIGHTED_TYPES:
                    tonnage += _update_weighted_bests(bests, s, session)
                    session_reps += reps
                if set_type in REP_BASED_TYPES:
                    _update_rep_bests(bests, reps, session)
                    session_reps += reps
                if set_type in DURATION_TYPES:
                    _update_duration_bests(bests, s.get("duration_sec", 0), session)
                if set_type in DISTANCE_TYPES:
                    _update_distance_bests(bests, s.get("distance_m", 0.0), session)

            if tonnage > bests["max_tonnage"]:
                bests["max_tonnage"] = round(tonnage, 1)
                bests["max_tonnage_date"] = session["date"]
                bests["max_tonnage_session_id"] = session["id"]
            if session_reps > bests["max_total_reps"]:
                bests["max_total_reps"] = session_reps
                bests["max_total_reps_date"] = session["date"]
                bests["max_total_reps_session_id"] = session["id"]

    return _build_pr_list(exercise_bests)


def _build_pr_list(exercise_bests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Baut die PR-Liste aus den gesammelten Bests."""
    records: list[dict[str, Any]] = []
    for bests in exercise_bests.values():
        set_type = bests["set_type"]
        if set_type in WEIGHTED_TYPES:
            _append_weighted_prs(records, bests)
        if set_type in REP_BASED_TYPES:
            _append_rep_prs(records, bests)
        if set_type in DURATION_TYPES and bests["max_duration"] > 0 and bests["max_duration_date"]:
            records.append(
                {
                    "exercise_name": bests["name"],
                    "record_type": "max_duration",
                    "value": bests["max_duration"],
                    "unit": "sec",
                    "date": bests["max_duration_date"],
                    "session_id": bests["max_duration_session_id"],
                }
            )
        if set_type in DISTANCE_TYPES and bests["max_distance"] > 0 and bests["max_distance_date"]:
            records.append(
                {
                    "exercise_name": bests["name"],
                    "record_type": "max_distance",
                    "value": bests["max_distance"],
                    "unit": "m",
                    "date": bests["max_distance_date"],
                    "session_id": bests["max_distance_session_id"],
                }
            )
    return records


def _append_weighted_prs(records: list[dict[str, Any]], bests: dict[str, Any]) -> None:
    """Fügt gewichtete PRs zur Liste hinzu."""
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


def _append_rep_prs(records: list[dict[str, Any]], bests: dict[str, Any]) -> None:
    """Fügt rep-basierte PRs zur Liste hinzu."""
    if bests["max_reps_set"] > 0 and bests["max_reps_set_date"]:
        records.append(
            {
                "exercise_name": bests["name"],
                "record_type": "max_reps_set",
                "value": bests["max_reps_set"],
                "unit": "reps",
                "date": bests["max_reps_set_date"],
                "session_id": bests["max_reps_set_session_id"],
            }
        )
    if bests["max_total_reps"] > 0 and bests["max_total_reps_date"]:
        records.append(
            {
                "exercise_name": bests["name"],
                "record_type": "max_total_reps",
                "value": bests["max_total_reps"],
                "unit": "reps",
                "date": bests["max_total_reps_date"],
                "session_id": bests["max_total_reps_session_id"],
            }
        )


def calculate_weekly_tonnage(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Berechnet die woechentliche Tonnage ueber alle Strength-Sessions."""
    weeks: dict[str, dict[str, Any]] = {}

    for session in sessions:
        exercises_raw = session.get("exercises", [])
        if not exercises_raw:
            continue

        session_date = session["date"]
        dt = (
            datetime.strptime(session_date, "%Y-%m-%d")
            if isinstance(session_date, str)
            else session_date
        )
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
                if _is_active_set(s) and _get_set_type(s) in WEIGHTED_TYPES:
                    w["total_tonnage_kg"] += s.get("reps", 0) * s.get("weight_kg", 0.0)

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


def calculate_weekly_category_tonnage(
    sessions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Berechnet woechentliche Tonnage aufgeschluesselt nach Kategorie."""
    from app.services.tonnage_calculator import calculate_category_tonnage

    weeks: dict[str, dict[str, Any]] = {}

    for session in sessions:
        exercises_raw = session.get("exercises", [])
        if not exercises_raw:
            continue

        session_date = session["date"]
        dt = (
            datetime.strptime(session_date, "%Y-%m-%d")
            if isinstance(session_date, str)
            else session_date
        )
        week_key = dt.strftime("%G-W%V")
        week_start = dt - timedelta(days=dt.weekday())

        if week_key not in weeks:
            weeks[week_key] = {
                "week": week_key,
                "week_start": week_start.strftime("%Y-%m-%d"),
                "exercises": [],
            }
        weeks[week_key]["exercises"].extend(exercises_raw)

    week_results = []
    all_exercises: list[dict[str, Any]] = []
    for week_key in sorted(weeks.keys()):
        w = weeks[week_key]
        cats = calculate_category_tonnage(w["exercises"])
        total = round(sum(c["tonnage_kg"] for c in cats), 1)
        week_results.append(
            {
                "week": w["week"],
                "week_start": w["week_start"],
                "categories": cats,
                "total_tonnage_kg": total,
            }
        )
        all_exercises.extend(w["exercises"])

    aggregated = calculate_category_tonnage(all_exercises)
    grand_total = round(sum(c["tonnage_kg"] for c in aggregated), 1)

    return {
        "weeks": week_results,
        "aggregated": aggregated,
        "total_tonnage_kg": grand_total,
    }


def get_all_exercise_names(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sammelt alle Uebungsnamen mit Metadaten aus allen Sessions."""
    exercises: dict[str, dict[str, Any]] = {}

    for session in sorted(sessions, key=lambda s: s["date"]):
        for ex in session.get("exercises", []):
            name_key = ex["name"].lower()
            exercise_type = _detect_exercise_set_type(ex)

            if name_key not in exercises:
                exercises[name_key] = {
                    "name": ex["name"],
                    "category": ex.get("category", ""),
                    "set_type": exercise_type,
                    "session_count": 0,
                    "last_date": session["date"],
                    "last_max_weight_kg": 0.0,
                }

            entry = exercises[name_key]
            entry["session_count"] += 1
            entry["last_date"] = session["date"]
            entry["set_type"] = exercise_type

            for s in ex.get("sets", []):
                if _is_active_set(s):
                    entry["last_max_weight_kg"] = max(
                        entry["last_max_weight_kg"], s.get("weight_kg", 0.0)
                    )

    return sorted(exercises.values(), key=lambda x: x["session_count"], reverse=True)
