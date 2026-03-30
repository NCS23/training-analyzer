"""VDOT-Rechner nach Jack Daniels' Running Formula.

Berechnet den VDOT-Wert (Index der aeroben Leistungsfähigkeit) aus einer
bekannten Leistung und leitet individuelle Trainingszonen ab.

Quellen:
- Daniels, J. (2014). Daniels' Running Formula, 3rd Edition.
- Pace-Tabellen: Kapitel 3+5 (VDOT → Trainings-Paces).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# VDOT-Lookup-Tabelle
# ---------------------------------------------------------------------------
# Stützstellen: VDOT → Wettkampfzeiten in Sekunden für Standarddistanzen.
# Werte aus Daniels' Running Formula, 3rd Edition (gerundete Tabellenwerte).
# Fehlende VDOT-Werte werden linear interpoliert.

_VDOT_TABLE: list[dict[str, float]] = [
    # vdot, 1500m, 1mile, 3000m, 5000m, 10000m, 15000m, half_marathon, marathon
    {"vdot": 30, "d1500": 510, "d5000": 1800, "d10000": 3762, "d21097": 8280, "d42195": 17100},
    {"vdot": 32, "d1500": 486, "d5000": 1710, "d10000": 3576, "d21097": 7860, "d42195": 16260},
    {"vdot": 34, "d1500": 462, "d5000": 1626, "d10000": 3402, "d21097": 7470, "d42195": 15480},
    {"vdot": 36, "d1500": 441, "d5000": 1548, "d10000": 3240, "d21097": 7110, "d42195": 14760},
    {"vdot": 38, "d1500": 420, "d5000": 1476, "d10000": 3090, "d21097": 6780, "d42195": 14100},
    {"vdot": 40, "d1500": 402, "d5000": 1410, "d10000": 2952, "d21097": 6480, "d42195": 13500},
    {"vdot": 42, "d1500": 384, "d5000": 1350, "d10000": 2826, "d21097": 6210, "d42195": 12948},
    {"vdot": 44, "d1500": 367, "d5000": 1290, "d10000": 2706, "d21097": 5952, "d42195": 12420},
    {"vdot": 46, "d1500": 352, "d5000": 1236, "d10000": 2592, "d21097": 5700, "d42195": 11916},
    {"vdot": 48, "d1500": 338, "d5000": 1188, "d10000": 2490, "d21097": 5478, "d42195": 11448},
    {"vdot": 50, "d1500": 324, "d5000": 1140, "d10000": 2394, "d21097": 5268, "d42195": 11010},
    {"vdot": 52, "d1500": 312, "d5000": 1098, "d10000": 2304, "d21097": 5070, "d42195": 10596},
    {"vdot": 54, "d1500": 300, "d5000": 1056, "d10000": 2220, "d21097": 4884, "d42195": 10212},
    {"vdot": 56, "d1500": 289, "d5000": 1020, "d10000": 2142, "d21097": 4710, "d42195": 9852},
    {"vdot": 58, "d1500": 279, "d5000": 984, "d10000": 2070, "d21097": 4548, "d42195": 9510},
    {"vdot": 60, "d1500": 270, "d5000": 951, "d10000": 2001, "d21097": 4398, "d42195": 9198},
    {"vdot": 62, "d1500": 261, "d5000": 921, "d10000": 1938, "d21097": 4260, "d42195": 8904},
    {"vdot": 64, "d1500": 252, "d5000": 891, "d10000": 1878, "d21097": 4128, "d42195": 8628},
    {"vdot": 66, "d1500": 244, "d5000": 864, "d10000": 1821, "d21097": 4002, "d42195": 8370},
    {"vdot": 68, "d1500": 237, "d5000": 837, "d10000": 1767, "d21097": 3888, "d42195": 8124},
    {"vdot": 70, "d1500": 230, "d5000": 813, "d10000": 1716, "d21097": 3780, "d42195": 7896},
    {"vdot": 72, "d1500": 223, "d5000": 789, "d10000": 1668, "d21097": 3672, "d42195": 7680},
    {"vdot": 74, "d1500": 217, "d5000": 768, "d10000": 1623, "d21097": 3576, "d42195": 7476},
    {"vdot": 76, "d1500": 211, "d5000": 747, "d10000": 1578, "d21097": 3480, "d42195": 7278},
    {"vdot": 78, "d1500": 205, "d5000": 729, "d10000": 1539, "d21097": 3390, "d42195": 7092},
    {"vdot": 80, "d1500": 200, "d5000": 711, "d10000": 1500, "d21097": 3306, "d42195": 6912},
    {"vdot": 82, "d1500": 195, "d5000": 693, "d10000": 1464, "d21097": 3228, "d42195": 6744},
    {"vdot": 85, "d1500": 188, "d5000": 669, "d10000": 1413, "d21097": 3120, "d42195": 6522},
]

# Distanz-Keys in der Tabelle → km
_DISTANCE_KEYS: dict[str, float] = {
    "d1500": 1.5,
    "d5000": 5.0,
    "d10000": 10.0,
    "d21097": 21.0975,
    "d42195": 42.195,
}

# Umgekehrt: km → Key (mit Toleranz für typische Eingaben)
_KM_TO_KEY: list[tuple[float, str]] = sorted(
    [(km, key) for key, km in _DISTANCE_KEYS.items()],
    key=lambda x: x[0],
)


def _find_distance_key(distance_km: float) -> str | None:
    """Finde den passenden Tabellen-Key für eine Distanz (±5% Toleranz)."""
    for km, key in _KM_TO_KEY:
        if abs(distance_km - km) / km < 0.05:
            return key
    return None


def _interpolate_vdot_for_distance(
    distance_key: str,
    time_seconds: float,
) -> float | None:
    """Interpoliere VDOT aus der Tabelle für eine gegebene Distanz und Zeit.

    Schnellere Zeit (weniger Sekunden) = höherer VDOT.
    """
    prev_row: dict[str, float] | None = None

    for row in _VDOT_TABLE:
        row_time = row[distance_key]
        if time_seconds >= row_time:
            if prev_row is None:
                # Langsamer als niedrigster VDOT — auf Untergrenze clampen
                return row["vdot"]
            # Zwischen prev_row und row interpolieren
            prev_time = prev_row[distance_key]
            fraction = (prev_time - time_seconds) / (prev_time - row_time)
            return prev_row["vdot"] + fraction * (row["vdot"] - prev_row["vdot"])
        prev_row = row

    # Schneller als höchster VDOT — auf Obergrenze clampen
    return _VDOT_TABLE[-1]["vdot"]


def _interpolate_time_for_vdot(
    distance_key: str,
    vdot: float,
) -> float:
    """Interpoliere Wettkampfzeit (Sekunden) aus VDOT für eine Distanz."""
    prev_row: dict[str, float] | None = None

    for row in _VDOT_TABLE:
        if vdot <= row["vdot"]:
            if prev_row is None:
                return row[distance_key]
            fraction = (vdot - prev_row["vdot"]) / (row["vdot"] - prev_row["vdot"])
            prev_time = prev_row[distance_key]
            curr_time = row[distance_key]
            return prev_time + fraction * (curr_time - prev_time)
        prev_row = row

    return _VDOT_TABLE[-1][distance_key]


# ---------------------------------------------------------------------------
# Daniels-Trainingszonen: VDOT → Pace-Bereiche (sec/km)
# ---------------------------------------------------------------------------
# Abgeleitet aus Daniels' Running Formula Tabellen (Kapitel 5).
# Jede Zone ist als Multiplikator relativ zur 5K-Pace definiert,
# da 5K-Pace ≈ VO2max-Pace (Daniels' I-Pace).
#
# Die Bereiche sind (min_sec_per_km, max_sec_per_km) — min ist schneller.


def _5k_pace_from_vdot(vdot: float) -> float:
    """Berechne 5K-Pace (sec/km) aus VDOT."""
    time_5k = _interpolate_time_for_vdot("d5000", vdot)
    return time_5k / 5.0


def training_paces_from_vdot(vdot: float) -> dict[str, tuple[float, float]]:
    """Berechne Daniels-Trainingszonen aus VDOT.

    Returns:
        Dict mit Zone → (schnellere_pace_sec_km, langsamere_pace_sec_km).
        Zonen: easy, marathon, threshold, interval, repetition.
    """
    pace_5k = _5k_pace_from_vdot(vdot)

    # Multiplikatoren relativ zu 5K-Pace (Daniels-basiert).
    # 5K-Pace ≈ I-Pace (Interval/VO2max).
    return {
        "easy": (pace_5k * 1.25, pace_5k * 1.40),
        "marathon": (pace_5k * 1.12, pace_5k * 1.18),
        "threshold": (pace_5k * 1.06, pace_5k * 1.10),
        "interval": (pace_5k * 0.97, pace_5k * 1.03),
        "repetition": (pace_5k * 0.88, pace_5k * 0.95),
    }


def training_paces_for_plan(vdot: float) -> dict[str, tuple[float, float]]:
    """Trainingszonen im Format des Plan-Generators (kompatibel mit PACE_MULTIPLIERS).

    Mappt Daniels-Zonen auf die Session-Typen des Plan-Generators:
    easy, recovery, tempo, intervals, long_run, progression, repetitions, fartlek, race.
    """
    daniels = training_paces_from_vdot(vdot)

    # Marathon-Pace für Race und Long Run (HM ≈ etwas schneller als Marathon)
    hm_time = _interpolate_time_for_vdot("d21097", vdot)
    hm_pace = hm_time / 21.0975
    marathon_time = _interpolate_time_for_vdot("d42195", vdot)
    marathon_pace = marathon_time / 42.195

    return {
        "easy": daniels["easy"],
        "recovery": (daniels["easy"][1], daniels["easy"][1] * 1.08),
        "tempo": daniels["threshold"],
        "intervals": daniels["interval"],
        "long_run": (daniels["easy"][0] * 0.95, daniels["easy"][1]),
        "progression": (daniels["marathon"][0], daniels["easy"][1]),
        "repetitions": daniels["repetition"],
        "fartlek": (daniels["threshold"][0], daniels["easy"][0]),
        "race": (hm_pace * 0.99, hm_pace * 1.01),
        "marathon_race": (marathon_pace * 0.99, marathon_pace * 1.01),
    }


# ---------------------------------------------------------------------------
# VDOT-Schätzung aus Leistungsdaten
# ---------------------------------------------------------------------------


def estimate_vdot(distance_km: float, time_seconds: float) -> float | None:
    """Schätze VDOT aus einer bekannten Leistung.

    Args:
        distance_km: Wettkampf-/Testdistanz in km (z.B. 5.0, 10.0, 21.0975).
        time_seconds: Benötigte Zeit in Sekunden.

    Returns:
        Geschätzter VDOT-Wert (30-85) oder None wenn Distanz nicht unterstützt.
    """
    if time_seconds <= 0 or distance_km <= 0:
        return None

    dist_key = _find_distance_key(distance_km)
    if dist_key is None:
        # Nicht-Standard-Distanz: über Pace → nächste bekannte Distanz extrapolieren
        return _estimate_vdot_from_pace(distance_km, time_seconds)

    return _interpolate_vdot_for_distance(dist_key, time_seconds)


def _estimate_vdot_from_pace(distance_km: float, time_seconds: float) -> float | None:
    """Schätze VDOT für Nicht-Standard-Distanzen über Pace-Vergleich.

    Findet die zwei nächsten Standard-Distanzen und interpoliert.
    """
    # Nächste kleinere und größere Standarddistanz finden
    smaller_key: str | None = None
    larger_key: str | None = None

    for km, key in _KM_TO_KEY:
        if km <= distance_km:
            smaller_key = key
        if km >= distance_km and larger_key is None:
            larger_key = key

    # Fallback: nächste verfügbare Distanz
    ref_key = smaller_key or larger_key
    if ref_key is None:
        return None

    ref_km = _DISTANCE_KEYS[ref_key]

    # Geschätzte Zeit auf Referenz-Distanz (Riegel-Formel: t2 = t1 * (d2/d1)^1.06)
    estimated_ref_time = time_seconds * (ref_km / distance_km) ** 1.06

    return _interpolate_vdot_for_distance(ref_key, estimated_ref_time)


# ---------------------------------------------------------------------------
# Äquivalente Wettkampfzeiten
# ---------------------------------------------------------------------------


def equivalent_race_time(
    vdot: float,
    target_distance_km: float,
) -> int | None:
    """Berechne die äquivalente Wettkampfzeit für eine Zieldistanz.

    Args:
        vdot: Aktueller VDOT-Wert.
        target_distance_km: Zieldistanz in km.

    Returns:
        Geschätzte Zeit in Sekunden oder None.
    """
    dist_key = _find_distance_key(target_distance_km)
    if dist_key is None:
        # Nicht-Standard-Distanz: Riegel-Formel von 5K extrapolieren
        time_5k = _interpolate_time_for_vdot("d5000", vdot)
        estimated = time_5k * (target_distance_km / 5.0) ** 1.06
        return round(estimated)

    return round(_interpolate_time_for_vdot(dist_key, vdot))


# ---------------------------------------------------------------------------
# Ziel-Validierung
# ---------------------------------------------------------------------------


class GoalCategory(str, Enum):
    """Kategorie der Zielbewertung."""

    REALISTIC = "realistic"
    AMBITIOUS = "ambitious"
    UNREALISTIC = "unrealistic"


class GoalAssessment(BaseModel):
    """Ergebnis der Ziel-Validierung."""

    category: GoalCategory
    message: str
    current_vdot: float
    required_vdot: float
    suggested_time_seconds: Optional[int] = None


def is_goal_realistic(
    current_vdot: float,
    goal_distance_km: float,
    goal_time_seconds: int,
) -> GoalAssessment:
    """Prüfe ob ein Wettkampfziel realistisch ist.

    Vergleicht den aktuellen VDOT mit dem VDOT, der nötig wäre,
    um die Zielzeit zu erreichen.

    Args:
        current_vdot: Aktueller VDOT des Athleten.
        goal_distance_km: Zieldistanz in km.
        goal_time_seconds: Zielzeit in Sekunden.

    Returns:
        GoalAssessment mit Kategorie und Erklärung.
    """
    required_vdot = estimate_vdot(goal_distance_km, goal_time_seconds)

    if required_vdot is None:
        return GoalAssessment(
            category=GoalCategory.REALISTIC,
            message="Ziel konnte nicht validiert werden (unbekannte Distanz).",
            current_vdot=current_vdot,
            required_vdot=current_vdot,
        )

    vdot_gap_pct = (required_vdot - current_vdot) / current_vdot * 100

    # Realistische Zeit basierend auf aktuellem VDOT
    realistic_time = equivalent_race_time(current_vdot, goal_distance_km)

    if vdot_gap_pct <= 3.0:
        return GoalAssessment(
            category=GoalCategory.REALISTIC,
            message=(
                f"Dein Ziel ist realistisch. Dein aktueller VDOT ({current_vdot:.1f}) "
                f"liegt nahe am benötigten Niveau ({required_vdot:.1f})."
            ),
            current_vdot=current_vdot,
            required_vdot=required_vdot,
        )

    if vdot_gap_pct <= 10.0:
        return GoalAssessment(
            category=GoalCategory.AMBITIOUS,
            message=(
                f"Dein Ziel ist ambitioniert. Du brauchst einen VDOT von {required_vdot:.1f}, "
                f"aktuell bist du bei {current_vdot:.1f} "
                f"(Lücke: {vdot_gap_pct:.1f}%). "
                f"Mit konsequentem Training in {_weeks_estimate(vdot_gap_pct)} erreichbar."
            ),
            current_vdot=current_vdot,
            required_vdot=required_vdot,
            suggested_time_seconds=realistic_time,
        )

    return GoalAssessment(
        category=GoalCategory.UNREALISTIC,
        message=(
            f"Dein Ziel ist aktuell unrealistisch. Du brauchst einen VDOT von "
            f"{required_vdot:.1f}, aktuell bist du bei {current_vdot:.1f} "
            f"(Lücke: {vdot_gap_pct:.1f}%). "
            f"Eine realistischere Zielzeit wäre {_format_time(realistic_time)}."
        ),
        current_vdot=current_vdot,
        required_vdot=required_vdot,
        suggested_time_seconds=realistic_time,
    )


def _weeks_estimate(vdot_gap_pct: float) -> str:
    """Grobe Schätzung wie viele Wochen Training nötig sind.

    Faustregel: ~1 VDOT-Punkt pro 4-6 Wochen konsistentes Training.
    """
    # Bei 3-5% Gap: 8-16 Wochen, bei 5-10%: 16-30 Wochen
    if vdot_gap_pct <= 5:
        return "8-16 Wochen"
    return "16-30 Wochen"


def _format_time(seconds: int | None) -> str:
    """Formatiere Sekunden als H:MM:SS oder M:SS."""
    if seconds is None:
        return "unbekannt"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
