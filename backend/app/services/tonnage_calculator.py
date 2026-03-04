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


def calculate_category_tonnage(exercises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Berechnet Tonnage aufgeschluesselt nach Kategorie (push/pull/legs/core/...).

    Args:
        exercises: Liste von Exercise-Dicts (wie in exercises_json gespeichert)

    Returns:
        Sortierte Liste von Dicts mit category, tonnage_kg, exercise_count, set_count.
        Sortierung: absteigend nach tonnage_kg.
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
            status = s.get("status", "completed")
            if status in ("completed", "reduced"):
                categories[cat]["tonnage_kg"] += s.get("reps", 0) * s.get("weight_kg", 0)

    result = list(categories.values())
    for entry in result:
        entry["tonnage_kg"] = round(entry["tonnage_kg"], 1)
    return sorted(result, key=lambda x: x["tonnage_kg"], reverse=True)
