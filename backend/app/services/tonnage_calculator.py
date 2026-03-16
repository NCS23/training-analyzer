"""Volumen-Metriken fuer Krafttraining-Sessions.

Berechnet typ-differenzierte Metriken für alle 8 Set-Typen:
- weight_reps, weighted_bodyweight: Tonnage (reps × weight)
- bodyweight_reps, assisted_bodyweight: Gesamt-Reps
- duration, weight_duration: Time Under Tension (Sekunden)
- distance_duration, weight_distance: Distanz (Meter)

Zusätzlich: sRPE (Session-RPE × Dauer) als universelle Metrik.
"""

from typing import Any

# Set-Typen die zur Tonnage-Berechnung beitragen
WEIGHTED_TYPES = {"weight_reps", "weighted_bodyweight"}

# Set-Typen die rein rep-basiert sind
REP_BASED_TYPES = {"bodyweight_reps", "assisted_bodyweight"}

# Set-Typen die zeitbasiert sind
DURATION_TYPES = {"duration", "weight_duration"}

# Set-Typen die distanzbasiert sind
DISTANCE_TYPES = {"distance_duration", "weight_distance"}


def _is_active_set(s: dict[str, Any]) -> bool:
    """Prüft ob ein Set aktiv ist (completed oder reduced, nicht skipped)."""
    return s.get("status", "completed") in ("completed", "reduced")


def _get_set_type(s: dict[str, Any]) -> str:
    """Gibt den Set-Typ zurück (Backward Compat: default weight_reps)."""
    return s.get("type", "weight_reps")


def calculate_strength_metrics(exercises: list[dict[str, Any]]) -> dict[str, Any]:
    """Berechnet typ-differenzierte Metriken aus exercises_json Daten.

    Returns:
        Dict mit total_exercises, total_sets, completed_sets,
        total_tonnage_kg, total_reps, total_duration_sec, total_distance_m
    """
    total_sets = 0
    completed_sets = 0
    total_tonnage = 0.0
    total_reps = 0
    total_duration_sec = 0
    total_distance_m = 0.0

    for exercise in exercises:
        for s in exercise.get("sets", []):
            total_sets += 1
            if not _is_active_set(s):
                continue

            completed_sets += 1
            set_type = _get_set_type(s)

            if set_type in WEIGHTED_TYPES:
                total_tonnage += s.get("reps", 0) * s.get("weight_kg", 0)
            elif set_type in REP_BASED_TYPES:
                total_reps += s.get("reps", 0)
            elif set_type in DURATION_TYPES:
                total_duration_sec += s.get("duration_sec", 0)
            elif set_type in DISTANCE_TYPES:
                total_distance_m += s.get("distance_m", 0)

    return {
        "total_exercises": len(exercises),
        "total_sets": total_sets,
        "total_tonnage_kg": round(total_tonnage, 1),
        "total_reps": total_reps,
        "total_duration_sec": total_duration_sec,
        "total_distance_m": round(total_distance_m, 1),
        "completed_sets": completed_sets,
    }


def calculate_srpe(rpe: int | None, duration_minutes: int | None) -> int | None:
    """Berechnet sRPE (Session-RPE × Dauer in Minuten) = Arbitrary Units.

    Universelle Belastungsmetrik über alle Übungstypen hinweg.
    """
    if rpe is not None and duration_minutes is not None:
        return rpe * duration_minutes
    return None


def calculate_category_tonnage(exercises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Berechnet Tonnage aufgeschluesselt nach Kategorie (push/pull/legs/core/...).

    Berücksichtigt nur gewichtete Set-Typen für Tonnage.
    """
    categories: dict[str, dict[str, Any]] = {}

    for exercise in exercises:
        cat = exercise.get("category", "other")
        if cat not in categories:
            categories[cat] = {
                "category": cat,
                "tonnage_kg": 0.0,
                "exercise_count": 0,
                "set_count": 0,
            }
        categories[cat]["exercise_count"] += 1
        for s in exercise.get("sets", []):
            categories[cat]["set_count"] += 1
            if _is_active_set(s):
                set_type = _get_set_type(s)
                if set_type in WEIGHTED_TYPES:
                    categories[cat]["tonnage_kg"] += s.get("reps", 0) * s.get("weight_kg", 0)

    result = list(categories.values())
    for entry in result:
        entry["tonnage_kg"] = round(entry["tonnage_kg"], 1)
    return sorted(result, key=lambda x: x["tonnage_kg"], reverse=True)
