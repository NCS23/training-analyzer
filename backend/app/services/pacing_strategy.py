"""Pacing-Strategie Generator: Berechnet km-genaue Pace-Empfehlungen."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.segment import Segment

from app.models.pacing import (
    ElevationSegment,
    KmPacingSplit,
    PacingRequest,
    PacingResponse,
    WeatherAdjustment,
)
from app.services.km_split_calculator import (
    DEFAULT_ELEV_GAIN_SEC_PER_100M,
    DEFAULT_ELEV_LOSS_SEC_PER_100M,
)

# ---------------------------------------------------------------------------
# Strategie-Labels (deutsch)
# ---------------------------------------------------------------------------

STRATEGY_LABELS: dict[str, str] = {
    "even": "Gleichmäßig",
    "negative": "Negative Splits",
    "effort_based": "Effort-Based",
}

# ---------------------------------------------------------------------------
# Wetter-Konstanten (sportwissenschaftliche Richtwerte)
# ---------------------------------------------------------------------------

# Temperatur: ~0.5% Leistungsverlust pro Grad ueber 15°C
_TEMP_THRESHOLD_C = 15.0
_TEMP_PENALTY_PCT_PER_DEGREE = 0.5
_TEMP_PENALTY_MAX_PCT = 20.0

# Wind: ~0.3 sec/km pro km/h Gegenwind (vereinfacht, ohne Richtung)
_WIND_PENALTY_SEC_PER_KMH = 0.3

# Luftfeuchtigkeit: zusaetzlich ~0.1% pro Prozentpunkt ueber 70%
_HUMIDITY_THRESHOLD = 70.0
_HUMIDITY_PENALTY_PCT_PER_POINT = 0.1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_pacing_strategy(request: PacingRequest) -> PacingResponse:
    """Generiert eine komplette Pacing-Strategie aus den Request-Parametern."""
    distance = request.distance_km
    target_secs = request.target_time_seconds
    num_full_km = int(distance)
    partial_km = distance - num_full_km

    base_pace_sec = target_secs / distance

    # 1) Elevation-Profil erstellen
    elevation = _get_elevation_profile(
        distance, request.elevation_preset, request.elevation_segments
    )

    # 2) Strategie-Modifier anwenden
    raw_paces = _apply_strategy(base_pace_sec, distance, request.strategy)

    # 3) Hoehen-Anpassung pro km (nur bei effort_based — konstanter Effort)
    #    Even/Negative = konstante Pace, Effort variiert mit Hoehe
    #    Effort-Based  = konstanter Effort, Pace variiert mit Hoehe
    elevation_adjustments = _calc_elevation_adjustments(elevation)
    if request.strategy == "effort_based":
        for i, adj in enumerate(elevation_adjustments):
            raw_paces[i] += adj

    # 4) Wetter-Anpassung (gleichmaessig auf alle km)
    weather_adj = _calc_weather_adjustment(
        base_pace_sec,
        request.temperature_celsius,
        request.wind_speed_kmh,
        request.humidity_percent,
    )
    if weather_adj and weather_adj.penalty_sec_per_km > 0:
        for i in range(len(raw_paces)):
            raw_paces[i] += weather_adj.penalty_sec_per_km

    # 5) Normalisierung: Summe der Zeiten == Zielzeit exakt
    #    Beruecksichtigt partielle letzte km
    distances = [1.0] * num_full_km
    if partial_km > 0.01:
        distances.append(partial_km)
    raw_paces = _normalize_to_target(raw_paces, distances, target_secs)

    # 6) Splits bauen
    splits: list[KmPacingSplit] = []
    cumulative_sec = 0.0

    for i, pace_sec in enumerate(raw_paces):
        km_num = i + 1
        km_dist = distances[i]
        km_time = pace_sec * km_dist
        cumulative_sec += km_time
        cum_int = round(cumulative_sec)

        elev = (
            elevation[i] if i < len(elevation) else ElevationSegment(km=km_num, gain_m=0, loss_m=0)
        )
        note = (
            _build_adjustment_note(
                elevation_adjustments[i] if i < len(elevation_adjustments) else 0.0
            )
            if request.strategy == "effort_based"
            else None
        )

        splits.append(
            KmPacingSplit(
                km=km_num,
                distance_km=round(km_dist, 2),
                target_pace_sec_per_km=round(pace_sec, 1),
                target_pace_formatted=_format_pace_sec(pace_sec),
                cumulative_seconds=cum_int,
                cumulative_formatted=_format_duration(cum_int),
                elevation_gain_m=round(elev.gain_m, 1),
                elevation_loss_m=round(elev.loss_m, 1),
                adjustment_note=note,
            )
        )

    # 7) Notizen
    notes = _build_notes(request.strategy, weather_adj, elevation)

    return PacingResponse(
        strategy=request.strategy,
        strategy_label=STRATEGY_LABELS.get(request.strategy, request.strategy),
        distance_km=distance,
        target_time_seconds=target_secs,
        target_time_formatted=_format_duration(target_secs),
        avg_pace_sec_per_km=round(base_pace_sec, 1),
        avg_pace_formatted=_format_pace_sec(base_pace_sec),
        splits=splits,
        weather_adjustment=weather_adj,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Strategie-Modifier
# ---------------------------------------------------------------------------


def _apply_strategy(
    base_pace_sec: float,
    distance_km: float,
    strategy: str,
) -> list[float]:
    """Erzeugt eine Liste von Pace-Werten (sec/km) basierend auf der Strategie."""
    num_full_km = int(distance_km)
    partial_km = distance_km - num_full_km
    total_splits = num_full_km + (1 if partial_km > 0.01 else 0)

    if strategy == "negative":
        return _negative_split_paces(base_pace_sec, total_splits)
    # even: konstante Pace (Hoehen-Anpassung wird NICHT angewendet)
    # effort_based: startet gleichmaessig, Hoehen-Anpassung kommt in Schritt 3
    return [base_pace_sec] * total_splits


def _negative_split_paces(base_pace: float, num_splits: int) -> list[float]:
    """Negative Split: Stufenmodell (Kipchoge-Stil).

    Erste Haelfte konstant ~3% langsamer, zweite Haelfte konstant schneller.
    Der gewichtete Durchschnitt beider Bloecke ergibt exakt die base_pace.
    """
    if num_splits <= 1:
        return [base_pace] * num_splits

    midpoint = num_splits // 2
    slow_pace = base_pace * 1.03
    # fast_pace so berechnen, dass gewichteter Durchschnitt = base_pace
    remaining = num_splits - midpoint
    fast_pace = (base_pace * num_splits - slow_pace * midpoint) / remaining

    return [slow_pace] * midpoint + [fast_pace] * remaining


# ---------------------------------------------------------------------------
# Hoehenprofil
# ---------------------------------------------------------------------------


def _get_elevation_profile(
    distance_km: float,
    preset: str | None,
    segments: list[ElevationSegment] | None,
) -> list[ElevationSegment]:
    """Erstellt Hoehenprofil: entweder aus manuellen Segmenten oder Preset."""
    num_full_km = int(distance_km)
    partial_km = distance_km - num_full_km
    total_splits = num_full_km + (1 if partial_km > 0.01 else 0)

    if segments:
        # Auffuellen oder kuerzen auf korrekte Laenge
        result = list(segments[:total_splits])
        while len(result) < total_splits:
            result.append(ElevationSegment(km=len(result) + 1, gain_m=0, loss_m=0))
        return result

    if preset == "rolling":
        return _preset_rolling(total_splits)
    if preset == "hilly":
        return _preset_hilly(total_splits)

    # flat (default)
    return [ElevationSegment(km=i + 1, gain_m=0, loss_m=0) for i in range(total_splits)]


def _preset_rolling(num_splits: int) -> list[ElevationSegment]:
    """Wellig: Sinuswelle ~15m gain/loss pro km, netto ~0."""
    result: list[ElevationSegment] = []
    for i in range(num_splits):
        phase = math.sin(2 * math.pi * i / max(num_splits, 1) * 2)
        gain = max(0.0, phase * 15.0)
        loss = max(0.0, -phase * 15.0)
        result.append(ElevationSegment(km=i + 1, gain_m=round(gain, 1), loss_m=round(loss, 1)))
    return result


def _preset_hilly(num_splits: int) -> list[ElevationSegment]:
    """Huegelig: groessere Anstiege, Hauptanstieg im mittleren Drittel."""
    result: list[ElevationSegment] = []
    third = max(1, num_splits // 3)
    for i in range(num_splits):
        if third <= i < 2 * third:
            # Mittleres Drittel: starker Anstieg
            gain, loss = 35.0, 5.0
        elif i >= 2 * third:
            # Letztes Drittel: Abstieg
            gain, loss = 5.0, 35.0
        else:
            # Erstes Drittel: leicht wellig
            gain, loss = 10.0, 10.0
        result.append(ElevationSegment(km=i + 1, gain_m=gain, loss_m=loss))
    return result


def _calc_elevation_adjustments(elevation: list[ElevationSegment]) -> list[float]:
    """Berechnet Hoehen-Anpassung in Sekunden pro km (positiv = langsamer)."""
    adjustments: list[float] = []
    for seg in elevation:
        gain_penalty = (seg.gain_m / 100.0) * DEFAULT_ELEV_GAIN_SEC_PER_100M
        loss_benefit = (seg.loss_m / 100.0) * DEFAULT_ELEV_LOSS_SEC_PER_100M
        adjustments.append(gain_penalty - loss_benefit)
    return adjustments


# ---------------------------------------------------------------------------
# Wetter-Anpassung
# ---------------------------------------------------------------------------


def _calc_weather_adjustment(
    base_pace_sec: float,
    temperature: float | None,
    wind_speed: float | None,
    humidity: float | None,
) -> WeatherAdjustment | None:
    """Berechnet Wetter-bedingte Pace-Anpassung."""
    if temperature is None and wind_speed is None:
        return None

    penalty = 0.0
    parts: list[str] = []

    # Temperatur
    if temperature is not None and temperature > _TEMP_THRESHOLD_C:
        temp_pct = min(
            (temperature - _TEMP_THRESHOLD_C) * _TEMP_PENALTY_PCT_PER_DEGREE,
            _TEMP_PENALTY_MAX_PCT,
        )
        temp_penalty = base_pace_sec * (temp_pct / 100.0)
        penalty += temp_penalty
        parts.append(f"Hitze {temperature:.0f}°C (+{temp_penalty:.0f}s/km)")

    # Wind
    if wind_speed is not None and wind_speed > 0:
        wind_penalty = wind_speed * _WIND_PENALTY_SEC_PER_KMH
        penalty += wind_penalty
        parts.append(f"Wind {wind_speed:.0f} km/h (+{wind_penalty:.0f}s/km)")

    # Luftfeuchtigkeit
    if humidity is not None and humidity > _HUMIDITY_THRESHOLD:
        hum_pct = (humidity - _HUMIDITY_THRESHOLD) * _HUMIDITY_PENALTY_PCT_PER_POINT
        hum_penalty = base_pace_sec * (hum_pct / 100.0)
        penalty += hum_penalty
        parts.append(f"Feuchte {humidity:.0f}% (+{hum_penalty:.0f}s/km)")

    if penalty == 0.0:
        return None

    return WeatherAdjustment(
        temperature_celsius=temperature,
        wind_speed_kmh=wind_speed,
        humidity_percent=humidity,
        penalty_sec_per_km=round(penalty, 1),
        description=", ".join(parts),
    )


# ---------------------------------------------------------------------------
# Normalisierung
# ---------------------------------------------------------------------------


def _normalize_to_target(
    paces: list[float],
    distances: list[float],
    target_total_sec: int,
) -> list[float]:
    """Skaliert alle Paces proportional, sodass die Gesamtzeit exakt der Zielzeit entspricht."""
    current_total = sum(p * d for p, d in zip(paces, distances))
    if current_total <= 0:
        return paces

    scale = target_total_sec / current_total
    return [p * scale for p in paces]


# ---------------------------------------------------------------------------
# Formatierung
# ---------------------------------------------------------------------------


def _format_pace_sec(pace_sec: float) -> str:
    """Formatiert Pace (Sekunden/km) als M:SS String."""
    pace_min = pace_sec / 60.0
    mins = int(pace_min)
    secs = int(round((pace_min - mins) * 60))
    if secs == 60:
        mins += 1
        secs = 0
    return f"{mins}:{secs:02d}"


def _format_duration(total_seconds: int) -> str:
    """Formatiert Dauer in Sekunden als H:MM:SS oder MM:SS."""
    hours = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def _build_adjustment_note(elevation_adj_sec: float) -> str | None:
    """Erzeugt Hinweis-Text fuer Hoehen-Anpassung pro km."""
    if abs(elevation_adj_sec) < 1.0:
        return None
    if elevation_adj_sec > 0:
        return f"Bergauf +{elevation_adj_sec:.0f}s"
    return f"Bergab {elevation_adj_sec:.0f}s"


def _build_notes(
    strategy: str,
    weather: WeatherAdjustment | None,
    elevation: list[ElevationSegment],
) -> list[str]:
    """Erzeugt allgemeine Tipps fuer die Pacing-Strategie."""
    notes: list[str] = []

    if strategy == "negative":
        notes.append("Starte bewusst langsamer — die zweite Hälfte wird schneller.")
    elif strategy == "effort_based":
        notes.append("Pace variiert mit dem Höhenprofil — halte die Belastung konstant.")

    total_gain = sum(s.gain_m for s in elevation)
    if total_gain > 100:
        notes.append(f"Gesamtanstieg: {total_gain:.0f}m — spare Energie für die Anstiege.")

    if weather and weather.penalty_sec_per_km > 3:
        notes.append(f"Wetter-Anpassung: {weather.description}")
        notes.append("Trinke frühzeitig und regelmäßig bei diesen Bedingungen.")

    return notes


# ---------------------------------------------------------------------------
# Splits → Segments Konvertierung (fuer FIT-Export + Wochenplan)
# ---------------------------------------------------------------------------

_GROUPING_TOLERANCE_SEC = 3.0  # km mit <=3s Pace-Differenz werden zusammengefasst
_PACE_BAND_SEC = 10.0  # ±10s Toleranzband um die Zielpace fuer FIT-Export


def pacing_splits_to_segments(splits: list[KmPacingSplit]) -> list[Segment]:
    """Konvertiert Pacing-Splits zu Segment-Objekten fuer FIT-Export.

    Aufeinanderfolgende km mit aehnlicher Pace (<=3 sec/km) werden
    zu einem einzelnen Segment zusammengefasst. Auf die Zielpace wird
    ein Toleranzband von ±10 sec/km angewendet, damit die Uhr nicht
    bei minimalen Abweichungen alarmiert.
    """
    from app.models.segment import Segment

    if not splits:
        return []

    groups: list[list[KmPacingSplit]] = []
    current_group: list[KmPacingSplit] = [splits[0]]

    for split in splits[1:]:
        ref_pace = current_group[0].target_pace_sec_per_km
        if abs(split.target_pace_sec_per_km - ref_pace) <= _GROUPING_TOLERANCE_SEC:
            current_group.append(split)
        else:
            groups.append(current_group)
            current_group = [split]
    groups.append(current_group)

    segments: list[Segment] = []
    for i, group in enumerate(groups):
        total_dist = round(sum(s.distance_km for s in group), 2)
        paces = [s.target_pace_sec_per_km for s in group]
        fastest = min(paces)
        slowest = max(paces)

        # Toleranzband: schnellere Grenze = fastest - Band, langsamere = slowest + Band
        pace_min_sec = max(fastest - _PACE_BAND_SEC, 60.0)  # nicht unter 1:00/km
        pace_max_sec = slowest + _PACE_BAND_SEC

        segments.append(
            Segment(
                position=i,
                segment_type="steady",
                target_distance_km=total_dist,
                target_pace_min=_format_pace_sec(pace_min_sec),
                target_pace_max=_format_pace_sec(pace_max_sec),
            )
        )

    return segments
