"""80/20 Intensitätsverteilungs-Validierung (Seiler).

Prüft ob ein generierter Wochenplan die 80/20-Regel einhält:
~80% lockeres Training, ~20% intensive Einheiten.

Quelle:
- Seiler, S. (2010). What is Best Practice for Training Intensity
  and Duration Distribution in Endurance Athletes?
- Stöggl & Sperlich (2015): Polarized Training Has Greater Impact

Kategorien:
- EASY: easy, recovery, long_run → 100% locker
- MODERATE: progression, fartlek → 50% locker / 50% intensiv
- HARD: tempo, intervals, repetitions, race → 100% intensiv
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Intensitätskategorien
# ---------------------------------------------------------------------------

# Session-Typen → Intensitätskategorie
_INTENSITY_CATEGORY: dict[str, str] = {
    # Locker (100% Easy-Anteil)
    "easy": "easy",
    "recovery": "easy",
    "long_run": "easy",
    # Moderat (50/50 Mischung)
    "progression": "moderate",
    "fartlek": "moderate",
    # Intensiv (100% Hard-Anteil)
    "tempo": "hard",
    "intervals": "hard",
    "repetitions": "hard",
    "race": "hard",
    "threshold": "hard",
}

# Gewichtung für die Berechnung der Intensitätsanteile
_EASY_WEIGHT: dict[str, float] = {
    "easy": 1.0,
    "moderate": 0.5,
    "hard": 0.0,
}

# Schwellenwerte (Seiler: 80/20 optimal, >75/25 akzeptabel)
OPTIMAL_EASY_PCT = 80.0
MIN_EASY_PCT = 75.0
MAX_HARD_PCT = 25.0


# ---------------------------------------------------------------------------
# Validierung
# ---------------------------------------------------------------------------


class IntensityDistribution(BaseModel):
    """Intensitätsverteilung einer Trainingswoche."""

    easy_count: int = 0  # Anzahl lockere Sessions
    moderate_count: int = 0  # Anzahl moderate Sessions
    hard_count: int = 0  # Anzahl intensive Sessions
    total_running: int = 0  # Gesamtzahl Running-Sessions

    easy_pct: float = 0.0  # Gewichteter Easy-Anteil (%)
    hard_pct: float = 0.0  # Gewichteter Hard-Anteil (%)

    is_valid: bool = True  # True wenn 80/20 eingehalten
    warning: Optional[str] = None


def validate_intensity_distribution(
    run_types: list[str],
) -> IntensityDistribution:
    """Validiere die Intensitätsverteilung einer Woche.

    Args:
        run_types: Liste der Run-Typen in der Woche (z.B. ["easy", "tempo", "easy", "long_run"]).

    Returns:
        IntensityDistribution mit Anteilen und ggf. Warnung.
    """
    if not run_types:
        return IntensityDistribution()

    easy_count = 0
    moderate_count = 0
    hard_count = 0

    for rt in run_types:
        category = _INTENSITY_CATEGORY.get(rt, "easy")
        if category == "easy":
            easy_count += 1
        elif category == "moderate":
            moderate_count += 1
        else:
            hard_count += 1

    total = len(run_types)

    # Gewichtete Berechnung (Moderate zählt 50/50)
    weighted_easy = easy_count + moderate_count * _EASY_WEIGHT["moderate"]
    weighted_hard = hard_count + moderate_count * (1 - _EASY_WEIGHT["moderate"])

    easy_pct = round(weighted_easy / total * 100, 1) if total > 0 else 0
    hard_pct = round(weighted_hard / total * 100, 1) if total > 0 else 0

    # Validierung
    is_valid = easy_pct >= MIN_EASY_PCT
    warning = _build_warning(easy_pct, hard_pct, hard_count, total)

    return IntensityDistribution(
        easy_count=easy_count,
        moderate_count=moderate_count,
        hard_count=hard_count,
        total_running=total,
        easy_pct=easy_pct,
        hard_pct=hard_pct,
        is_valid=is_valid,
        warning=warning,
    )


def _build_warning(
    easy_pct: float,
    hard_pct: float,
    hard_count: int,
    total: int,
) -> Optional[str]:
    """Generiere Warnung wenn 80/20 verletzt."""
    if easy_pct >= OPTIMAL_EASY_PCT:
        return None  # Perfekt

    if easy_pct >= MIN_EASY_PCT:
        return (
            f"Intensitätsverteilung akzeptabel ({easy_pct:.0f}% locker / "
            f"{hard_pct:.0f}% intensiv), aber nicht optimal. "
            f"Ideal: ≥{OPTIMAL_EASY_PCT:.0f}% lockere Einheiten (Seiler 80/20)."
        )

    return (
        f"⚠️ Intensitätsverteilung zu hart: {easy_pct:.0f}% locker / "
        f"{hard_pct:.0f}% intensiv ({hard_count} von {total} Sessions). "
        f"Empfehlung: Maximal {MAX_HARD_PCT:.0f}% intensive Einheiten "
        f"pro Woche für optimale Anpassung (Seiler 80/20-Regel)."
    )


# ---------------------------------------------------------------------------
# Plan-Level Validierung
# ---------------------------------------------------------------------------


def validate_plan_intensity(
    weeks: list[list[str]],
) -> PlanIntensityReport:
    """Validiere die Intensitätsverteilung eines kompletten Plans.

    Args:
        weeks: Liste von Wochen, jede Woche eine Liste von Run-Typen.

    Returns:
        PlanIntensityReport mit Gesamt-Bewertung und Wochen-Details.
    """
    week_results: list[IntensityDistribution] = []
    violations: list[int] = []

    for i, week_runs in enumerate(weeks):
        dist = validate_intensity_distribution(week_runs)
        week_results.append(dist)
        if not dist.is_valid:
            violations.append(i + 1)  # 1-basierte Wochen-Nummer

    all_run_types = [rt for week in weeks for rt in week]
    overall = validate_intensity_distribution(all_run_types)

    return PlanIntensityReport(
        overall=overall,
        weeks=week_results,
        violation_weeks=violations,
        is_plan_valid=len(violations) == 0,
    )


class PlanIntensityReport(BaseModel):
    """Intensitätsbericht für einen kompletten Plan."""

    overall: IntensityDistribution
    weeks: list[IntensityDistribution]
    violation_weeks: list[int]  # 1-basierte Wochen-Nummern mit Verletzungen
    is_plan_valid: bool
