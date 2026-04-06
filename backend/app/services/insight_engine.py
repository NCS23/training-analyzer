"""Insight-Engine — Regelbasierte, trainingswissenschaftlich fundierte Insights.

Generiert priorisierte Hinweise für Dashboard und Fortschritt-Seite.
Regeln basieren auf:
- ACWR-Verletzungsprävention (Gabbett 2016)
- Polarisiertes Training 80/20 (Seiler 2010)
- Monotonie/Strain (Foster 1998)
- Allgemeine Trainingswissenschaft
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from app.services.fitness_score import ACWRResult, FormIndicator
from app.services.training_quality import IntensityDistribution, MonotonyResult

if TYPE_CHECKING:
    from app.infrastructure.database.models import WorkoutModel


@dataclass
class Insight:
    """Ein einzelner Insight/Hinweis."""

    type: str  # "warning" | "trend" | "achievement" | "recommendation" | "info"
    priority: int  # 1-10 (1 = höchste)
    title: str
    message: str
    category: str  # "load" | "balance" | "performance" | "plan" | "recovery"
    icon: str  # Lucide icon name


@dataclass
class InsightContext:
    """Alle Daten die die Insight-Engine für die Regelauswertung braucht."""

    acwr: ACWRResult | None
    form: FormIndicator
    trend: str
    intensity: IntensityDistribution
    monotony: MonotonyResult
    sessions: Sequence[WorkoutModel]
    form_days_fatigued: int = 0
    plan_adherence_pct: float | None = None


_TYPE_ORDER = {
    "warning": 0,
    "recommendation": 1,
    "trend": 2,
    "info": 3,
    "achievement": 4,
}


def generate_insights(
    ctx: InsightContext,
    max_insights: int = 5,
) -> list[Insight]:
    """Evaluiere alle Regeln und gib priorisierte Insights zurück."""
    insights: list[Insight] = []

    # --- Warnungen (Priorität 1-3) ---
    _check_acwr_danger(ctx.acwr, insights)
    _check_monotony_high(ctx.monotony, insights)
    _check_too_much_intensity(ctx.intensity, insights)
    _check_fatigue_prolonged(ctx.form, ctx.form_days_fatigued, insights)

    # --- Trends (Priorität 4-6) ---
    _check_fitness_rising(ctx.trend, insights)
    _check_fitness_falling(ctx.trend, insights)
    _check_pace_improvement(ctx.sessions, insights)
    _check_strength_regularity(ctx.sessions, insights)

    # --- Plan-bezogen (Priorität 4-6) ---
    _check_plan_adherence_low(ctx.plan_adherence_pct, insights)

    # --- Achievements (Priorität 7-8) ---
    _check_good_polarization(ctx.intensity, insights)

    # Sortieren nach Priorität, dann nach Typ (Warnungen zuerst)
    insights.sort(key=lambda i: (i.priority, _TYPE_ORDER.get(i.type, 5)))

    return insights[:max_insights]


# ---------------------------------------------------------------------------
# Regel-Implementierungen
# ---------------------------------------------------------------------------


def _check_acwr_danger(acwr: ACWRResult | None, out: list[Insight]) -> None:
    """Regel 1: ACWR > 1.5 → Verletzungsrisiko."""
    if acwr and acwr.zone == "danger":
        out.append(
            Insight(
                type="warning",
                priority=1,
                title="Verletzungsrisiko erhöht",
                message=(
                    f"Deine Belastung der letzten 7 Tage liegt {acwr.ratio:.1f}x "
                    "über deinem Gewohnheitsniveau. Reduziere die Intensität "
                    "oder nimm einen Ruhetag."
                ),
                category="recovery",
                icon="alert-triangle",
            )
        )


def _check_monotony_high(monotony: MonotonyResult, out: list[Insight]) -> None:
    """Regel 2: Monotonie > 2.0 → Übertrainingsrisiko."""
    if monotony.level == "high":
        out.append(
            Insight(
                type="warning",
                priority=2,
                title="Training zu gleichförmig",
                message=(
                    "Du trainierst seit einer Woche sehr gleichförmig. "
                    "Mehr Variation (lockere Tage, verschiedene Intensitäten) "
                    "reduziert das Übertrainingsrisiko."
                ),
                category="load",
                icon="alert-circle",
            )
        )


def _check_too_much_intensity(dist: IntensityDistribution, out: list[Insight]) -> None:
    """Regel 3: >30% intensiv → zu viel harte Einheiten."""
    if dist.total_minutes < 60:  # Zu wenig Daten
        return
    if dist.high_percent > 30:
        out.append(
            Insight(
                type="warning",
                priority=2,
                title="Zu viel harte Einheiten",
                message=(
                    f"{dist.high_percent:.0f}% deiner Trainingszeit war intensiv. "
                    "Empfohlen sind 15-25%. Mehr lockere Läufe verbessern "
                    "deine Grundlagenausdauer."
                ),
                category="balance",
                icon="flame",
            )
        )


def _check_fatigue_prolonged(form: FormIndicator, days: int, out: list[Insight]) -> None:
    """Regel 4: Ermüdet seit > 3 Tagen."""
    if form.status == "fatigued" and days > 3:
        out.append(
            Insight(
                type="warning",
                priority=2,
                title="Erholung nötig",
                message=(
                    f"Du bist seit {days} Tagen im ermüdeten Zustand. "
                    "Ein Ruhetag oder lockerer Lauf hilft bei der Regeneration."
                ),
                category="recovery",
                icon="battery-low",
            )
        )


def _check_fitness_rising(trend: str, out: list[Insight]) -> None:
    """Regel 5: Fitness steigt."""
    if trend == "rising":
        out.append(
            Insight(
                type="trend",
                priority=5,
                title="Fitness im Aufwärtstrend",
                message="Deine Fitness entwickelt sich positiv — weiter so!",
                category="performance",
                icon="trending-up",
            )
        )


def _check_fitness_falling(trend: str, out: list[Insight]) -> None:
    """Regel 6: Fitness sinkt."""
    if trend == "falling":
        out.append(
            Insight(
                type="trend",
                priority=4,
                title="Fitness-Rückgang",
                message=(
                    "Deine Fitness ist leicht rückläufig. Prüfe ob du "
                    "genug trainierst oder ob eine Trainingspause zu lang war."
                ),
                category="performance",
                icon="trending-down",
            )
        )


def _check_pace_improvement(sessions: Sequence[WorkoutModel], out: list[Insight]) -> None:
    """Regel 7: Pace hat sich verbessert (letzte 4 Wochen vs. vorher)."""
    today = date.today()
    recent_paces: list[float] = []
    older_paces: list[float] = []

    for s in sessions:
        if s.workout_type != "running" or not s.pace:
            continue
        d = s.date.date() if hasattr(s.date, "date") else s.date
        days_ago = (today - d).days
        pace_sec = _parse_pace_to_seconds(s.pace)
        if pace_sec is None or pace_sec <= 0:
            continue
        if days_ago < 28:
            recent_paces.append(pace_sec)
        elif days_ago < 56:
            older_paces.append(pace_sec)

    if len(recent_paces) >= 3 and len(older_paces) >= 3:
        recent_avg = sum(recent_paces) / len(recent_paces)
        older_avg = sum(older_paces) / len(older_paces)
        diff = older_avg - recent_avg  # Positiv = schneller geworden
        if diff > 5:  # Mehr als 5s/km schneller
            out.append(
                Insight(
                    type="achievement",
                    priority=6,
                    title="Pace verbessert",
                    message=(
                        f"Dein Durchschnittspace hat sich um {diff:.0f}s/km "
                        "verbessert im Vergleich zum Vormonat."
                    ),
                    category="performance",
                    icon="zap",
                )
            )


def _check_strength_regularity(sessions: Sequence[WorkoutModel], out: list[Insight]) -> None:
    """Regel 8: Keine Kraft-Session seit > 7 Tagen."""
    today = date.today()
    last_strength: date | None = None
    has_regular_strength = False

    for s in sessions:
        if s.workout_type != "strength":
            continue
        d = s.date.date() if hasattr(s.date, "date") else s.date
        if last_strength is None or d > last_strength:
            last_strength = d
        if (today - d).days < 28:
            has_regular_strength = True

    if has_regular_strength and last_strength:
        days_since = (today - last_strength).days
        if days_since > 7:
            out.append(
                Insight(
                    type="recommendation",
                    priority=6,
                    title="Kraft-Training nicht vergessen",
                    message=(
                        f"Deine letzte Kraft-Session war vor {days_since} Tagen. "
                        "Regelmäßiges Krafttraining unterstützt die Verletzungsprävention."
                    ),
                    category="balance",
                    icon="dumbbell",
                )
            )


def _check_plan_adherence_low(adherence: float | None, out: list[Insight]) -> None:
    """Regel 9: Plan-Treue < 60%."""
    if adherence is not None and adherence < 60:
        out.append(
            Insight(
                type="recommendation",
                priority=4,
                title="Plan-Abweichung",
                message=(
                    f"Du hast in den letzten 2 Wochen nur {adherence:.0f}% deiner "
                    "geplanten Sessions absolviert. Passe den Plan an oder "
                    "erhöhe die Konsistenz."
                ),
                category="plan",
                icon="calendar-x",
            )
        )


def _check_good_polarization(dist: IntensityDistribution, out: list[Insight]) -> None:
    """Regel 11: Gute 80/20-Verteilung."""
    if dist.total_minutes < 60:
        return
    if dist.is_polarized:
        out.append(
            Insight(
                type="achievement",
                priority=7,
                title="Gute Trainingsbalance",
                message=(
                    f"{dist.low_percent:.0f}% deiner Läufe waren locker — "
                    "das ist eine optimale Verteilung für Ausdauerentwicklung."
                ),
                category="balance",
                icon="check-circle",
            )
        )


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _parse_pace_to_seconds(pace_str: str | None) -> float | None:
    """Parse Pace-String "M:SS" zu Sekunden pro km."""
    if not pace_str:
        return None
    try:
        parts = pace_str.replace(",", ".").split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
    except (ValueError, IndexError):
        pass
    return None
