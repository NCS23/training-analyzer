"""Entlastungswochen und progressive Taper-Logik.

Implementiert trainingswissenschaftlich fundierte Volumen-Steuerung:
- Mesozyklus-Muster (3:1 oder 2:1) mit Deload-Wochen
- Progressive Taper-Phase (75% → 60% → 40%)
- Volumen-Faktoren pro Woche für den Plan-Generator

Quellen:
- Pfitzinger: Advanced Marathoning (Periodisierung, Taper)
- Daniels: Running Formula (Meso-Zyklen)
- Bompa & Buzzichelli: Periodization (Theorie der Superkompensation)
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class DeloadRatio(str, Enum):
    """Aufbau:Entlastung Verhältnis."""

    RATIO_3_1 = "3:1"  # Standard: 3 Wochen Aufbau, 1 Woche Deload
    RATIO_2_1 = "2:1"  # Anfänger/Erholung: 2 Wochen Aufbau, 1 Woche Deload


class PhaseType(str, Enum):
    """Trainingsphase."""

    RECOVERY = "recovery"
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"
    TRANSITION = "transition"


class WeekVolumeFactor(BaseModel):
    """Volumen-Faktor für eine Trainingswoche."""

    week_number: int  # 1-basiert (Woche im Plan)
    phase: PhaseType
    volume_factor: float  # 1.0 = volle Volumen-Zielwoche, 0.7 = 70% (Deload)
    is_deload: bool  # True wenn Entlastungswoche
    is_taper: bool  # True wenn Taper-Woche


# ---------------------------------------------------------------------------
# Deload-Pattern
# ---------------------------------------------------------------------------

# Deload-Volumen-Reduktion (Pfitzinger: 20-30% Reduktion in Entlastungswoche)
_DELOAD_FACTOR = 0.75  # 75% des Normalvolumens = 25% Reduktion


def _get_cycle_length(ratio: DeloadRatio) -> int:
    """Zykluslänge (Aufbau + Deload) für ein Verhältnis."""
    if ratio == DeloadRatio.RATIO_2_1:
        return 3  # 2 Aufbau + 1 Deload
    return 4  # 3 Aufbau + 1 Deload


def _is_deload_week(week_in_phase: int, ratio: DeloadRatio) -> bool:
    """Prüfe ob eine Woche im Mesozyklus eine Deload-Woche ist.

    Args:
        week_in_phase: 0-basierter Index der Woche innerhalb der Phase.
        ratio: Aufbau:Entlastung Verhältnis.

    Returns:
        True wenn die Woche eine Entlastungswoche ist.
    """
    cycle_length = _get_cycle_length(ratio)
    return (week_in_phase + 1) % cycle_length == 0


# ---------------------------------------------------------------------------
# Taper-Progression (Pfitzinger: stufenweise Reduktion)
# ---------------------------------------------------------------------------

# Taper-Faktoren: stufenweise Reduktion über die Taper-Wochen.
# Letzte Woche hat die geringste Belastung.
_TAPER_FACTORS: dict[int, list[float]] = {
    1: [0.50],  # 1-Woche Taper: 50%
    2: [0.70, 0.45],  # 2-Wochen: 70% → 45%
    3: [0.75, 0.60, 0.40],  # 3-Wochen: 75% → 60% → 40%
    4: [0.80, 0.70, 0.55, 0.40],  # 4-Wochen: 80% → 70% → 55% → 40%
}


def _taper_factor(week_in_taper: int, taper_weeks: int) -> float:
    """Volumen-Faktor für eine Taper-Woche.

    Args:
        week_in_taper: 0-basierter Index der Woche in der Taper-Phase.
        taper_weeks: Gesamtanzahl der Taper-Wochen.

    Returns:
        Volumen-Faktor (0.4-0.8).
    """
    if taper_weeks <= 0:
        return 1.0

    factors = _TAPER_FACTORS.get(taper_weeks)
    if factors is None:
        # Für >4 Wochen Taper: lineare Interpolation 0.80 → 0.40
        return 0.80 - (0.40 * week_in_taper / (taper_weeks - 1)) if taper_weeks > 1 else 0.50

    if week_in_taper >= len(factors):
        return factors[-1]

    return factors[week_in_taper]


# ---------------------------------------------------------------------------
# Haupt-API: Volumen-Faktoren für einen kompletten Plan
# ---------------------------------------------------------------------------


def compute_volume_factors(
    phases: list[dict[str, object]],
    deload_ratio: DeloadRatio = DeloadRatio.RATIO_3_1,
) -> list[WeekVolumeFactor]:
    """Berechne Volumen-Faktoren für alle Wochen eines Trainingsplans.

    Wendet Deload-Muster auf Base/Build/Peak Phasen an und progressive
    Taper-Faktoren auf die Taper-Phase.

    Args:
        phases: Liste von Phasen-Dicts mit:
            - phase_type: str (base, build, peak, taper, recovery, transition)
            - weeks: int (Anzahl Wochen in dieser Phase)
        deload_ratio: Aufbau:Entlastung Verhältnis (Standard: 3:1).

    Returns:
        Liste von WeekVolumeFactor für jede Woche im Plan.

    Example:
        >>> phases = [
        ...     {"phase_type": "base", "weeks": 5},
        ...     {"phase_type": "build", "weeks": 4},
        ...     {"phase_type": "taper", "weeks": 2},
        ... ]
        >>> factors = compute_volume_factors(phases)
        >>> len(factors) == 11
        True
    """
    result: list[WeekVolumeFactor] = []
    global_week = 1

    for phase_def in phases:
        phase_type = PhaseType(str(phase_def["phase_type"]))
        weeks_raw = phase_def.get("weeks", 1)
        phase_weeks = int(weeks_raw) if isinstance(weeks_raw, (int, float, str)) else 1

        for week_in_phase in range(phase_weeks):
            factor, is_deload, is_taper = _compute_single_week(
                phase_type=phase_type,
                week_in_phase=week_in_phase,
                phase_weeks=phase_weeks,
                deload_ratio=deload_ratio,
                is_last_phase_week=(week_in_phase == phase_weeks - 1),
                next_phase_is_taper=_next_phase_is_taper(phases, phase_def),
            )

            result.append(
                WeekVolumeFactor(
                    week_number=global_week,
                    phase=phase_type,
                    volume_factor=round(factor, 2),
                    is_deload=is_deload,
                    is_taper=is_taper,
                )
            )
            global_week += 1

    return result


def _compute_single_week(
    phase_type: PhaseType,
    week_in_phase: int,
    phase_weeks: int,
    deload_ratio: DeloadRatio,
    is_last_phase_week: bool,
    next_phase_is_taper: bool,
) -> tuple[float, bool, bool]:
    """Berechne Faktor für eine einzelne Woche.

    Returns:
        Tuple (volume_factor, is_deload, is_taper).
    """
    # Taper-Phase: progressive Reduktion
    if phase_type == PhaseType.TAPER:
        factor = _taper_factor(week_in_phase, phase_weeks)
        return (factor, False, True)

    # Recovery/Transition: durchgehend reduziert (keine Deloads nötig)
    if phase_type in (PhaseType.RECOVERY, PhaseType.TRANSITION):
        return (0.70, False, False)

    # Base/Build/Peak: Deload-Pattern anwenden
    if phase_type in (PhaseType.BASE, PhaseType.BUILD, PhaseType.PEAK):
        # Keine Deload direkt vor Taper (Taper ist selbst eine Entlastung)
        if is_last_phase_week and next_phase_is_taper:
            return (1.0, False, False)

        if _is_deload_week(week_in_phase, deload_ratio):
            return (_DELOAD_FACTOR, True, False)

        return (1.0, False, False)

    # Fallback: volle Volumen
    return (1.0, False, False)


def _next_phase_is_taper(
    phases: list[dict[str, object]],
    current_phase: dict[str, object],
) -> bool:
    """Prüfe ob die nächste Phase ein Taper ist."""
    found_current = False
    for phase in phases:
        if found_current:
            return str(phase.get("phase_type", "")) == PhaseType.TAPER.value
        if phase is current_phase:
            found_current = True
    return False


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def suggest_deload_ratio(current_weekly_km: float, weeks_training: int) -> DeloadRatio:
    """Empfehle ein Deload-Verhältnis basierend auf Fitness-Level.

    Args:
        current_weekly_km: Aktuelles Wochenvolumen in km.
        weeks_training: Wochen konsistentes Training.

    Returns:
        Empfohlenes DeloadRatio.
    """
    # Anfänger (<20 km/Woche oder <12 Wochen Training): 2:1
    if current_weekly_km < 20 or weeks_training < 12:
        return DeloadRatio.RATIO_2_1

    return DeloadRatio.RATIO_3_1


def suggest_taper_weeks(race_distance_km: float) -> int:
    """Empfehle die Taper-Länge basierend auf der Wettkampfdistanz.

    Args:
        race_distance_km: Wettkampfdistanz in km.

    Returns:
        Empfohlene Taper-Wochen (1-3).
    """
    if race_distance_km >= 42.0:
        return 3  # Marathon: 3 Wochen
    if race_distance_km >= 21.0:
        return 2  # Halbmarathon: 2 Wochen
    if race_distance_km >= 10.0:
        return 2  # 10K: 1-2 Wochen
    return 1  # 5K und kürzer: 1 Woche
