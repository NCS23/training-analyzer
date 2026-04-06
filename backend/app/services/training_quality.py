"""Trainingsqualität-Metriken — 80/20-Verteilung, Monotonie, Strain.

Wissenschaftliche Grundlage:
- Seiler (2010): Polarisiertes Training 80/20
- Foster (1998): Monotonie und Strain als Übertrainings-Indikatoren
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from app.services.fitness_score import _get_hr_zone

if TYPE_CHECKING:
    from app.infrastructure.database.models import WorkoutModel


@dataclass
class IntensityDistribution:
    """Verteilung der Trainingszeit auf Intensitätsbereiche."""

    low_percent: float  # Zone 1-2
    medium_percent: float  # Zone 3
    high_percent: float  # Zone 4-5
    total_minutes: float
    is_polarized: bool  # low >= 75 und high >= 15


@dataclass
class MonotonyResult:
    """Trainings-Monotonie (Gleichförmigkeit)."""

    value: float
    level: str  # "good" | "medium" | "high"


@dataclass
class StrainResult:
    """Trainings-Strain (Belastungsmaß)."""

    value: float
    level: str  # "normal" | "elevated" | "high"


def calculate_intensity_distribution(
    sessions: Sequence[WorkoutModel],
    resting_hr: int,
    max_hr: int,
    days: int = 28,
) -> IntensityDistribution:
    """Berechne Intensitätsverteilung über die letzten N Tage.

    Analysiert nur Lauf-Sessions mit HR-Daten.
    Gruppiert: Locker (Zone 1-2), Mittel (Zone 3), Intensiv (Zone 4-5).
    Optimal nach Seiler: 75-85% locker, <5% mittel, 15-25% intensiv.
    """
    cutoff = date.today() - timedelta(days=days)
    zone_seconds: dict[str, float] = {"low": 0.0, "medium": 0.0, "high": 0.0}

    for session in sessions:
        if session.workout_type != "running":
            continue
        session_date = session.date.date() if hasattr(session.date, "date") else session.date
        if session_date < cutoff:
            continue

        _accumulate_zone_time(session, resting_hr, max_hr, zone_seconds)

    total = zone_seconds["low"] + zone_seconds["medium"] + zone_seconds["high"]
    if total <= 0:
        return IntensityDistribution(0.0, 0.0, 0.0, 0.0, False)

    total_min = total / 60.0
    low_pct = round(zone_seconds["low"] / total * 100, 1)
    med_pct = round(zone_seconds["medium"] / total * 100, 1)
    high_pct = round(zone_seconds["high"] / total * 100, 1)

    return IntensityDistribution(
        low_percent=low_pct,
        medium_percent=med_pct,
        high_percent=high_pct,
        total_minutes=round(total_min, 1),
        is_polarized=(low_pct >= 75 and high_pct >= 15),
    )


def _accumulate_zone_time(
    session: WorkoutModel,
    resting_hr: int,
    max_hr: int,
    zone_seconds: dict[str, float],
) -> None:
    """Akkumuliere Zonenzeit aus einer Session in das zone_seconds Dict."""
    # Priorität 1: Sekündliche HR-Daten
    if session.hr_timeseries_json:
        try:
            hr_data = json.loads(session.hr_timeseries_json)
            if isinstance(hr_data, list) and len(hr_data) > 0:
                for hr_val in hr_data:
                    if hr_val and hr_val > 0:
                        zone = _get_hr_zone(float(hr_val), resting_hr, max_hr)
                        bucket = _zone_to_bucket(zone)
                        zone_seconds[bucket] += 1.0
                return
        except (json.JSONDecodeError, TypeError):
            pass

    # Priorität 2: Zonen-Verteilung
    if session.hr_zones_json and session.duration_sec:
        try:
            zones_data = json.loads(session.hr_zones_json)
            if isinstance(zones_data, dict):
                for _key, value in zones_data.items():
                    if isinstance(value, dict):
                        zone_num = value.get("zone")
                        pct = value.get("percentage", 0)
                        if zone_num and pct:
                            secs = session.duration_sec * float(pct) / 100.0
                            bucket = _zone_to_bucket(int(zone_num))
                            zone_seconds[bucket] += secs
                return
        except (json.JSONDecodeError, TypeError):
            pass

    # Priorität 3: Durchschnitts-HR
    if session.hr_avg and session.hr_avg > 0 and session.duration_sec:
        zone = _get_hr_zone(float(session.hr_avg), resting_hr, max_hr)
        bucket = _zone_to_bucket(zone)
        zone_seconds[bucket] += float(session.duration_sec)


def _zone_to_bucket(zone: int) -> str:
    if zone <= 2:
        return "low"
    if zone == 3:
        return "medium"
    return "high"


def calculate_monotony(daily_trimps: Sequence[float]) -> MonotonyResult:
    """Berechne Trainings-Monotonie über 7 Tage.

    Monotonie = Mean / StdDev der täglichen TRIMP-Werte.
    Hohe Monotonie (>2.0) = zu gleichförmig = Übertrainingsrisiko.

    Args:
        daily_trimps: TRIMP-Werte der letzten 7 Tage (inkl. Ruhetage als 0).
    """
    if len(daily_trimps) < 2:
        return MonotonyResult(value=0.0, level="good")

    mean = sum(daily_trimps) / len(daily_trimps)
    if mean <= 0:
        return MonotonyResult(value=0.0, level="good")

    variance = sum((x - mean) ** 2 for x in daily_trimps) / len(daily_trimps)
    std_dev = math.sqrt(variance)

    if std_dev <= 0:
        # Alle Werte gleich → maximale Monotonie
        return MonotonyResult(value=10.0, level="high")

    monotony = round(mean / std_dev, 2)

    if monotony > 2.0:
        level = "high"
    elif monotony > 1.5:
        level = "medium"
    else:
        level = "good"

    return MonotonyResult(value=monotony, level=level)


def calculate_strain(weekly_trimp: float, monotony: float) -> StrainResult:
    """Berechne Training Strain.

    Strain = Wochen-TRIMP × Monotonie.
    Hoher Strain bei hoher Monotonie → Übertrainingsrisiko.
    """
    strain = round(weekly_trimp * monotony, 1)

    # Schwellwerte sind relativ — grobe Orientierung
    if strain > 5000 and monotony > 1.5:
        level = "high"
    elif strain > 3000:
        level = "elevated"
    else:
        level = "normal"

    return StrainResult(value=strain, level=level)


def get_last_7_days_trimps(
    sessions: Sequence[WorkoutModel],
) -> list[float]:
    """Extrahiere tägliche TRIMP-Werte der letzten 7 Tage (inkl. Ruhetage als 0)."""
    today = date.today()
    daily: dict[date, float] = defaultdict(float)

    for s in sessions:
        if s.trimp_score and s.trimp_score > 0:
            d = s.date.date() if hasattr(s.date, "date") else s.date
            if (today - d).days < 7:
                daily[d] += s.trimp_score

    return [daily.get(today - timedelta(days=i), 0.0) for i in range(7)]
