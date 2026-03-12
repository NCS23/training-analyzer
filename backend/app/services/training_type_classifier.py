"""Regelbasierte Training Type Klassifizierung.

Erkennt automatisch den Trainingstyp basierend auf:
- HR-Zonen-Verteilung (Karvonen 5-Zone oder 3-Zone Fallback)
- Session-Dauer
- Lap-Analyse (Anzahl, HR-Variabilitaet, Pace-Konsistenz)

Architektur: Classification Rules als Registry (Open/Closed Principle).
Neuer Trainingstyp = neue _check_*-Funktion + Eintrag in CLASSIFICATION_RULES.
"""

from dataclasses import dataclass
from typing import Callable, Optional

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
    """Vorberechnete Session-Metriken — Input fuer alle Rule Checks."""

    duration_min: float
    laps: list[dict]
    zone_pcts: dict[str, float]
    pace_values: list[float]
    lap_hr_stats: dict


# Type alias fuer Rule-Funktionen
RuleCheck = Callable[
    [SessionMetrics, ClassifierThresholds],
    tuple[str, int, list[str]],
]


# --- Classifier ---


def _build_metrics(
    duration_sec: int,
    laps: list[dict],
    hr_zone_distribution: dict | None,
) -> SessionMetrics:
    """Bereitet Session-Metriken fuer die Rule Checks vor."""
    return SessionMetrics(
        duration_min=duration_sec / 60,
        laps=laps,
        zone_pcts=_extract_zone_percentages(hr_zone_distribution),
        pace_values=_extract_pace_values(laps),
        lap_hr_stats=_analyze_lap_hr(laps),
    )


def classify_training_type(
    duration_sec: int,
    laps: Optional[list[dict]] = None,
    hr_zone_distribution: Optional[dict] = None,
    thresholds: Optional[ClassifierThresholds] = None,
    *,
    # Legacy kwargs — nicht mehr genutzt, aber backward-kompatibel
    hr_avg: Optional[int] = None,  # noqa: ARG001
    hr_max: Optional[int] = None,  # noqa: ARG001
    distance_km: Optional[float] = None,  # noqa: ARG001
) -> ClassificationResult:
    """Klassifiziert den Trainingstyp basierend auf Session-Metriken.

    Returns:
        ClassificationResult mit training_type, confidence (0-100), und Begründungen.
    """
    t = thresholds or DEFAULT_THRESHOLDS
    metrics = _build_metrics(duration_sec, laps or [], hr_zone_distribution)

    candidates = [
        (name, score, reasons)
        for rule in CLASSIFICATION_RULES
        for name, score, reasons in [rule(metrics, t)]
        if score > 0
    ]

    if not candidates:
        return ClassificationResult(
            training_type="easy",
            confidence=20,
            reasons=["Keine klare Zuordnung moeglich, Fallback auf Easy Run"],
        )

    candidates.sort(key=lambda c: c[1], reverse=True)
    best_name, best_score, best_reasons = candidates[0]
    return ClassificationResult(
        training_type=best_name,
        confidence=best_score,
        reasons=best_reasons,
    )


# --- Rule Checks ---


def _check_race(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Wettkampf/Race ist."""
    reasons: list[str] = []
    score = 0

    high_zone_pct = m.zone_pcts.get("zone_4_plus", 0)

    if high_zone_pct >= t.race_min_zone4_plus_pct and m.duration_min >= t.race_min_duration_min:
        score = 70
        reasons.append(f"{high_zone_pct:.0f}% in Zone 4+ (>= {t.race_min_zone4_plus_pct}%)")
        reasons.append(f"Dauer {m.duration_min:.0f} min (>= {t.race_min_duration_min} min)")

        if high_zone_pct >= 80:
            score += 15
            reasons.append("Sehr hohe durchgehende Intensitaet")
        elif high_zone_pct >= 70:
            score += 10

    return "race", score, reasons


def _check_intervals(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Intervalltraining ist."""
    reasons: list[str] = []
    score = 0

    num_laps = len(m.laps)
    if num_laps < t.intervals_min_laps:
        return "intervals", 0, []

    high_hr_laps = m.lap_hr_stats.get("high_hr_lap_count", 0)
    high_hr_pct = (high_hr_laps / num_laps * 100) if num_laps > 0 else 0

    hr_variability = m.lap_hr_stats.get("hr_cv", 0)

    if high_hr_pct >= t.intervals_min_high_hr_laps_pct:
        score = 60
        reasons.append(f"{high_hr_laps}/{num_laps} Laps mit hoher HR")

        if hr_variability > 0.10:
            score += 20
            reasons.append(f"Hohe HR-Variabilitaet (CV={hr_variability:.2f})")
        elif hr_variability > 0.05:
            score += 10
            reasons.append(f"Moderate HR-Variabilitaet (CV={hr_variability:.2f})")

        if num_laps >= 6:
            score += 5
            reasons.append(f"{num_laps} Laps")

    return "intervals", score, reasons


def _check_tempo(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Tempodauerlauf ist."""
    reasons: list[str] = []
    score = 0

    zone3_pct = m.zone_pcts.get("zone_3", 0)

    if zone3_pct >= t.tempo_min_zone3_pct:
        score = 55
        reasons.append(f"{zone3_pct:.0f}% in Zone 3 (>= {t.tempo_min_zone3_pct}%)")

        if len(m.pace_values) >= 2:
            pace_cv = _coefficient_of_variation(m.pace_values)
            if pace_cv <= t.tempo_max_pace_cv:
                score += 20
                reasons.append(f"Konstante Pace (CV={pace_cv:.2f})")
            elif pace_cv <= t.tempo_max_pace_cv * 1.5:
                score += 10

        if 20 <= m.duration_min <= 60:
            score += 5
            reasons.append(f"Typische Tempo-Dauer ({m.duration_min:.0f} min)")

    return "tempo", score, reasons


def _check_long_run(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Long Run ist."""
    reasons: list[str] = []
    score = 0

    if m.duration_min >= t.long_run_min_duration_min:
        score = 65
        reasons.append(f"Dauer {m.duration_min:.0f} min (>= {t.long_run_min_duration_min} min)")

        zone4_plus = m.zone_pcts.get("zone_4_plus", 0)
        if zone4_plus <= t.long_run_max_zone4_plus_pct:
            score += 15
            reasons.append(f"Niedrige Intensitaet ({zone4_plus:.0f}% Zone 4+)")
        elif zone4_plus <= t.long_run_max_zone4_plus_pct * 2:
            score += 5

        if m.duration_min >= 120:
            score += 10
            reasons.append("Sehr langer Lauf (>= 120 min)")

    return "long_run", score, reasons


def _check_recovery(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Recovery Run ist."""
    reasons: list[str] = []
    score = 0

    if not m.zone_pcts:
        return "recovery", 0, []

    zone2_plus = m.zone_pcts.get("zone_2_plus", 0)

    if m.duration_min <= t.recovery_max_duration_min and zone2_plus <= t.recovery_max_hr_zone_pct:
        score = 60
        reasons.append(f"Kurze Dauer ({m.duration_min:.0f} min)")
        reasons.append(f"Niedrige Intensitaet ({zone2_plus:.0f}% in Zone 2+)")

        if zone2_plus <= 30:
            score += 20
            reasons.append("Sehr niedrige HR-Verteilung")
        elif zone2_plus <= 45:
            score += 10

    return "recovery", score, reasons


def _check_easy(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Easy Run ist."""
    reasons: list[str] = []
    score = 0

    zone3_plus = m.zone_pcts.get("zone_3_plus", 0)

    if zone3_plus <= t.easy_max_zone3_plus_pct:
        score = 45
        reasons.append(f"Geringe Intensitaet ({zone3_plus:.0f}% in Zone 3+)")

        if t.easy_min_duration_min <= m.duration_min <= t.easy_max_duration_min:
            score += 15
            reasons.append(f"Typische Easy-Dauer ({m.duration_min:.0f} min)")
        elif m.duration_min >= t.easy_min_duration_min:
            score += 5

    return "easy", score, reasons


def _check_progression(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Steigerungslauf ist (Pace nimmt systematisch ab)."""
    reasons: list[str] = []
    score = 0

    if len(m.pace_values) < t.progression_min_laps:
        return "progression", 0, []

    mid = len(m.pace_values) // 2
    first_half_avg = sum(m.pace_values[:mid]) / mid
    second_half_avg = sum(m.pace_values[mid:]) / (len(m.pace_values) - mid)

    if first_half_avg <= 0:
        return "progression", 0, []

    pace_drop_pct = ((first_half_avg - second_half_avg) / first_half_avg) * 100

    if pace_drop_pct >= t.progression_min_pace_drop_pct:
        score = 65
        reasons.append(f"Pace-Abnahme {pace_drop_pct:.0f}% (>= {t.progression_min_pace_drop_pct}%)")

        zone3_plus = m.zone_pcts.get("zone_3_plus", 0)
        if 30 <= zone3_plus <= 70:
            score += 10
            reasons.append(f"Moderate Intensitaet ({zone3_plus:.0f}% Zone 3+)")

        decreasing = sum(
            1 for i in range(1, len(m.pace_values)) if m.pace_values[i] < m.pace_values[i - 1]
        )
        monotonic_pct = decreasing / (len(m.pace_values) - 1) * 100
        if monotonic_pct >= 70:
            score += 10
            reasons.append(f"Nahezu monotone Pace-Abnahme ({monotonic_pct:.0f}%)")

    return "progression", score, reasons


def _check_fartlek(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session ein Fartlek (Fahrtspiel) ist — gemischte Pace."""
    reasons: list[str] = []
    score = 0

    if len(m.laps) < t.fartlek_min_laps or len(m.pace_values) < t.fartlek_min_laps:
        return "fartlek", 0, []

    pace_cv = _coefficient_of_variation(m.pace_values)
    hr_cv = m.lap_hr_stats.get("hr_cv", 0)

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
        if len(m.laps) >= 6:
            score += 5
            reasons.append(f"{len(m.laps)} Laps")

    return "fartlek", score, reasons


def _check_repetitions(
    m: SessionMetrics,
    t: ClassifierThresholds,
) -> tuple[str, int, list[str]]:
    """Prueft ob die Session Repetitions sind — kurze, schnelle Wiederholungen."""
    reasons: list[str] = []
    score = 0

    num_laps = len(m.laps)
    if num_laps < t.repetitions_min_laps:
        return "repetitions", 0, []

    # Zaehle kurze Laps mit hoher HR
    short_fast_count = 0
    for lap in m.laps:
        duration = lap.get("duration_seconds", 0)
        avg_hr = lap.get("avg_hr_bpm")
        if duration <= t.repetitions_max_work_lap_duration and avg_hr and avg_hr > 160:
            short_fast_count += 1

    short_fast_pct = (short_fast_count / num_laps * 100) if num_laps > 0 else 0

    if short_fast_pct >= 25 and short_fast_count >= 3:
        score = 60
        reasons.append(f"{short_fast_count} kurze schnelle Laps (<= 2 min, HR > 160)")

        # HR-Variabilitaet (typisch fuer Wechsel zwischen schnell und Pause)
        hr_cv = m.lap_hr_stats.get("hr_cv", 0)
        if hr_cv > 0.10:
            score += 15
            reasons.append(f"Hohe HR-Variabilitaet (CV={hr_cv:.2f})")
        elif hr_cv > 0.05:
            score += 5

        # Unterscheidung zu Intervallen: Repetitions haben kuerzere Work-Phasen
        avg_work_duration = sum(
            lap.get("duration_seconds", 0)
            for lap in m.laps
            if lap.get("avg_hr_bpm", 0) and lap["avg_hr_bpm"] > 160
        )
        work_laps = sum(1 for lap in m.laps if lap.get("avg_hr_bpm", 0) and lap["avg_hr_bpm"] > 160)
        if work_laps > 0:
            avg_dur = avg_work_duration / work_laps
            if avg_dur <= 90:
                score += 15
                reasons.append(f"Sehr kurze Work-Dauer {avg_dur:.0f}s (<= 90s)")
            elif avg_dur <= t.repetitions_max_work_lap_duration:
                score += 10
                reasons.append(f"Kurze Work-Dauer {avg_dur:.0f}s (<= 120s)")

    return "repetitions", score, reasons


# --- Rule Registry (OCP: neuer Typ = neue Funktion + Eintrag hier) ---

CLASSIFICATION_RULES: list[RuleCheck] = [
    _check_race,
    _check_intervals,
    _check_repetitions,
    _check_progression,
    _check_tempo,
    _check_fartlek,
    _check_long_run,
    _check_recovery,
    _check_easy,
]


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
