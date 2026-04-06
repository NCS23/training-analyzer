"""Fitness-Score Engine — Banister Fitness-Fatigue-Modell.

Wissenschaftliche Grundlage:
- Banister et al. (1975): Impulse-Response-Modell
- Edwards (1993): HR-Zonen-basierter TRIMP
- Seiler (2010): Polarisierte Intensitätsverteilung (80/20)
- ACWR: Acute:Chronic Workload Ratio (EWMA-basiert)

Berechnung:
1. TRIMP pro Session (Edwards Methode: Zeit in Zone × Gewicht)
2. CTL = EWMA über ~42 Tage (Fitness)
3. ATL = EWMA über ~7 Tage (Ermüdung)
4. TSB = CTL - ATL (Form)
5. Score = CTL normalisiert auf 0-100
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.database.models import WorkoutModel

# ---------------------------------------------------------------------------
# Konstanten (trainingswissenschaftlich fundiert)
# ---------------------------------------------------------------------------

# Edwards TRIMP Gewichte: Zone 1-5
EDWARDS_ZONE_WEIGHTS: dict[int, float] = {1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0, 5: 5.0}

# Karvonen HR-Zonen-Grenzen (% der HRR = Heart Rate Reserve)
ZONE_BOUNDARIES: list[float] = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]

# EWMA Zeitkonstanten (Tage)
CTL_TAU = 42  # Chronic Training Load (Fitness)
ATL_TAU = 7  # Acute Training Load (Ermüdung)

# TSB Schwellwerte für Form-Indikator
TSB_FRESH_THRESHOLD = 10.0
TSB_FATIGUED_THRESHOLD = -10.0

# ACWR Schwellwerte (evidenzbasiert, Gabbett 2016)
ACWR_LOW = 0.5
ACWR_OPTIMAL_LOW = 0.8
ACWR_OPTIMAL_HIGH = 1.3
ACWR_WARNING = 1.5

# Trend: Mindestdifferenz in % für steigend/fallend
TREND_THRESHOLD_PERCENT = 2.0
TREND_LOOKBACK_DAYS = 14

# Kraft-Session TRIMP-Äquivalent
STRENGTH_RPE_FACTOR = 0.5
STRENGTH_DEFAULT_FACTOR = 2.0


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------


@dataclass
class FitnessMetrics:
    """Ergebnis der CTL/ATL/TSB Berechnung."""

    ctl: float = 0.0
    atl: float = 0.0
    tsb: float = 0.0
    ctl_history: list[tuple[date, float]] = field(default_factory=list)
    atl_history: list[tuple[date, float]] = field(default_factory=list)
    tsb_history: list[tuple[date, float]] = field(default_factory=list)


@dataclass
class FormIndicator:
    """Frische/Ermüdungs-Bewertung."""

    status: str  # "fresh" | "normal" | "fatigued"
    label: str  # "Frisch" | "Normal" | "Ermüdet"
    color: str  # "green" | "yellow" | "orange"
    recommendation: str


@dataclass
class ACWRResult:
    """Acute:Chronic Workload Ratio."""

    ratio: float
    zone: str  # "low" | "optimal" | "warning" | "danger"
    message: str


# ---------------------------------------------------------------------------
# TRIMP-Berechnung (Edwards Methode)
# ---------------------------------------------------------------------------


def _get_hr_zone(hr: float, resting_hr: int, max_hr: int) -> int:
    """Bestimme Karvonen-Zone (1-5) für einen HR-Wert."""
    if max_hr <= resting_hr:
        return 1
    hrr = max_hr - resting_hr
    pct = (hr - resting_hr) / hrr
    if pct < ZONE_BOUNDARIES[0]:
        return 1
    for zone_idx in range(len(ZONE_BOUNDARIES) - 1):
        if pct < ZONE_BOUNDARIES[zone_idx + 1]:
            return zone_idx + 1
    return 5


def _trimp_from_hr_timeseries(
    hr_data: Sequence[int | float],
    resting_hr: int,
    max_hr: int,
) -> float:
    """TRIMP aus sekündlichen HR-Daten (genaueste Methode).

    Summiert Zeit (in Minuten) pro Zone × Edwards-Gewicht.
    """
    zone_seconds: dict[int, float] = defaultdict(float)
    for hr_value in hr_data:
        if hr_value and hr_value > 0:
            zone = _get_hr_zone(float(hr_value), resting_hr, max_hr)
            zone_seconds[zone] += 1.0

    trimp = 0.0
    for zone, seconds in zone_seconds.items():
        minutes = seconds / 60.0
        trimp += minutes * EDWARDS_ZONE_WEIGHTS.get(zone, 1.0)
    return round(trimp, 1)


def _trimp_from_hr_zones_json(hr_zones_json: str, duration_sec: int) -> float:
    """TRIMP aus bereits berechneter Zonen-Verteilung.

    hr_zones_json Format: {"zone1_pct": 20, "zone2_pct": 50, ...}
    oder [{"zone": 1, "percent": 20}, ...]
    """
    try:
        zones_data = json.loads(hr_zones_json)
    except (json.JSONDecodeError, TypeError):
        return 0.0

    total_minutes = duration_sec / 60.0
    trimp = 0.0

    if isinstance(zones_data, dict):
        for key, value in zones_data.items():
            # Format A: {"zone_1_recovery": {"percentage": 33.3, "zone": 1, ...}}
            # Format B: {"zone1_pct": 20, ...}
            zone_num = None
            pct: float = 0.0

            if isinstance(value, dict):
                zone_num = value.get("zone")
                raw_pct = value.get("percentage", value.get("pct", 0))
                pct = float(raw_pct) if raw_pct is not None else 0.0
            elif isinstance(value, (int, float)):
                pct = float(value)
                if "zone" in key.lower():
                    for char in key:
                        if char.isdigit():
                            zone_num = int(char)
                            break

            if zone_num and 1 <= zone_num <= 5 and pct > 0:
                minutes = total_minutes * (pct / 100.0)
                trimp += minutes * EDWARDS_ZONE_WEIGHTS.get(zone_num, 1.0)
    elif isinstance(zones_data, list):
        for entry in zones_data:
            zone_num = entry.get("zone")
            pct = entry.get("percent", entry.get("pct", 0))
            if zone_num and 1 <= zone_num <= 5:
                minutes = total_minutes * (float(pct) / 100.0)
                trimp += minutes * EDWARDS_ZONE_WEIGHTS.get(zone_num, 1.0)

    return round(trimp, 1)


def _trimp_from_avg_hr(
    avg_hr: int,
    duration_sec: int,
    resting_hr: int,
    max_hr: int,
) -> float:
    """TRIMP-Schätzung aus Durchschnitts-HR (gröbste Methode)."""
    zone = _get_hr_zone(float(avg_hr), resting_hr, max_hr)
    minutes = duration_sec / 60.0
    return round(minutes * EDWARDS_ZONE_WEIGHTS.get(zone, 1.0), 1)


def _trimp_for_strength(rpe: int | None, duration_sec: int | None) -> float:
    """TRIMP-Äquivalent für Kraft-Sessions (kein HR verfügbar)."""
    duration_min = (duration_sec or 0) / 60.0
    if rpe and rpe > 0:
        return round(rpe * duration_min * STRENGTH_RPE_FACTOR, 1)
    if duration_min > 0:
        return round(duration_min * STRENGTH_DEFAULT_FACTOR, 1)
    return 0.0


def calculate_trimp(session: WorkoutModel) -> float:
    """Berechne Edwards TRIMP für eine Session.

    Priorisierung der HR-Datenquellen:
    1. hr_timeseries_json (sekündlich) → genaueste Berechnung
    2. hr_zones_json (Zonen-Verteilung) → gute Näherung
    3. hr_avg (Durchschnitt) → grobe Schätzung
    4. Kraft: RPE × Dauer → Äquivalent
    5. Fallback: Dauer × Standardfaktor
    """
    resting_hr = session.athlete_resting_hr or 60
    max_hr = session.athlete_max_hr or 190
    duration = session.duration_sec or 0

    # Kraft-Sessions: kein HR, nutze RPE
    if session.workout_type == "strength":
        rpe = session.rpe
        if not rpe and session.exercises_json:
            try:
                data = json.loads(session.exercises_json)
                if isinstance(data, dict):
                    rpe = data.get("rpe")
            except (json.JSONDecodeError, TypeError):
                pass
        return _trimp_for_strength(rpe, duration)

    # Lauf-Sessions: HR-Daten priorisieren
    # 1. Sekündliche HR-Daten
    if session.hr_timeseries_json:
        try:
            hr_data = json.loads(session.hr_timeseries_json)
            if isinstance(hr_data, list) and len(hr_data) > 0:
                return _trimp_from_hr_timeseries(hr_data, resting_hr, max_hr)
        except (json.JSONDecodeError, TypeError):
            pass

    # 2. Zonen-Verteilung
    if session.hr_zones_json and duration > 0:
        trimp = _trimp_from_hr_zones_json(session.hr_zones_json, duration)
        if trimp > 0:
            return trimp

    # 3. Durchschnitts-HR
    if session.hr_avg and session.hr_avg > 0 and duration > 0:
        return _trimp_from_avg_hr(session.hr_avg, duration, resting_hr, max_hr)

    # 4. Fallback: Dauer × Standardfaktor
    if duration > 0:
        return round((duration / 60.0) * STRENGTH_DEFAULT_FACTOR, 1)

    return 0.0


# ---------------------------------------------------------------------------
# CTL / ATL / TSB (EWMA-basiert)
# ---------------------------------------------------------------------------


def _ewma_update(previous: float, new_value: float, tau: int) -> float:
    """Exponentially Weighted Moving Average Update-Schritt."""
    alpha = 1.0 / tau
    return previous * (1.0 - alpha) + new_value * alpha


def calculate_fitness_metrics(
    daily_trimps: dict[date, float],
    up_to_date: date | None = None,
) -> FitnessMetrics:
    """Berechne CTL/ATL/TSB über alle Tage.

    Args:
        daily_trimps: Dict {Datum: Summe-TRIMP-an-diesem-Tag}
        up_to_date: Bis zu welchem Datum berechnen (default: heute)

    Returns:
        FitnessMetrics mit aktuellen Werten und History für Charts
    """
    if not daily_trimps:
        return FitnessMetrics()

    target = up_to_date or date.today()
    start = min(daily_trimps.keys())

    ctl = 0.0
    atl = 0.0
    ctl_history: list[tuple[date, float]] = []
    atl_history: list[tuple[date, float]] = []
    tsb_history: list[tuple[date, float]] = []

    current = start
    while current <= target:
        trimp = daily_trimps.get(current, 0.0)
        ctl = _ewma_update(ctl, trimp, CTL_TAU)
        atl = _ewma_update(atl, trimp, ATL_TAU)
        tsb = ctl - atl

        ctl_history.append((current, round(ctl, 2)))
        atl_history.append((current, round(atl, 2)))
        tsb_history.append((current, round(tsb, 2)))

        current += timedelta(days=1)

    return FitnessMetrics(
        ctl=round(ctl, 2),
        atl=round(atl, 2),
        tsb=round(ctl - atl, 2),
        ctl_history=ctl_history,
        atl_history=atl_history,
        tsb_history=tsb_history,
    )


# ---------------------------------------------------------------------------
# Score-Normalisierung
# ---------------------------------------------------------------------------


def normalize_score(ctl: float) -> int:
    """Normalisiere CTL auf Score 0-100 mit absoluter Referenzskala.

    Verwendet eine logarithmische Kurve basierend auf typischen CTL-Werten
    für verschiedene Trainingsniveaus (Edwards TRIMP):

    - CTL ~10: Gelegenheitssportler (Score ~25)
    - CTL ~30: Regelmäßiges Training 3×/Woche (Score ~50)
    - CTL ~60: Ambitionierter Hobbyathlet (Score ~75)
    - CTL ~80: Gut trainiert, wettkampforientiert (Score ~87)
    - CTL ~120+: Elite / Hochphase (Score ~95+)

    Die logarithmische Kurve sorgt dafür, dass Anfänger schnell
    Fortschritte sehen, während hohe Werte schwerer zu erreichen sind.
    """
    if ctl <= 0:
        return 0

    # Logarithmische Normalisierung: score = k * ln(1 + ctl/c)
    # Kalibriert: CTL=30→50, CTL=60→67, CTL=80→75, CTL=120→85
    raw = 28.0 * math.log(1.0 + ctl / 6.0)
    return min(100, round(raw))


def calculate_split_scores(
    sessions_with_trimp: list[tuple[date, float, str]],
    up_to_date: date | None = None,
) -> tuple[int, int]:
    """Berechne aufgeschlüsselte Scores für Ausdauer und Kraft.

    Args:
        sessions_with_trimp: [(date, trimp, workout_type), ...]
        up_to_date: Bis-Datum

    Returns:
        (endurance_score, strength_score)
    """
    endurance_trimps: dict[date, float] = defaultdict(float)
    strength_trimps: dict[date, float] = defaultdict(float)

    for d, trimp, wtype in sessions_with_trimp:
        if wtype == "strength":
            strength_trimps[d] += trimp
        else:
            endurance_trimps[d] += trimp

    endurance_ctl = 0.0
    strength_ctl = 0.0

    if endurance_trimps:
        metrics = calculate_fitness_metrics(endurance_trimps, up_to_date)
        endurance_ctl = metrics.ctl

    if strength_trimps:
        metrics = calculate_fitness_metrics(strength_trimps, up_to_date)
        strength_ctl = metrics.ctl

    e_score = normalize_score(endurance_ctl)
    s_score = normalize_score(strength_ctl)

    return e_score, s_score


# ---------------------------------------------------------------------------
# Form-Indikator
# ---------------------------------------------------------------------------


def calculate_form(tsb: float) -> FormIndicator:
    """Bestimme Form basierend auf TSB (Training Stress Balance)."""
    if tsb > TSB_FRESH_THRESHOLD:
        return FormIndicator(
            status="fresh",
            label="Frisch",
            color="green",
            recommendation="Guter Tag für ein intensives Training",
        )
    if tsb < TSB_FATIGUED_THRESHOLD:
        return FormIndicator(
            status="fatigued",
            label="Ermüdet",
            color="orange",
            recommendation="Regeneration empfohlen — lockerer Lauf oder Ruhetag",
        )
    return FormIndicator(
        status="normal",
        label="Normal",
        color="yellow",
        recommendation="Normales Training möglich",
    )


# ---------------------------------------------------------------------------
# ACWR (Acute:Chronic Workload Ratio)
# ---------------------------------------------------------------------------


def calculate_acwr(atl: float, ctl: float) -> ACWRResult | None:
    """Berechne ACWR und bewerte das Verletzungsrisiko.

    Returns None wenn CTL zu niedrig (< 1.0) — keine sinnvolle Aussage möglich.
    """
    if ctl < 1.0:
        return None

    ratio = round(atl / ctl, 2)

    if ratio > ACWR_WARNING:
        return ACWRResult(
            ratio=ratio,
            zone="danger",
            message=(
                f"Verletzungsrisiko erhöht — Belastung liegt {ratio:.1f}x "
                "über deinem Gewohnheitsniveau. Reduziere die Intensität."
            ),
        )
    if ratio > ACWR_OPTIMAL_HIGH:
        return ACWRResult(
            ratio=ratio,
            zone="warning",
            message="Belastung über Gewohnheit — Vorsicht bei intensiven Einheiten",
        )
    if ratio < ACWR_LOW:
        return ACWRResult(
            ratio=ratio,
            zone="low",
            message="Du trainierst deutlich weniger als gewohnt — Fitness könnte abnehmen",
        )
    if ratio < ACWR_OPTIMAL_LOW:
        return ACWRResult(
            ratio=ratio,
            zone="optimal",
            message="Belastung im guten Bereich — leicht unter Gewohnheit",
        )
    return ACWRResult(
        ratio=ratio,
        zone="optimal",
        message="Belastung im optimalen Bereich",
    )


# ---------------------------------------------------------------------------
# Trend-Berechnung
# ---------------------------------------------------------------------------


def calculate_trend(
    ctl_history: list[tuple[date, float]],
    lookback_days: int = TREND_LOOKBACK_DAYS,
) -> str:
    """Bestimme Trend anhand CTL-Verlauf.

    Vergleicht aktuellen CTL mit dem Wert vor lookback_days Tagen.
    """
    if len(ctl_history) < 2:
        return "stable"

    current_ctl = ctl_history[-1][1]
    target_date = ctl_history[-1][0] - timedelta(days=lookback_days)

    # Finde den nächsten Eintrag zum Zieldatum
    past_ctl = ctl_history[0][1]
    for d, val in ctl_history:
        if d <= target_date:
            past_ctl = val
        else:
            break

    if past_ctl <= 0:
        return "rising" if current_ctl > 0 else "stable"

    pct_change = ((current_ctl - past_ctl) / past_ctl) * 100.0

    if pct_change > TREND_THRESHOLD_PERCENT:
        return "rising"
    if pct_change < -TREND_THRESHOLD_PERCENT:
        return "falling"
    return "stable"


TREND_LABELS: dict[str, str] = {
    "rising": "↑ steigend",
    "stable": "→ stabil",
    "falling": "↓ fallend",
}


# ---------------------------------------------------------------------------
# Kontext-Satz
# ---------------------------------------------------------------------------


_SCORE_MESSAGES: list[tuple[int, str]] = [
    (70, "Gutes Fitnesslevel — halte die Konsistenz aufrecht"),
    (40, "Solide Basis — regelmäßiges Training zeigt Wirkung"),
    (1, "Deine Fitness baut sich auf — bleib dran!"),
]


def _score_based_message(score: int) -> str:
    for threshold, msg in _SCORE_MESSAGES:
        if score >= threshold:
            return msg
    return "Lade dein erstes Training hoch um deinen Fitness-Score zu berechnen"


def generate_context_message(
    score: int,
    trend: str,
    form: FormIndicator,
    acwr: ACWRResult | None,
) -> str:
    """Generiere einen einordnenden Satz für das Dashboard."""
    # Priorität: ACWR-Warnung > Form-Ermüdung > Trend > Form-Frisch > Score
    if acwr and acwr.zone == "danger":
        return acwr.message
    if form.status == "fatigued":
        return "Du bist aktuell ermüdet — ein Ruhetag oder lockerer Lauf hilft bei der Regeneration"
    if trend == "rising":
        return "Deine Fitness entwickelt sich positiv — weiter so!"
    if trend == "falling":
        return "Deine Fitness ist leicht rückläufig — prüfe ob du genug trainierst"
    if form.status == "fresh":
        return "Du bist gut erholt — ein guter Zeitpunkt für eine intensive Einheit"
    return _score_based_message(score)


# ---------------------------------------------------------------------------
# Aggregierte Berechnung
# ---------------------------------------------------------------------------


def aggregate_daily_trimps(
    sessions: list[WorkoutModel],
) -> dict[date, float]:
    """Aggregiere TRIMP-Werte pro Tag."""
    daily: dict[date, float] = defaultdict(float)
    for s in sessions:
        if s.trimp_score is not None and s.trimp_score > 0:
            session_date = s.date.date() if hasattr(s.date, "date") else s.date
            daily[session_date] += s.trimp_score
    return dict(daily)


def sessions_with_types(
    sessions: list[WorkoutModel],
) -> list[tuple[date, float, str]]:
    """Extrahiere (date, trimp, workout_type) aus Sessions."""
    result: list[tuple[date, float, str]] = []
    for s in sessions:
        if s.trimp_score is not None and s.trimp_score > 0:
            session_date = s.date.date() if hasattr(s.date, "date") else s.date
            result.append((session_date, s.trimp_score, s.workout_type or "running"))
    return result


def compute_full_score(
    sessions: list[WorkoutModel],
    up_to_date: date | None = None,
) -> dict:
    """Berechne den kompletten Fitness-Score mit allen Indikatoren.

    Returns ein Dict das direkt in FitnessScoreResponse gemappt werden kann.
    """
    target = up_to_date or date.today()

    # 1. Tägliche TRIMPs
    daily_trimps = aggregate_daily_trimps(sessions)

    # 2. CTL/ATL/TSB
    metrics = calculate_fitness_metrics(daily_trimps, target)

    # 3. Score normalisieren (absolute Referenzskala)
    score = normalize_score(metrics.ctl)

    # 4. Aufschlüsselung
    typed = sessions_with_types(sessions)
    endurance_score, strength_score = calculate_split_scores(typed, target)

    # 5. Form
    form = calculate_form(metrics.tsb)

    # 6. ACWR
    acwr = calculate_acwr(metrics.atl, metrics.ctl)

    # 7. Trend
    trend = calculate_trend(metrics.ctl_history)
    trend_label = TREND_LABELS.get(trend, "→ stabil")

    # 8. Kontext-Satz
    context = generate_context_message(score, trend, form, acwr)

    return {
        "score": score,
        "endurance_score": endurance_score,
        "strength_score": strength_score,
        "trend": trend,
        "trend_label": trend_label,
        "form": {
            "status": form.status,
            "label": form.label,
            "color": form.color,
            "recommendation": form.recommendation,
        },
        "acwr": (
            {
                "ratio": acwr.ratio,
                "zone": acwr.zone,
                "message": acwr.message,
            }
            if acwr
            else None
        ),
        "context_message": context,
        "metrics": metrics,
    }


def compute_history(
    sessions: list[WorkoutModel],
    days: int = 90,
) -> dict:
    """Berechne Fitness-Verlauf für Charts.

    Returns dict mit ctl_history, atl_history, tsb_history, score_history.
    """
    target = date.today()
    daily_trimps = aggregate_daily_trimps(sessions)
    metrics = calculate_fitness_metrics(daily_trimps, target)

    cutoff = target - timedelta(days=days)

    def _filter_and_format(
        history: list[tuple[date, float]],
    ) -> list[dict[str, str | float]]:
        return [{"date": d.isoformat(), "value": v} for d, v in history if d >= cutoff]

    # Score-History: CTL → absolute Skala via normalize_score
    score_history = [
        {
            "date": d.isoformat(),
            "value": float(normalize_score(v)),
        }
        for d, v in metrics.ctl_history
        if d >= cutoff
    ]

    return {
        "ctl_history": _filter_and_format(metrics.ctl_history),
        "atl_history": _filter_and_format(metrics.atl_history),
        "tsb_history": _filter_and_format(metrics.tsb_history),
        "score_history": score_history,
    }
