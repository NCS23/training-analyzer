"""Ziel-Validierung und Warnsystem für den KI-Chat.

Prüft ob ein Wettkampfziel realistisch ist basierend auf dem aktuellen
Fitness-Level des Athleten. Gibt Warnungen und Alternativen zurück.

Abhängigkeiten:
- vdot_calculator.py (S01, #541) — VDOT-Schätzung + is_goal_realistic()
- athlete_fitness.py (S02, #555) — FitnessProfile
"""

from __future__ import annotations

from typing import Optional

from app.services.vdot_calculator import (
    GoalCategory,
    equivalent_race_time,
    is_goal_realistic,
)


def validate_goal(
    current_vdot: Optional[float],
    goal_distance_km: float,
    goal_time_seconds: int,
) -> GoalValidationResult:
    """Validiere ein Wettkampfziel gegen das aktuelle Fitness-Level.

    Args:
        current_vdot: VDOT des Athleten (None wenn unbekannt).
        goal_distance_km: Zieldistanz in km.
        goal_time_seconds: Zielzeit in Sekunden.

    Returns:
        GoalValidationResult mit Warnung, Alternative und Empfehlung.
    """
    if current_vdot is None:
        return GoalValidationResult(
            valid=True,
            category="unknown",
            message=(
                "Dein Fitness-Level konnte nicht ermittelt werden. "
                "Lade Trainings-Sessions hoch oder führe einen Schwellentest durch, "
                "damit ich dein Ziel besser bewerten kann."
            ),
        )

    assessment = is_goal_realistic(current_vdot, goal_distance_km, goal_time_seconds)

    return GoalValidationResult(
        valid=assessment.category != GoalCategory.UNREALISTIC,
        category=assessment.category.value,
        message=assessment.message,
        current_vdot=assessment.current_vdot,
        required_vdot=assessment.required_vdot,
        suggested_time_seconds=assessment.suggested_time_seconds,
        suggested_time_formatted=_format_time(assessment.suggested_time_seconds),
    )


class GoalValidationResult:
    """Ergebnis der Ziel-Validierung für den Chat."""

    def __init__(
        self,
        valid: bool,
        category: str,
        message: str,
        current_vdot: Optional[float] = None,
        required_vdot: Optional[float] = None,
        suggested_time_seconds: Optional[int] = None,
        suggested_time_formatted: Optional[str] = None,
    ) -> None:
        self.valid = valid
        self.category = category
        self.message = message
        self.current_vdot = current_vdot
        self.required_vdot = required_vdot
        self.suggested_time_seconds = suggested_time_seconds
        self.suggested_time_formatted = suggested_time_formatted

    def to_dict(self) -> dict:
        """Konvertiere zu Dict für Chat-Tool-Response."""
        result: dict = {
            "valid": self.valid,
            "category": self.category,
            "message": self.message,
        }
        if self.current_vdot is not None:
            result["current_vdot"] = round(self.current_vdot, 1)
        if self.required_vdot is not None:
            result["required_vdot"] = round(self.required_vdot, 1)
        if self.suggested_time_formatted:
            result["suggested_time"] = self.suggested_time_formatted
        return result

    def to_chat_warning(self) -> Optional[str]:
        """Generiere eine Warnung für den Chat (None wenn kein Problem)."""
        if self.category == "realistic":
            return None
        if self.category == "unknown":
            return self.message

        warning = f"⚠️ **Ziel-Bewertung: {self.category.title()}**\n\n{self.message}"

        if self.suggested_time_formatted and self.category == "unrealistic":
            warning += (
                f"\n\n💡 **Empfehlung:** Eine realistischere Zielzeit wäre "
                f"**{self.suggested_time_formatted}** basierend auf deinem aktuellen Niveau."
            )

        return warning


def validate_goal_for_plan(
    current_vdot: Optional[float],
    goal_distance_km: Optional[float],
    goal_time_seconds: Optional[int],
) -> Optional[str]:
    """Validiere Ziel im Kontext der Plan-Erstellung.

    Wird automatisch von handle_generate_training_plan aufgerufen.
    Gibt einen Warnungs-String zurück oder None wenn alles ok.

    Args:
        current_vdot: VDOT des Athleten.
        goal_distance_km: Zieldistanz.
        goal_time_seconds: Zielzeit.

    Returns:
        Warnungstext oder None.
    """
    if not goal_distance_km or not goal_time_seconds:
        return None

    result = validate_goal(current_vdot, goal_distance_km, goal_time_seconds)
    return result.to_chat_warning()


def get_equivalent_times(vdot: float) -> dict[str, str]:
    """Berechne äquivalente Wettkampfzeiten für gängige Distanzen.

    Nützlich für den Chat: "Was kann ich aktuell auf 5K, 10K, HM, Marathon?"

    Args:
        vdot: VDOT-Wert.

    Returns:
        Dict mit Distanz-Label → formatierte Zeit.
    """
    distances = {
        "5K": 5.0,
        "10K": 10.0,
        "Halbmarathon": 21.0975,
        "Marathon": 42.195,
    }
    result: dict[str, str] = {}
    for label, km in distances.items():
        time_sec = equivalent_race_time(vdot, km)
        if time_sec:
            formatted = _format_time(time_sec)
            if formatted:
                result[label] = formatted
    return result


def _format_time(seconds: Optional[int]) -> Optional[str]:
    """Formatiere Sekunden als H:MM:SS oder M:SS."""
    if seconds is None:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
