"""Race Goal API Endpoints — CRUD fuer Wettkampf-Ziele."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    RaceGoalModel,
    TrainingPlanModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.goal import (
    GoalProgressResponse,
    RaceGoalCreate,
    RaceGoalListResponse,
    RaceGoalResponse,
    RaceGoalUpdate,
    TrainingPlanSummaryForGoal,
)

router = APIRouter(prefix="/goals", tags=["goals"])


async def _get_plan_summary(
    db: AsyncSession,
    plan_id: Optional[int],
) -> Optional[TrainingPlanSummaryForGoal]:
    """Look up a training plan summary by ID."""
    if plan_id is None:
        return None
    plan_id_int = int(plan_id)
    result = await db.execute(
        select(TrainingPlanModel.id, TrainingPlanModel.name, TrainingPlanModel.status).where(
            TrainingPlanModel.id == plan_id_int
        )
    )
    row = result.one_or_none()
    if not row:
        return None
    return TrainingPlanSummaryForGoal(
        id=int(row.id),  # type: ignore[arg-type]
        name=str(row.name),
        status=str(row.status),
    )


async def _goal_to_response(
    db: AsyncSession,
    goal: RaceGoalModel,
) -> RaceGoalResponse:
    """Build RaceGoalResponse with optional plan summary."""
    tp_id = int(goal.training_plan_id) if goal.training_plan_id else None  # type: ignore[arg-type]
    plan_summary = await _get_plan_summary(db, tp_id)
    return RaceGoalResponse.from_db(goal, plan_summary=plan_summary)


@router.get("", response_model=RaceGoalListResponse)
async def list_goals(
    db: AsyncSession = Depends(get_db),
) -> RaceGoalListResponse:
    """Liste aller Wettkampf-Ziele (aktive zuerst, dann nach Datum)."""
    query = select(RaceGoalModel).order_by(
        RaceGoalModel.is_active.desc(),
        RaceGoalModel.race_date.asc(),
    )
    result = await db.execute(query)
    goals = result.scalars().all()
    return RaceGoalListResponse(
        goals=[await _goal_to_response(db, g) for g in goals],
    )


@router.post("", response_model=RaceGoalResponse, status_code=201)
async def create_goal(
    body: RaceGoalCreate,
    db: AsyncSession = Depends(get_db),
) -> RaceGoalResponse:
    """Erstellt ein neues Wettkampf-Ziel."""
    goal = RaceGoalModel(
        title=body.title,
        race_date=datetime.combine(body.race_date, datetime.min.time()),
        distance_km=body.distance_km,
        target_time_seconds=body.target_time_seconds,
        is_active=True,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return await _goal_to_response(db, goal)


@router.get("/{goal_id}", response_model=RaceGoalResponse)
async def get_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
) -> RaceGoalResponse:
    """Einzelnes Wettkampf-Ziel."""
    query = select(RaceGoalModel).where(RaceGoalModel.id == goal_id)
    result = await db.execute(query)
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Ziel nicht gefunden.")
    return await _goal_to_response(db, goal)


@router.patch("/{goal_id}", response_model=RaceGoalResponse)
async def update_goal(
    goal_id: int,
    body: RaceGoalUpdate,
    db: AsyncSession = Depends(get_db),
) -> RaceGoalResponse:
    """Aktualisiert ein Wettkampf-Ziel."""
    query = select(RaceGoalModel).where(RaceGoalModel.id == goal_id)
    result = await db.execute(query)
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Ziel nicht gefunden.")

    if body.title is not None:
        goal.title = body.title  # type: ignore[assignment]
    if body.race_date is not None:
        goal.race_date = datetime.combine(body.race_date, datetime.min.time())  # type: ignore[assignment]
    if body.distance_km is not None:
        goal.distance_km = body.distance_km  # type: ignore[assignment]
    if body.target_time_seconds is not None:
        goal.target_time_seconds = body.target_time_seconds  # type: ignore[assignment]
    if body.is_active is not None:
        goal.is_active = body.is_active  # type: ignore[assignment]

    await db.commit()
    await db.refresh(goal)
    return await _goal_to_response(db, goal)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Loescht ein Wettkampf-Ziel."""
    query = select(RaceGoalModel).where(RaceGoalModel.id == goal_id)
    result = await db.execute(query)
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Ziel nicht gefunden.")
    await db.delete(goal)
    await db.commit()


def _parse_pace_to_seconds(pace_str: str) -> float:
    """Parse pace string like '5:41' to total seconds (341)."""
    parts = pace_str.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0.0


def _format_pace_seconds(total_sec: float) -> str:
    """Format seconds-per-km to pace string M:SS."""
    minutes = int(total_sec // 60)
    seconds = int(total_sec % 60)
    return f"{minutes}:{seconds:02d}"


def _format_time_seconds(total_sec: int) -> str:
    """Format total seconds to H:MM:SS or M:SS."""
    hours = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


@router.get("/{goal_id}/progress", response_model=GoalProgressResponse)
async def get_goal_progress(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
) -> GoalProgressResponse:
    """Berechnet den Fortschritt in Richtung eines Wettkampf-Ziels.

    Nutzt die letzten 4 Wochen an Lauf-Sessions (Tempo, Intervals, Long Run)
    um den aktuellen Pace-Stand zu ermitteln.
    """
    query = select(RaceGoalModel).where(RaceGoalModel.id == goal_id)
    result = await db.execute(query)
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Ziel nicht gefunden.")

    goal_response = await _goal_to_response(db, goal)
    distance = float(goal.distance_km)  # type: ignore[arg-type]
    target_secs = int(goal.target_time_seconds)  # type: ignore[arg-type]
    target_pace_sec = target_secs / distance if distance > 0 else 0

    # Fetch recent running sessions (last 8 weeks for trend) with pace data
    eight_weeks_ago = datetime.utcnow() - timedelta(weeks=8)
    effective_type = func.coalesce(
        WorkoutModel.training_type_override,
        WorkoutModel.training_type_auto,
    )
    sessions_query = (
        select(
            WorkoutModel.pace,
            WorkoutModel.distance_km,
            WorkoutModel.duration_sec,
            WorkoutModel.date,
        )
        .where(
            WorkoutModel.workout_type == "running",
            WorkoutModel.date >= eight_weeks_ago,
            WorkoutModel.pace.isnot(None),
            WorkoutModel.pace != "",
            # Use tempo-relevant sessions: tempo, intervals, long_run, threshold
            effective_type.in_(["tempo", "intervals", "long_run", "threshold", "race"]),
        )
        .order_by(WorkoutModel.date.asc())
    )
    result = await db.execute(sessions_query)
    all_sessions = result.all()

    # Filter to last 4 weeks for current pace
    four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
    recent_sessions = [s for s in all_sessions if s.date >= four_weeks_ago]

    if not recent_sessions:
        return GoalProgressResponse(
            goal=goal_response,
            target_pace_sec_per_km=target_pace_sec,
            target_pace_formatted=_format_pace_seconds(target_pace_sec),
            sessions_used=0,
        )

    # Calculate weighted average pace (weighted by distance)
    total_weighted_pace = 0.0
    total_distance = 0.0
    for row in recent_sessions:
        pace_sec = _parse_pace_to_seconds(str(row.pace))
        dist = float(row.distance_km) if row.distance_km else 0.0
        if pace_sec > 0 and dist > 0:
            total_weighted_pace += pace_sec * dist
            total_distance += dist

    if total_distance == 0:
        return GoalProgressResponse(
            goal=goal_response,
            target_pace_sec_per_km=target_pace_sec,
            target_pace_formatted=_format_pace_seconds(target_pace_sec),
            sessions_used=0,
        )

    current_pace_sec = total_weighted_pace / total_distance
    pace_gap = current_pace_sec - target_pace_sec

    # Progress: 0% = way off, 100% = at or faster than target
    # Map the gap: if current is slower, progress < 100; if faster, progress > 100
    # Use a reasonable range: ±60 sec/km as the 0-100% range
    progress = max(0, min(100, 100 - (pace_gap / 60) * 100)) if target_pace_sec > 0 else 0

    # Estimated finish time at current pace
    est_finish_sec = int(current_pace_sec * distance)

    # Finish delta: estimated finish vs target time
    finish_delta = est_finish_sec - target_secs
    if finish_delta > 0:
        finish_delta_label = f"+{_format_time_seconds(abs(finish_delta))} langsamer"
    elif finish_delta < 0:
        finish_delta_label = f"-{_format_time_seconds(abs(finish_delta))} schneller"
    else:
        finish_delta_label = "Genau im Ziel"

    # Pace gap label
    if pace_gap > 0:
        gap_label = f"+{abs(pace_gap):.0f} sec/km langsamer"
    elif pace_gap < 0:
        gap_label = f"{abs(pace_gap):.0f} sec/km schneller"
    else:
        gap_label = "Genau im Ziel"

    # Weekly trend: compare first half vs second half of sessions
    weekly_trend_sec = None
    weekly_trend_label = None
    weeks_to_goal = None
    goal_reachable = None

    if len(all_sessions) >= 4:
        # Group sessions by week and calculate average pace per week
        week_paces: dict[int, list[tuple[float, float]]] = {}
        now = datetime.utcnow()
        for row in all_sessions:
            pace_sec_val = _parse_pace_to_seconds(str(row.pace))
            dist_val = float(row.distance_km) if row.distance_km else 0.0
            if pace_sec_val > 0 and dist_val > 0:
                weeks_ago = int((now - row.date).days / 7)
                if weeks_ago not in week_paces:
                    week_paces[weeks_ago] = []
                week_paces[weeks_ago].append((pace_sec_val, dist_val))

        # Calculate weighted pace per week
        weekly_avg: list[tuple[int, float]] = []
        for week_num, entries in sorted(week_paces.items(), reverse=True):
            w_pace = sum(p * d for p, d in entries)
            w_dist = sum(d for _, d in entries)
            if w_dist > 0:
                weekly_avg.append((week_num, w_pace / w_dist))

        # Trend: improvement per week (negative = faster = improvement)
        if len(weekly_avg) >= 2:
            # Simple linear regression: pace vs week
            n = len(weekly_avg)
            sum_x = sum(w for w, _ in weekly_avg)
            sum_y = sum(p for _, p in weekly_avg)
            sum_xy = sum(w * p for w, p in weekly_avg)
            sum_x2 = sum(w * w for w, _ in weekly_avg)
            denom = n * sum_x2 - sum_x * sum_x
            if denom != 0:
                # slope = change in pace per week
                # positive slope = getting faster (higher week_num = older)
                slope = (n * sum_xy - sum_x * sum_y) / denom
                # slope is sec/km per week of age. Positive = older weeks faster
                # We want improvement per week: older weeks slower → slope > 0 → improving
                weekly_trend_sec = round(slope, 1)

                if weekly_trend_sec > 1:
                    weekly_trend_label = f"-{abs(weekly_trend_sec):.0f} sec/km pro Woche"
                elif weekly_trend_sec < -1:
                    weekly_trend_label = f"+{abs(weekly_trend_sec):.0f} sec/km pro Woche"
                else:
                    weekly_trend_label = "Stabil"

                # Weeks to goal: if improving (slope > 0)
                if weekly_trend_sec > 0 and pace_gap > 0:
                    weeks_needed = pace_gap / weekly_trend_sec
                    weeks_to_goal = int(round(weeks_needed))
                    goal_reachable = goal_response.days_until >= weeks_to_goal * 7
                elif pace_gap <= 0:
                    weeks_to_goal = 0
                    goal_reachable = True

    return GoalProgressResponse(
        goal=goal_response,
        current_pace_sec_per_km=round(current_pace_sec, 1),
        current_pace_formatted=_format_pace_seconds(current_pace_sec),
        target_pace_sec_per_km=round(target_pace_sec, 1),
        target_pace_formatted=_format_pace_seconds(target_pace_sec),
        pace_gap_sec=round(pace_gap, 1),
        pace_gap_formatted=_format_pace_seconds(abs(pace_gap)),
        pace_gap_label=gap_label,
        progress_percent=round(progress, 1),
        sessions_used=len(recent_sessions),
        estimated_finish_seconds=est_finish_sec,
        estimated_finish_formatted=_format_time_seconds(est_finish_sec),
        finish_delta_seconds=finish_delta,
        finish_delta_formatted=_format_time_seconds(abs(finish_delta)),
        finish_delta_label=finish_delta_label,
        weekly_pace_trend_sec=weekly_trend_sec,
        weekly_pace_trend_label=weekly_trend_label,
        weeks_to_goal=weeks_to_goal,
        goal_reachable=goal_reachable,
    )
