"""Tonnage und Metriken fuer Krafttraining-Sessions."""

from typing import Any


def calculate_strength_metrics(exercises: list[dict[str, Any]]) -> dict[str, Any]:
    """Berechnet Tonnage, Exercise-Count, Set-Count aus exercises_json Daten.

    Args:
        exercises: Liste von Exercise-Dicts (wie in exercises_json gespeichert)

    Returns:
        Dict mit total_exercises, total_sets, total_tonnage_kg, completed_sets
    """
    total_sets = 0
    completed_sets = 0
    total_tonnage = 0.0

    for exercise in exercises:
        for s in exercise.get("sets", []):
            total_sets += 1
            status = s.get("status", "completed")
            if status in ("completed", "reduced"):
                completed_sets += 1
                total_tonnage += s.get("reps", 0) * s.get("weight_kg", 0)

    return {
        "total_exercises": len(exercises),
        "total_sets": total_sets,
        "total_tonnage_kg": round(total_tonnage, 1),
        "completed_sets": completed_sets,
    }
