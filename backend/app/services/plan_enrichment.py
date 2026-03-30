"""Plan-Enrichment: VDOT-basierte Paces und HR-Zonen für den Plan-Generator.

Überbrückt den VDOT-Rechner und HR-Zonen-Calculator mit dem Plan-Generator.
Ersetzt die hardcodierten PACE_MULTIPLIERS durch individuelle Trainingszonen
wenn ein FitnessProfile vorhanden ist.

Abhängigkeiten:
- vdot_calculator.py (S01, #541)
- athlete_fitness.py (S02, #555)
- hr_zone_calculator.py (bestehend)
"""

from __future__ import annotations

from typing import Optional

from app.services.hr_zone_calculator import (
    calculate_friel_zones,
    calculate_karvonen_zones,
)
from app.services.vdot_calculator import training_paces_for_plan

# Fallback-Multiplikatoren relativ zur Race-Pace (identisch mit plan_generator.py).
# Nur verwendet wenn kein VDOT vorhanden ist.
_FALLBACK_PACE_MULTIPLIERS: dict[str, tuple[float, float]] = {
    "easy": (1.15, 1.22),
    "recovery": (1.22, 1.30),
    "tempo": (1.02, 1.07),
    "intervals": (0.90, 0.96),
    "long_run": (1.08, 1.15),
    "progression": (1.10, 1.22),
    "repetitions": (0.85, 0.92),
    "fartlek": (1.05, 1.18),
    "race": (1.00, 1.00),
}


def _seconds_to_pace(sec_per_km: float) -> str:
    """Konvertiere Sekunden/km in 'M:SS' Pace-String."""
    minutes = int(sec_per_km // 60)
    seconds = int(sec_per_km % 60)
    return f"{minutes}:{seconds:02d}"


# ---------------------------------------------------------------------------
# VDOT-basierte Pace-Berechnung
# ---------------------------------------------------------------------------


def get_vdot_paces(vdot: float) -> dict[str, tuple[str, str]]:
    """Berechne individuelle Trainingspaces aus VDOT als formatierte Strings.

    Returns:
        Dict mit run_type → (schnellere_pace, langsamere_pace) als "M:SS".
    """
    raw = training_paces_for_plan(vdot)
    return {
        run_type: (_seconds_to_pace(fast), _seconds_to_pace(slow))
        for run_type, (fast, slow) in raw.items()
    }


def get_pace_for_run_type(
    run_type: str,
    vdot: Optional[float] = None,
    race_pace: Optional[float] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Hole Pace-Bereich für einen Run-Typ.

    Priorität:
    1. VDOT-basierte individuelle Paces
    2. Race-Pace mit hardcodierten Multiplikatoren (Fallback)
    3. None/None wenn keine Daten

    Args:
        run_type: Session-Typ (easy, tempo, intervals etc.)
        vdot: VDOT-Wert des Athleten (bevorzugt)
        race_pace: Race-Pace in sec/km (Fallback)

    Returns:
        (pace_min, pace_max) als "M:SS" Strings oder (None, None).
    """
    if vdot is not None:
        paces = get_vdot_paces(vdot)
        if run_type in paces:
            return paces[run_type]

    if race_pace is not None:
        multipliers = _FALLBACK_PACE_MULTIPLIERS.get(run_type, _FALLBACK_PACE_MULTIPLIERS["easy"])
        pace_fast = race_pace * multipliers[0]
        pace_slow = race_pace * multipliers[1]
        return (_seconds_to_pace(pace_fast), _seconds_to_pace(pace_slow))

    return (None, None)


# ---------------------------------------------------------------------------
# HR-Zonen-Berechnung für Segmente
# ---------------------------------------------------------------------------

# Mapping: run_type → (Friel-Zone, Karvonen-Zone)
# Verwendet für target_hr_min/max in Segmenten.
_RUN_TYPE_TO_ZONE: dict[str, int] = {
    "easy": 2,
    "recovery": 1,
    "long_run": 2,
    "tempo": 4,
    "threshold": 4,
    "intervals": 5,
    "repetitions": 5,
    "progression": 3,  # Start easy, ende tempo
    "fartlek": 3,
    "race": 4,
}


def get_hr_zone_for_run_type(
    run_type: str,
    lthr: Optional[int] = None,
    resting_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
) -> tuple[Optional[int], Optional[int]]:
    """Berechne HR-Zielzone (min, max bpm) für einen Run-Typ.

    Priorität:
    1. Friel-Zonen (wenn LTHR vorhanden)
    2. Karvonen-Zonen (wenn Resting+Max HR vorhanden)
    3. None/None

    Args:
        run_type: Session-Typ.
        lthr: Laktatschwellen-HR.
        resting_hr: Ruhe-HR.
        max_hr: Max-HR.

    Returns:
        (hr_min, hr_max) in bpm oder (None, None).
    """
    target_zone = _RUN_TYPE_TO_ZONE.get(run_type, 2)

    zones: list[dict] = []
    if lthr is not None:
        zones = calculate_friel_zones(lthr)
    elif resting_hr is not None and max_hr is not None:
        zones = calculate_karvonen_zones(resting_hr, max_hr)

    if not zones:
        return (None, None)

    # Zone-Nummern sind 1-basiert
    for z in zones:
        if z["zone"] == target_zone:
            return (z["lower_bpm"], z["upper_bpm"])

    return (None, None)


# ---------------------------------------------------------------------------
# Kombinierte Enrichment-Funktion
# ---------------------------------------------------------------------------


def enrich_run_details_params(
    run_type: str,
    vdot: Optional[float] = None,
    race_pace: Optional[float] = None,
    lthr: Optional[int] = None,
    resting_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
) -> dict:
    """Berechne alle Pace- und HR-Parameter für eine Running-Session.

    Gibt ein Dict zurück das direkt in Segment-Erstellung verwendet werden kann.

    Returns:
        {
            "pace_min": "5:30" | None,
            "pace_max": "6:00" | None,
            "hr_min": 140 | None,
            "hr_max": 160 | None,
        }
    """
    pace_min, pace_max = get_pace_for_run_type(run_type, vdot, race_pace)
    hr_min, hr_max = get_hr_zone_for_run_type(run_type, lthr, resting_hr, max_hr)

    return {
        "pace_min": pace_min,
        "pace_max": pace_max,
        "hr_min": hr_min,
        "hr_max": hr_max,
    }
