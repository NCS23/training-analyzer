"""Volumen-Kalibrierung aus Trainingshistorie.

Berechnet wochenweise Volumen-Ziele basierend auf dem tatsächlichen
Trainingsvolumen des Athleten, mit 10%-Regel und Deload-Integration.

Quellen:
- Daniels: Running Formula (10%-Regel)
- Pfitzinger: Advanced Marathoning (Volume Progression)
- Bompa: Periodization (Superkompensation)

Abhängigkeiten:
- athlete_fitness.py (S02, #555) — avg_weekly_km
- deload_pattern.py (S03, #552) — WeekVolumeFactor
"""

from __future__ import annotations

from typing import Optional

from app.services.deload_pattern import (
    DeloadRatio,
    compute_volume_factors,
)

# Maximale Steigerung pro Woche (10%-Regel, Daniels)
MAX_WEEKLY_INCREASE_PCT = 0.10

# Maximaler Peak als Vielfaches des Start-Volumens
MAX_PEAK_MULTIPLIER = 2.0

# Minimum-Volumen (km/Woche) — darunter macht Periodisierung keinen Sinn
MIN_WEEKLY_VOLUME_KM = 10.0


def calibrate_weekly_volumes(
    phases: list[dict],
    current_weekly_km: float,
    peak_volume_km: Optional[float] = None,
    deload_ratio: DeloadRatio = DeloadRatio.RATIO_3_1,
) -> list[WeeklyVolumeTarget]:
    """Berechne kalibrierte Volumen-Ziele für jede Woche eines Plans.

    Kombiniert:
    1. Lineare Progression vom Start- zum Peak-Volumen (10%-Regel)
    2. Deload-Faktoren aus deload_pattern.py
    3. Volumen-Caps (max 2x Start, min 10km)

    Args:
        phases: Phasen-Definitionen [{phase_type, weeks}, ...].
        current_weekly_km: Aktuelles Wochenvolumen (aus FitnessProfile oder Parameter).
        peak_volume_km: Ziel-Peak-Volumen (optional, wird sonst berechnet).
        deload_ratio: Deload-Muster (3:1 oder 2:1).

    Returns:
        Liste von WeeklyVolumeTarget für jede Woche.
    """
    start_km = max(current_weekly_km, MIN_WEEKLY_VOLUME_KM)

    # Peak-Volumen berechnen oder validieren
    total_weeks = sum(int(p.get("weeks", 1)) for p in phases)
    if peak_volume_km is None:
        peak_km = _estimate_peak_from_progression(start_km, total_weeks)
    else:
        peak_km = min(peak_volume_km, start_km * MAX_PEAK_MULTIPLIER)

    peak_km = max(peak_km, start_km)  # Peak nie unter Start

    # Deload-Faktoren holen
    volume_factors = compute_volume_factors(phases, deload_ratio)

    # Basis-Volumen pro Woche berechnen (lineare Progression zum Peak)
    base_volumes = _compute_base_volumes(phases, start_km, peak_km)

    # Deload-Faktoren anwenden
    result: list[WeeklyVolumeTarget] = []
    for i, factor in enumerate(volume_factors):
        base_vol = base_volumes[i] if i < len(base_volumes) else start_km

        adjusted_vol = round(base_vol * factor.volume_factor, 1)
        adjusted_vol = max(adjusted_vol, MIN_WEEKLY_VOLUME_KM)

        result.append(
            WeeklyVolumeTarget(
                week_number=factor.week_number,
                phase=factor.phase.value,
                base_volume_km=round(base_vol, 1),
                adjusted_volume_km=adjusted_vol,
                volume_factor=factor.volume_factor,
                is_deload=factor.is_deload,
                is_taper=factor.is_taper,
            )
        )

    # 10%-Regel validieren
    _enforce_10_percent_rule(result)

    return result


class WeeklyVolumeTarget:
    """Volumen-Ziel für eine Trainingswoche."""

    def __init__(
        self,
        week_number: int,
        phase: str,
        base_volume_km: float,
        adjusted_volume_km: float,
        volume_factor: float,
        is_deload: bool,
        is_taper: bool,
    ) -> None:
        self.week_number = week_number
        self.phase = phase
        self.base_volume_km = base_volume_km
        self.adjusted_volume_km = adjusted_volume_km
        self.volume_factor = volume_factor
        self.is_deload = is_deload
        self.is_taper = is_taper


def _compute_base_volumes(
    phases: list[dict],
    start_km: float,
    peak_km: float,
) -> list[float]:
    """Berechne Basis-Volumen pro Woche (vor Deload-Anpassung).

    Progression:
    - recovery/transition: start_km * 0.5
    - base: linear von start_km → start_km + 40% des Wegs zum Peak
    - build: linear bis 80% Peak
    - peak: 100% Peak
    - taper: Peak (wird durch Deload-Faktor reduziert)
    """
    result: list[float] = []
    global_week = 0
    total_weeks = sum(int(p.get("weeks", 1)) for p in phases)

    for phase in phases:
        phase_type = str(phase.get("phase_type", "base"))
        phase_weeks = int(phase.get("weeks", 1))

        for _week_in_phase in range(phase_weeks):
            progress = global_week / max(1, total_weeks - 1)

            if phase_type in ("recovery", "transition"):
                vol = start_km * 0.5
            elif phase_type == "taper":
                vol = peak_km  # Deload-Faktor reduziert
            else:
                # Lineare Progression von Start zu Peak
                vol = start_km + (peak_km - start_km) * progress

            result.append(vol)
            global_week += 1

    return result


def _estimate_peak_from_progression(start_km: float, total_weeks: int) -> float:
    """Schätze Peak-Volumen basierend auf 10%-Regel und Wochenzahl.

    Berücksichtigt dass ~25% der Wochen Deloads/Taper sind.
    """
    # Effektive Aufbau-Wochen ≈ 75% der Gesamtwochen
    effective_weeks = int(total_weeks * 0.75)

    # Mit 10%/Woche: peak = start * (1.10)^effective_weeks
    # Aber gecappt auf MAX_PEAK_MULTIPLIER
    raw_peak = start_km * (1 + MAX_WEEKLY_INCREASE_PCT) ** effective_weeks
    return min(raw_peak, start_km * MAX_PEAK_MULTIPLIER)


def _enforce_10_percent_rule(targets: list[WeeklyVolumeTarget]) -> None:
    """Stelle sicher dass keine Woche >10% mehr als die Vorwoche hat.

    Deload- und Taper-Wochen werden übersprungen (reduziertes Volumen ist ok).
    Nach einem Deload darf das Volumen auf das Niveau vor dem Deload zurückkehren.
    """
    if len(targets) < 2:
        return

    pre_deload_volume = targets[0].adjusted_volume_km

    for i in range(1, len(targets)):
        current = targets[i]
        prev = targets[i - 1]

        # Deload/Taper: Reduzierung ist immer ok, merke Pre-Deload-Volumen
        if current.is_deload or current.is_taper:
            continue

        # Nach Deload: darf auf Pre-Deload-Niveau zurückkehren
        if prev.is_deload:
            max_allowed = max(
                pre_deload_volume,
                prev.adjusted_volume_km * (1 + MAX_WEEKLY_INCREASE_PCT),
            )
        else:
            max_allowed = prev.adjusted_volume_km * (1 + MAX_WEEKLY_INCREASE_PCT)
            pre_deload_volume = prev.adjusted_volume_km

        if current.adjusted_volume_km > max_allowed:
            current.adjusted_volume_km = round(max_allowed, 1)
