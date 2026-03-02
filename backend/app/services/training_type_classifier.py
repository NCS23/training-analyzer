"""Regelbasierte Training Type Klassifizierung.

Erkennt automatisch den Trainingstyp basierend auf:
- HR-Zonen-Verteilung (Karvonen 5-Zone oder 3-Zone Fallback)
- Session-Dauer
- Lap-Analyse (Anzahl, HR-Variabilitaet, Pace-Konsistenz)
"""

from dataclasses import dataclass
from typing import Optional

# --- Konfigurierbare Schwellenwerte ---


@dataclass(frozen=True)
class ClassifierThresholds:
    """Schwellenwerte fuer die Training Type Erkennung."""

    # Recovery: niedrige HR + kurze Dauer
    recovery_max_duration_min: int = 45
    recovery_max_hr_zone_pct: float = 60.0  # Max % in Zone 2+

    # Easy Run: moderate HR, mittlere Dauer
    easy_min_duration_min: int = 20
    easy_max_duration_min: int = 60
    easy_max_zone3_plus_pct: float = 15.0  # Max % in Zone 3+

    # Long Run: lange Dauer, niedrige-moderate HR
    long_run_min_duration_min: int = 75
    long_run_max_zone4_plus_pct: float = 15.0  # Max % in Zone 4+

    # Tempo: Mehrheit in Zone 3, geringe Pace-Varianz
    tempo_min_zone3_pct: float = 40.0  # Min % in Zone 3
    tempo_max_pace_cv: float = 0.15  # Max Pace-Variationskoeffizient

    # Intervals: hohe HR-Variabilitaet, mehrere Laps
    intervals_min_laps: int = 3
    intervals_min_high_hr_laps_pct: float = 25.0  # % Laps mit Zone 4+ HR

    # Race: durchgehend hohe Intensitaet
    race_min_zone4_plus_pct: float = 60.0  # Min % in Zone 4+
    race_min_duration_min: int = 10

    # Progression: systematisch abnehmende Pace
    progression_min_laps: int = 4
    progression_min_pace_drop_pct: float = 10.0  # Letzte Haelfte >= 10% schneller

    # Fartlek: gemischte Pace, moderate HR-Variabilitaet
    fartlek_min_laps: int = 4
    fartlek_min_pace_cv: float = 0.10
    fartlek_max_pace_cv: float = 0.30

    # Repetitions: kurze, schnelle Wiederholungen
    repetitions_min_laps: int = 4
    repetitions_max_work_lap_duration: int = 120  # Max 2 min pro Work-Lap


DEFAULT_THRESHOLDS = ClassifierThresholds()


# --- Datenstrukturen ---


@dataclass
class ClassificationResult:
    """Ergebnis der Training Type Klassifizierung."""

    training_type: str
    confidence: int  # 0-100
    reasons: list[str]


@dataclass
class SessionMetrics:
    """Aggregierte Session-Metriken fuer die Klassifizierung."""

    duration_sec: int
    hr_avg: Optional[int]
    hr_max: Optional[int]
    distance_km: Optional[float]
    laps: list[dict]
    hr_zone_distribution: Optional[dict]
    pace_values: list[float]  # min/km pro Lap


# --- Classifier ---


def classify_training_type(
    duration_sec: int,
    hr_avg: Optional[int],  # noqa: ARG001
    hr_max: Optional[int],  # noqa: ARG001
    distance_km: Optional[float],  # noqa: ARG001
    laps: Optional[list[dict]],
    hr_zone_distribution: Optional[dict],
    thresholds: Optional[ClassifierThresholds] = None,
) -> ClassificationResult:
    """Klassifiziert den Trainingstyp basierend auf Session-Metriken.

    Returns:
        ClassificationResult mit training_type, confidence (0-100), und Begründungen.
    """
    t = thresholds or DEFAULT_THRESHOLDS
    laps = laps or []

    duration_min = duration_sec / 60

    # Extrahiere Zone-Prozentsaetze
    zone_pcts = _extract_zone_percentages(hr_zone_distribution)

    # Pace-Werte aus Laps extrahieren
    pace_values = _extract_pace_values(laps)

    # HR-Verteilung ueber Laps
    lap_hr_stats = _analyze_lap_hr(laps)

    # Kandidaten mit Scores berechnen
    candidates: list[tuple[str, int, list[str]]] = []

    # 1. Race Check (hoechste Prioritaet bei extremer Intensitaet)
    race_score, race_reasons = _check_race(
        duration_min,
        zone_pcts,
        t,
    )
    if race_score > 0:
        candidates.append(("race", race_score, race_reasons))

    # 2. Intervals Check
    interval_score, interval_reasons = _check_intervals(
        laps,
        lap_hr_stats,
        t,
    )
    if interval_score > 0:
        candidates.append(("intervals", interval_score, interval_reasons))

    # 3. Repetitions Check (vor Tempo — kurze schnelle Laps)
    reps_score, reps_reasons = _check_repetitions(
        laps,
        lap_hr_stats,
        t,
    )
    if reps_score > 0:
        candidates.append(("repetitions", reps_score, reps_reasons))

    # 4. Progression Check (vor Tempo — abnehmende Pace)
    prog_score, prog_reasons = _check_progression(
        laps,
        pace_values,
        zone_pcts,
        t,
    )
    if prog_score > 0:
        candidates.append(("progression", prog_score, prog_reasons))

    # 5. Tempo Check
    tempo_score, tempo_reasons = _check_tempo(
        duration_min,
        zone_pcts,
        pace_values,
        t,
    )
    if tempo_score > 0:
        candidates.append(("tempo", tempo_score, tempo_reasons))

    # 6. Fartlek Check (nach Tempo — gemischte Pace)
    fartlek_score, fartlek_reasons = _check_fartlek(
        laps,
        pace_values,
        lap_hr_stats,
        t,
    )
    if fartlek_score > 0:
        candidates.append(("fartlek", fartlek_score, fartlek_reasons))

    # 7. Long Run Check
    long_run_score, long_run_reasons = _check_long_run(
        duration_min,
        zone_pcts,
        t,
    )
    if long_run_score > 0:
        candidates.append(("long_run", long_run_score, long_run_reasons))

    # 8. Recovery Check
    recovery_score, recovery_reasons = _check_recovery(
        duration_min,
        zone_pcts,
        t,
    )
    if recovery_score > 0:
        candidates.append(("recovery", recovery_score, recovery_reasons))

    # 9. Easy Run (Default-Kandidat)
    easy_score, easy_reasons = _check_easy(
        duration_min,
        zone_pcts,
        t,
    )
    if easy_score > 0:
        candidates.append(("easy", easy_score, easy_reasons))

    # Bester Kandidat
    if not candidates:
        return ClassificationResult(
            training_type="easy",
            confidence=20,
            reasons=["Keine klare Zuordnung moeglich, Fallback auf Easy Run"],
        )

    candidates.sort(key=lambda c: c[1], reverse=True)
    best = candidates[0]

    return ClassificationResult(
        training_type=best[0],
        confidence=best[1],
        reasons=best[2],
    )


# --- Rule Checks ---


def _check_race(
    duration_min: float,
    zone_pcts: dict[str, float],
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Wettkampf/Race ist."""
    reasons: list[str] = []
    score = 0

    high_zone_pct = zone_pcts.get("zone_4_plus", 0)

    if high_zone_pct >= t.race_min_zone4_plus_pct and duration_min >= t.race_min_duration_min:
        score = 70
        reasons.append(f"{high_zone_pct:.0f}% in Zone 4+ (>= {t.race_min_zone4_plus_pct}%)")
        reasons.append(f"Dauer {duration_min:.0f} min (>= {t.race_min_duration_min} min)")

        # Bonus fuer sehr hohen HR-Anteil
        if high_zone_pct >= 80:
            score += 15
            reasons.append("Sehr hohe durchgehende Intensitaet")
        elif high_zone_pct >= 70:
            score += 10

    return score, reasons


def _check_intervals(
    laps: list[dict],
    lap_hr_stats: dict,
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Intervalltraining ist."""
    reasons: list[str] = []
    score = 0

    num_laps = len(laps)
    if num_laps < t.intervals_min_laps:
        return 0, []

    high_hr_laps = lap_hr_stats.get("high_hr_lap_count", 0)
    high_hr_pct = (high_hr_laps / num_laps * 100) if num_laps > 0 else 0

    hr_variability = lap_hr_stats.get("hr_cv", 0)

    if high_hr_pct >= t.intervals_min_high_hr_laps_pct:
        score = 60
        reasons.append(f"{high_hr_laps}/{num_laps} Laps mit hoher HR")

        # Bonus fuer HR-Variabilitaet (typisch fuer Intervalle)
        if hr_variability > 0.10:
            score += 20
            reasons.append(f"Hohe HR-Variabilitaet (CV={hr_variability:.2f})")
        elif hr_variability > 0.05:
            score += 10
            reasons.append(f"Moderate HR-Variabilitaet (CV={hr_variability:.2f})")

        # Bonus fuer viele Laps
        if num_laps >= 6:
            score += 5
            reasons.append(f"{num_laps} Laps")

    return score, reasons


def _check_tempo(
    duration_min: float,
    zone_pcts: dict[str, float],
    pace_values: list[float],
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Tempodauerlauf ist."""
    reasons: list[str] = []
    score = 0

    zone3_pct = zone_pcts.get("zone_3", 0)

    if zone3_pct >= t.tempo_min_zone3_pct:
        score = 55
        reasons.append(f"{zone3_pct:.0f}% in Zone 3 (>= {t.tempo_min_zone3_pct}%)")

        # Pace-Konsistenz pruefen
        if len(pace_values) >= 2:
            pace_cv = _coefficient_of_variation(pace_values)
            if pace_cv <= t.tempo_max_pace_cv:
                score += 20
                reasons.append(f"Konstante Pace (CV={pace_cv:.2f})")
            elif pace_cv <= t.tempo_max_pace_cv * 1.5:
                score += 10

        # Bonus fuer moderate Dauer
        if 20 <= duration_min <= 60:
            score += 5
            reasons.append(f"Typische Tempo-Dauer ({duration_min:.0f} min)")

    return score, reasons


def _check_long_run(
    duration_min: float,
    zone_pcts: dict[str, float],
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Long Run ist."""
    reasons: list[str] = []
    score = 0

    if duration_min >= t.long_run_min_duration_min:
        score = 65
        reasons.append(f"Dauer {duration_min:.0f} min (>= {t.long_run_min_duration_min} min)")

        zone4_plus = zone_pcts.get("zone_4_plus", 0)
        if zone4_plus <= t.long_run_max_zone4_plus_pct:
            score += 15
            reasons.append(f"Niedrige Intensitaet ({zone4_plus:.0f}% Zone 4+)")
        elif zone4_plus <= t.long_run_max_zone4_plus_pct * 2:
            score += 5

        # Bonus fuer sehr lange Laeufe
        if duration_min >= 120:
            score += 10
            reasons.append("Sehr langer Lauf (>= 120 min)")

    return score, reasons


def _check_recovery(
    duration_min: float,
    zone_pcts: dict[str, float],
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Recovery Run ist."""
    reasons: list[str] = []
    score = 0

    # Ohne HR-Daten kann Recovery nicht sicher bestimmt werden
    if not zone_pcts:
        return 0, []

    zone2_plus = zone_pcts.get("zone_2_plus", 0)

    if duration_min <= t.recovery_max_duration_min and zone2_plus <= t.recovery_max_hr_zone_pct:
        score = 60
        reasons.append(f"Kurze Dauer ({duration_min:.0f} min)")
        reasons.append(f"Niedrige Intensitaet ({zone2_plus:.0f}% in Zone 2+)")

        # Bonus fuer sehr niedrige HR
        if zone2_plus <= 30:
            score += 20
            reasons.append("Sehr niedrige HR-Verteilung")
        elif zone2_plus <= 45:
            score += 10

    return score, reasons


def _check_easy(
    duration_min: float,
    zone_pcts: dict[str, float],
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Easy Run ist."""
    reasons: list[str] = []
    score = 0

    zone3_plus = zone_pcts.get("zone_3_plus", 0)

    if zone3_plus <= t.easy_max_zone3_plus_pct:
        score = 45
        reasons.append(f"Geringe Intensitaet ({zone3_plus:.0f}% in Zone 3+)")

        if t.easy_min_duration_min <= duration_min <= t.easy_max_duration_min:
            score += 15
            reasons.append(f"Typische Easy-Dauer ({duration_min:.0f} min)")
        elif duration_min >= t.easy_min_duration_min:
            score += 5

    return score, reasons


def _check_progression(
    _laps: list[dict],
    pace_values: list[float],
    zone_pcts: dict[str, float],
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Steigerungslauf ist (Pace nimmt systematisch ab)."""
    reasons: list[str] = []
    score = 0

    if len(pace_values) < t.progression_min_laps:
        return 0, []

    # Vergleiche erste Haelfte vs zweite Haelfte
    mid = len(pace_values) // 2
    first_half_avg = sum(pace_values[:mid]) / mid
    second_half_avg = sum(pace_values[mid:]) / (len(pace_values) - mid)

    if first_half_avg <= 0:
        return 0, []

    # Pace-Drop: zweite Haelfte schneller (niedrigere min/km) als erste
    pace_drop_pct = ((first_half_avg - second_half_avg) / first_half_avg) * 100

    if pace_drop_pct >= t.progression_min_pace_drop_pct:
        score = 65
        reasons.append(
            f"Pace-Abnahme {pace_drop_pct:.0f}% "
            f"(>= {t.progression_min_pace_drop_pct}%)"
        )

        # Zone 3+ zwischen 30-70% (Start Easy, Ende Tempo)
        zone3_plus = zone_pcts.get("zone_3_plus", 0)
        if 30 <= zone3_plus <= 70:
            score += 10
            reasons.append(f"Moderate Intensitaet ({zone3_plus:.0f}% Zone 3+)")

        # Bonus fuer monoton abnehmende Pace
        decreasing = sum(
            1 for i in range(1, len(pace_values)) if pace_values[i] < pace_values[i - 1]
        )
        monotonic_pct = decreasing / (len(pace_values) - 1) * 100
        if monotonic_pct >= 70:
            score += 10
            reasons.append(f"Nahezu monotone Pace-Abnahme ({monotonic_pct:.0f}%)")

    return score, reasons


def _check_fartlek(
    laps: list[dict],
    pace_values: list[float],
    lap_hr_stats: dict,
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session ein Fartlek (Fahrtspiel) ist — gemischte Pace."""
    reasons: list[str] = []
    score = 0

    if len(laps) < t.fartlek_min_laps or len(pace_values) < t.fartlek_min_laps:
        return 0, []

    pace_cv = _coefficient_of_variation(pace_values)
    hr_cv = lap_hr_stats.get("hr_cv", 0)

    if t.fartlek_min_pace_cv <= pace_cv <= t.fartlek_max_pace_cv:
        score = 50
        reasons.append(f"Gemischte Pace (CV={pace_cv:.2f})")

        # Moderate HR-Variabilitaet (0.05-0.12)
        if 0.05 <= hr_cv <= 0.12:
            score += 15
            reasons.append(f"Moderate HR-Variabilitaet (CV={hr_cv:.2f})")
        elif hr_cv > 0:
            score += 5

        # Bonus fuer viele Laps
        if len(laps) >= 6:
            score += 5
            reasons.append(f"{len(laps)} Laps")

    return score, reasons


def _check_repetitions(
    laps: list[dict],
    lap_hr_stats: dict,
    t: ClassifierThresholds,
) -> tuple[int, list[str]]:
    """Prueft ob die Session Repetitions sind — kurze, schnelle Wiederholungen."""
    reasons: list[str] = []
    score = 0

    num_laps = len(laps)
    if num_laps < t.repetitions_min_laps:
        return 0, []

    # Zaehle kurze Laps mit hoher HR
    short_fast_count = 0
    for lap in laps:
        duration = lap.get("duration_seconds", 0)
        avg_hr = lap.get("avg_hr_bpm")
        if duration <= t.repetitions_max_work_lap_duration and avg_hr and avg_hr > 160:
            short_fast_count += 1

    short_fast_pct = (short_fast_count / num_laps * 100) if num_laps > 0 else 0

    if short_fast_pct >= 25 and short_fast_count >= 3:
        score = 60
        reasons.append(f"{short_fast_count} kurze schnelle Laps (<= 2 min, HR > 160)")

        # HR-Variabilitaet (typisch fuer Wechsel zwischen schnell und Pause)
        hr_cv = lap_hr_stats.get("hr_cv", 0)
        if hr_cv > 0.10:
            score += 15
            reasons.append(f"Hohe HR-Variabilitaet (CV={hr_cv:.2f})")
        elif hr_cv > 0.05:
            score += 5

        # Unterscheidung zu Intervallen: Repetitions haben kuerzere Work-Phasen
        avg_work_duration = sum(
            lap.get("duration_seconds", 0)
            for lap in laps
            if lap.get("avg_hr_bpm", 0) and lap["avg_hr_bpm"] > 160
        )
        work_laps = sum(1 for lap in laps if lap.get("avg_hr_bpm", 0) and lap["avg_hr_bpm"] > 160)
        if work_laps > 0:
            avg_dur = avg_work_duration / work_laps
            if avg_dur <= 90:
                score += 15
                reasons.append(f"Sehr kurze Work-Dauer {avg_dur:.0f}s (<= 90s)")
            elif avg_dur <= t.repetitions_max_work_lap_duration:
                score += 10
                reasons.append(f"Kurze Work-Dauer {avg_dur:.0f}s (<= 120s)")

    return score, reasons


# --- Helpers ---


def _extract_zone_percentages(hr_zones: Optional[dict]) -> dict[str, float]:
    """Extrahiert Zone-Prozentsaetze aus der HR-Zone-Verteilung.

    Gibt aggregierte Werte zurueck:
    - zone_1, zone_2, zone_3, zone_4, zone_5 (einzeln)
    - zone_2_plus: Zone 2 und hoeher
    - zone_3_plus: Zone 3 und hoeher
    - zone_4_plus: Zone 4 und hoeher
    """
    if not hr_zones:
        return {}

    result: dict[str, float] = {}

    # Karvonen 5-Zone Keys: zone_1_recovery, zone_2_base, zone_3_tempo, zone_4_threshold, zone_5_vo2max
    # 3-Zone Keys: zone_1_recovery, zone_2_base, zone_3_tempo
    zone_values: list[float] = []
    for key, zone_data in hr_zones.items():
        pct = zone_data.get("percentage", 0) if isinstance(zone_data, dict) else 0

        if "zone_1" in key:
            result["zone_1"] = pct
            zone_values.append(pct)
        elif "zone_2" in key:
            result["zone_2"] = pct
            zone_values.append(pct)
        elif "zone_3" in key:
            result["zone_3"] = pct
            zone_values.append(pct)
        elif "zone_4" in key:
            result["zone_4"] = pct
            zone_values.append(pct)
        elif "zone_5" in key:
            result["zone_5"] = pct
            zone_values.append(pct)

    # Aggregierte Werte
    result["zone_2_plus"] = sum(result.get(f"zone_{i}", 0) for i in range(2, 6))
    result["zone_3_plus"] = sum(result.get(f"zone_{i}", 0) for i in range(3, 6))
    result["zone_4_plus"] = sum(result.get(f"zone_{i}", 0) for i in range(4, 6))

    return result


def _extract_pace_values(laps: list[dict]) -> list[float]:
    """Extrahiert Pace-Werte aus Working-Laps (ohne Warmup/Cooldown/Rest)."""
    excluded = {"warmup", "cooldown", "rest"}
    pace_values = []

    for lap in laps:
        effective_type = lap.get("user_override") or lap.get("suggested_type") or "steady"
        if effective_type in excluded:
            continue
        pace = lap.get("pace_min_per_km")
        if pace and pace > 0:
            pace_values.append(float(pace))

    return pace_values


def _analyze_lap_hr(laps: list[dict]) -> dict:
    """Analysiert HR-Verteilung ueber Laps."""
    hr_values = []
    high_hr_count = 0

    for lap in laps:
        avg_hr = lap.get("avg_hr_bpm")
        if avg_hr:
            hr_values.append(avg_hr)
            # "Hohe HR" = > 160 bpm (Fallback wenn keine Zonen-Info)
            if avg_hr > 160:
                high_hr_count += 1

    hr_cv = _coefficient_of_variation(hr_values) if len(hr_values) >= 2 else 0

    return {
        "high_hr_lap_count": high_hr_count,
        "hr_cv": hr_cv,
        "hr_values": hr_values,
    }


def _coefficient_of_variation(values: list[float]) -> float:
    """Berechnet den Variationskoeffizienten (Standardabweichung / Mittelwert)."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return (variance**0.5) / mean
