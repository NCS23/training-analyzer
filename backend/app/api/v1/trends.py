"""Trend Analysis API — Aggregated training data over time."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.trend import TrendInsight, TrendResponse, WeeklyDataPoint

router = APIRouter(prefix="/trends", tags=["trends"])


def _parse_pace_to_seconds(pace_str: str) -> float:
    """Parse pace string like '5:41' to total seconds."""
    parts = pace_str.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0.0


@router.get("", response_model=TrendResponse)
async def get_trends(
    days: int = Query(default=28, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
) -> TrendResponse:
    """Aggregierte Trainingsdaten fuer Trend-Analyse.

    Gruppiert Sessions nach Woche und berechnet:
    - Pace-Entwicklung (gewichteter Durchschnitt)
    - HR-Entwicklung
    - Volumen (Distanz + Dauer pro Woche)
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = (
        select(
            WorkoutModel.date,
            WorkoutModel.workout_type,
            WorkoutModel.pace,
            WorkoutModel.distance_km,
            WorkoutModel.duration_sec,
            WorkoutModel.hr_avg,
            func.coalesce(
                WorkoutModel.training_type_override,
                WorkoutModel.training_type_auto,
            ).label("effective_type"),
        )
        .where(
            WorkoutModel.date >= cutoff,
            WorkoutModel.workout_type == "running",
        )
        .order_by(WorkoutModel.date.asc())
    )
    result = await db.execute(query)
    sessions = result.all()

    # Group by ISO week
    weeks: dict[str, list] = {}
    for row in sessions:
        week_key = row.date.strftime("%G-W%V")
        if week_key not in weeks:
            weeks[week_key] = []
        weeks[week_key].append(row)

    weekly_data = []
    for week_key in sorted(weeks.keys()):
        rows = weeks[week_key]

        # Pace (weighted by distance, only running with pace)
        pace_weighted = 0.0
        pace_dist = 0.0
        total_distance = 0.0
        total_duration = 0
        hr_sum = 0
        hr_count = 0
        session_count = len(rows)

        for row in rows:
            dist = float(row.distance_km) if row.distance_km else 0.0
            dur = int(row.duration_sec) if row.duration_sec else 0
            total_distance += dist
            total_duration += dur

            if row.pace and dist > 0:
                pace_sec = _parse_pace_to_seconds(str(row.pace))
                if pace_sec > 0:
                    pace_weighted += pace_sec * dist
                    pace_dist += dist

            if row.hr_avg:
                hr_sum += int(row.hr_avg)
                hr_count += 1

        avg_pace: Optional[float] = round(pace_weighted / pace_dist, 1) if pace_dist > 0 else None
        avg_hr: Optional[int] = round(hr_sum / hr_count) if hr_count > 0 else None

        # Format pace
        pace_formatted = None
        if avg_pace is not None:
            p_min = int(avg_pace // 60)
            p_sec = int(avg_pace % 60)
            pace_formatted = f"{p_min}:{p_sec:02d}"

        # Week start date (Monday)
        first_date = min(r.date for r in rows)
        week_start = first_date - timedelta(days=first_date.weekday())

        weekly_data.append(
            WeeklyDataPoint(
                week=week_key,
                week_start=week_start.strftime("%Y-%m-%d"),
                session_count=session_count,
                total_distance_km=round(total_distance, 1),
                total_duration_sec=total_duration,
                avg_pace_sec_per_km=avg_pace,
                avg_pace_formatted=pace_formatted,
                avg_hr_bpm=avg_hr,
            )
        )

    # Compute insights
    insights = _compute_insights(weekly_data)

    return TrendResponse(weeks=weekly_data, insights=insights)


def _compute_insights(weekly_data: list[WeeklyDataPoint]) -> list[TrendInsight]:
    """Generate insights from weekly trend data."""
    insights: list[TrendInsight] = []

    if len(weekly_data) < 2:
        return insights

    # Pace trend
    paces = [w.avg_pace_sec_per_km for w in weekly_data if w.avg_pace_sec_per_km]
    if len(paces) >= 2:
        first_pace = paces[0]
        last_pace = paces[-1]
        diff = first_pace - last_pace  # positive = improved (faster)

        if diff > 3:
            insights.append(
                TrendInsight(
                    type="positive",
                    message=f"Pace um {abs(diff):.0f} sec/km verbessert ueber {len(paces)} Wochen.",
                )
            )
        elif diff < -3:
            insights.append(
                TrendInsight(
                    type="warning",
                    message=f"Pace um {abs(diff):.0f} sec/km langsamer geworden. Moeglicherweise Ermuedung?",
                )
            )

    # HR trend
    hrs = [w.avg_hr_bpm for w in weekly_data if w.avg_hr_bpm]
    if len(hrs) >= 2:
        first_hr = hrs[0]
        last_hr = hrs[-1]
        hr_diff = last_hr - first_hr

        if hr_diff > 5:
            insights.append(
                TrendInsight(
                    type="warning",
                    message=f"Durchschnittliche HF um {hr_diff} bpm gestiegen. Achte auf Erholung und Schlaf.",
                )
            )
        elif hr_diff < -5:
            insights.append(
                TrendInsight(
                    type="positive",
                    message=f"Durchschnittliche HF um {abs(hr_diff)} bpm gesunken — gutes Zeichen für Fitness.",
                )
            )

    # Volume trend
    volumes = [w.total_distance_km for w in weekly_data if w.total_distance_km > 0]
    if len(volumes) >= 2:
        first_half = sum(volumes[: len(volumes) // 2]) / (len(volumes) // 2)
        second_half = sum(volumes[len(volumes) // 2 :]) / (len(volumes) - len(volumes) // 2)

        if second_half > first_half * 1.2:
            insights.append(
                TrendInsight(
                    type="neutral",
                    message=f"Wochenvolumen um {((second_half / first_half) - 1) * 100:.0f}% gesteigert. Achte auf die 10%-Regel.",
                )
            )

    return insights
