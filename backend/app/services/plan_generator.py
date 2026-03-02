"""Generate weekly plans from a training plan's phases.

Uses phase type, target metrics, and optional goal pace to create
fully populated WeeklyPlanEntry data with RunDetails.
"""

import json
import math
from datetime import date, timedelta
from typing import Optional

from app.infrastructure.database.models import RaceGoalModel, TrainingPhaseModel, TrainingPlanModel
from app.models.training_plan import PhaseWeeklyTemplate, PhaseWeeklyTemplates
from app.models.weekly_plan import RunDetails, WeeklyPlanEntry

# --- Phase Defaults ---

# Default session distribution per phase type.
# run_types: list of run types to distribute across available days.
# strength: default number of strength sessions per week.
# long_run_volume_pct: percentage of weekly volume for the long run.
PHASE_DEFAULTS: dict[str, dict] = {  # type: ignore[type-arg]
    "base": {
        "run_types": ["easy", "easy", "easy", "long_run"],
        "strength": 2,
        "long_run_volume_pct": 0.30,
    },
    "build": {
        "run_types": ["easy", "progression", "easy", "long_run"],
        "strength": 1,
        "long_run_volume_pct": 0.28,
    },
    "peak": {
        "run_types": ["easy", "intervals", "tempo", "long_run"],
        "strength": 1,
        "long_run_volume_pct": 0.25,
    },
    "taper": {
        "run_types": ["easy", "fartlek", "easy"],
        "strength": 0,
        "long_run_volume_pct": 0.0,
    },
    "transition": {
        "run_types": ["easy", "easy"],
        "strength": 1,
        "long_run_volume_pct": 0.0,
    },
}

# Pace multipliers relative to race pace (Daniels-based).
# (min_multiplier, max_multiplier) — lower multiplier = faster pace.
PACE_MULTIPLIERS: dict[str, tuple[float, float]] = {
    "easy": (1.15, 1.22),
    "recovery": (1.22, 1.30),
    "tempo": (1.02, 1.07),
    "intervals": (0.90, 0.96),
    "long_run": (1.08, 1.15),
    "progression": (1.10, 1.22),
    "repetitions": (0.85, 0.92),
    "fartlek": (1.05, 1.18),
    "race": (1.00, 1.00),
}

# Volume share per run type (as fraction of remaining volume after long run).
QUALITY_VOLUME_PCT = 0.22  # Each quality session gets ~22% of non-long-run volume


# --- Helpers ---


def _seconds_to_pace(sec_per_km: float) -> str:
    """Convert seconds/km to 'M:SS' pace string."""
    minutes = int(sec_per_km // 60)
    seconds = int(sec_per_km % 60)
    return f"{minutes}:{seconds:02d}"


def _round_to_5(value: float) -> int:
    """Round to nearest 5 minutes."""
    return max(5, int(round(value / 5.0) * 5))


def _get_phase_for_week(
    phases: list[TrainingPhaseModel],
    week_number: int,
) -> Optional[TrainingPhaseModel]:
    """Find the phase covering a given week number."""
    for phase in phases:
        if int(phase.start_week) <= week_number <= int(phase.end_week):  # type: ignore[arg-type]
            return phase
    return None


def _parse_target_metrics(phase: TrainingPhaseModel) -> dict:  # type: ignore[type-arg]
    """Parse phase target_metrics_json into a dict."""
    if not phase.target_metrics_json:
        return {}
    try:
        return json.loads(str(phase.target_metrics_json))  # type: ignore[no-any-return]
    except (json.JSONDecodeError, ValueError):
        return {}


def _parse_weekly_template(phase: TrainingPhaseModel) -> Optional[PhaseWeeklyTemplate]:
    """Parse phase weekly_template_json into a PhaseWeeklyTemplate."""
    if not phase.weekly_template_json:
        return None
    try:
        raw = json.loads(str(phase.weekly_template_json))
        return PhaseWeeklyTemplate(**raw)
    except (json.JSONDecodeError, ValueError, Exception):
        return None


def _parse_weekly_templates(
    phase: TrainingPhaseModel,
) -> Optional[PhaseWeeklyTemplates]:
    """Parse phase weekly_templates_json into PhaseWeeklyTemplates."""
    if not phase.weekly_templates_json:
        return None
    try:
        raw = json.loads(str(phase.weekly_templates_json))
        result = PhaseWeeklyTemplates(**raw)
        return result if result.weeks else None
    except (json.JSONDecodeError, ValueError, Exception):
        return None


def _template_to_entries(template: PhaseWeeklyTemplate) -> list[WeeklyPlanEntry]:
    """Convert a PhaseWeeklyTemplate into 7 WeeklyPlanEntry objects."""
    entries: list[WeeklyPlanEntry] = []
    for day_entry in template.days:
        run_details: Optional[RunDetails] = None
        if day_entry.training_type == "running" and day_entry.run_type:
            run_details = RunDetails(
                run_type=day_entry.run_type,
                target_duration_minutes=None,
                target_pace_min=None,
                target_pace_max=None,
                target_hr_min=None,
                target_hr_max=None,
                intervals=None,
            )
        entries.append(
            WeeklyPlanEntry(
                day_of_week=day_entry.day_of_week,
                training_type=day_entry.training_type,
                template_id=day_entry.template_id,
                is_rest_day=day_entry.is_rest_day,
                notes=day_entry.notes,
                run_details=run_details,
            )
        )
    return entries


def _compute_race_pace(goal: Optional[RaceGoalModel]) -> Optional[float]:
    """Compute race pace in seconds/km from goal."""
    if not goal:
        return None
    time_sec = goal.target_time_seconds
    dist_km = goal.distance_km
    if not time_sec or not dist_km or dist_km <= 0:
        return None
    return float(time_sec) / float(dist_km)


def _build_run_details(
    run_type: str,
    distance_km: float,
    race_pace: Optional[float],
) -> RunDetails:
    """Build RunDetails for a single running session."""
    multipliers = PACE_MULTIPLIERS.get(run_type, PACE_MULTIPLIERS["easy"])
    pace_min: Optional[str] = None
    pace_max: Optional[str] = None
    duration_minutes: Optional[int] = None

    if race_pace:
        pace_slow = race_pace * multipliers[1]  # slower end
        pace_fast = race_pace * multipliers[0]  # faster end
        pace_min = _seconds_to_pace(pace_fast)
        pace_max = _seconds_to_pace(pace_slow)
        avg_pace = (pace_slow + pace_fast) / 2.0
        duration_minutes = _round_to_5(distance_km * avg_pace / 60.0)
    elif distance_km > 0:
        # No goal: estimate ~6:30/km average
        duration_minutes = _round_to_5(distance_km * 390.0 / 60.0)

    return RunDetails(
        run_type=run_type,
        target_duration_minutes=duration_minutes,
        target_pace_min=pace_min,
        target_pace_max=pace_max,
        target_hr_min=None,
        target_hr_max=None,
        intervals=None,
    )


def _distribute_days(
    run_types: list[str],
    strength_count: int,
    rest_days: list[int],
) -> list[WeeklyPlanEntry]:
    """Distribute sessions across 7 days (0=Mon..6=Sun).

    Strategy:
    1. Mark rest days
    2. Place long_run on Saturday (5) or nearest free weekend day
    3. Place quality sessions with easy day buffer between them
    4. Place strength on remaining days (prefer non-quality-adjacent)
    5. Fill remaining with easy runs
    """
    entries: list[Optional[WeeklyPlanEntry]] = [None] * 7

    # 1. Mark rest days
    for day in rest_days:
        if 0 <= day <= 6:
            entries[day] = WeeklyPlanEntry(
                day_of_week=day,
                training_type=None,
                is_rest_day=True,
                notes=None,
                run_details=None,
            )

    available = [d for d in range(7) if entries[d] is None]

    # Separate run types
    long_run_types = [r for r in run_types if r == "long_run"]
    _quality_set = {"tempo", "intervals", "repetitions", "progression", "fartlek"}
    quality_types = [r for r in run_types if r in _quality_set]
    easy_types = [r for r in run_types if r != "long_run" and r not in _quality_set]

    assigned_runs: list[tuple[int, str]] = []  # (day, run_type)

    # 2. Place long run on Saturday (5) or nearest available weekend day
    if long_run_types:
        long_day = None
        for candidate in [5, 4, 3]:  # Sat, Fri, Thu
            if candidate in available:
                long_day = candidate
                break
        if long_day is None and available:
            long_day = available[-1]
        if long_day is not None:
            assigned_runs.append((long_day, "long_run"))
            available.remove(long_day)

    # 3. Place quality sessions with buffer
    for qt in quality_types:
        best_day = None
        best_score = -1
        for day in available:
            # Score: distance from other quality/long sessions
            min_dist = 7
            for ad, _ in assigned_runs:
                dist = min(abs(day - ad), 7 - abs(day - ad))
                min_dist = min(min_dist, dist)
            if min_dist > best_score:
                best_score = min_dist
                best_day = day
        if best_day is not None:
            assigned_runs.append((best_day, qt))
            available.remove(best_day)

    # 4. Place strength sessions
    strength_days: list[int] = []
    for _ in range(strength_count):
        if not available:
            break
        # Prefer days adjacent to easy, not quality
        best_day = available[0]
        for day in available:
            # Prefer mid-week for strength
            if day in (1, 2, 3) and day in available:
                best_day = day
                break
        strength_days.append(best_day)
        available.remove(best_day)

    # 5. Fill remaining with easy runs
    easy_idx = 0
    easy_days: list[tuple[int, str]] = []
    for day in available:
        if easy_idx < len(easy_types):
            easy_days.append((day, easy_types[easy_idx]))
            easy_idx += 1
        else:
            easy_days.append((day, "easy"))

    # Build final entries
    for day, run_type in assigned_runs:
        entries[day] = WeeklyPlanEntry(
            day_of_week=day,
            training_type="running",
            is_rest_day=False,
            notes=None,
            run_details=RunDetails(
                run_type=run_type,
                target_duration_minutes=None,
                target_pace_min=None,
                target_pace_max=None,
                target_hr_min=None,
                target_hr_max=None,
                intervals=None,
            ),
        )

    for day in strength_days:
        entries[day] = WeeklyPlanEntry(
            day_of_week=day,
            training_type="strength",
            is_rest_day=False,
            notes=None,
            run_details=None,
        )

    for day, run_type in easy_days:
        entries[day] = WeeklyPlanEntry(
            day_of_week=day,
            training_type="running",
            is_rest_day=False,
            notes=None,
            run_details=RunDetails(
                run_type=run_type,
                target_duration_minutes=None,
                target_pace_min=None,
                target_pace_max=None,
                target_hr_min=None,
                target_hr_max=None,
                intervals=None,
            ),
        )

    # Fill any remaining None entries as rest
    for day in range(7):
        if entries[day] is None:
            entries[day] = WeeklyPlanEntry(
                day_of_week=day,
                training_type=None,
                is_rest_day=True,
                notes=None,
                run_details=None,
            )

    return [e for e in entries if e is not None]


# --- Main Generator ---


def generate_weekly_plans(
    plan: TrainingPlanModel,
    phases: list[TrainingPhaseModel],
    rest_days: list[int],
    goal: Optional[RaceGoalModel],
) -> list[tuple[date, list[WeeklyPlanEntry]]]:
    """Generate (week_start, entries) tuples for all weeks of the plan.

    Args:
        plan: The training plan with start_date and end_date.
        phases: List of phases sorted by start_week.
        rest_days: List of rest day indices (0=Mon, 6=Sun).
        goal: Optional goal for pace calculation.

    Returns:
        List of (week_start_date, list_of_7_entries) tuples.
    """
    plan_start = plan.start_date
    plan_end = plan.end_date
    if not plan_start or not plan_end:
        return []

    # Ensure start is a Monday
    start_date = date(plan_start.year, plan_start.month, plan_start.day)
    # Adjust to Monday if needed
    start_date = start_date - timedelta(days=start_date.weekday())

    end_date = date(plan_end.year, plan_end.month, plan_end.day)
    total_days = (end_date - start_date).days
    total_weeks = max(1, math.ceil(total_days / 7))

    race_pace = _compute_race_pace(goal)
    result: list[tuple[date, list[WeeklyPlanEntry]]] = []

    for week_idx in range(total_weeks):
        week_number = week_idx + 1
        week_start = start_date + timedelta(weeks=week_idx)

        phase = _get_phase_for_week(phases, week_number)
        if not phase:
            # No phase covers this week — generate rest week
            entries = [
                WeeklyPlanEntry(
                    day_of_week=d,
                    training_type=None,
                    is_rest_day=True,
                    notes=None,
                    run_details=None,
                )
                for d in range(7)
            ]
            result.append((week_start, entries))
            continue

        phase_type = str(phase.phase_type)
        defaults = PHASE_DEFAULTS.get(phase_type, PHASE_DEFAULTS["base"])
        metrics = _parse_target_metrics(phase)

        # Compute week position within phase (needed for per-week templates + volume)
        phase_start_week = int(phase.start_week)  # type: ignore[arg-type]
        phase_end_week = int(phase.end_week)  # type: ignore[arg-type]
        phase_duration = max(1, phase_end_week - phase_start_week + 1)
        week_in_phase = week_number - phase_start_week  # 0-indexed

        # 3-tier template resolution: per-week → shared → PHASE_DEFAULTS
        per_week_templates = _parse_weekly_templates(phase)
        week_key = str(week_in_phase + 1)  # 1-indexed key
        per_week_template: Optional[PhaseWeeklyTemplate] = None
        if per_week_templates and week_key in per_week_templates.weeks:
            per_week_template = per_week_templates.weeks[week_key]

        shared_template = _parse_weekly_template(phase)

        if per_week_template:
            entries = _template_to_entries(per_week_template)
        elif shared_template:
            entries = _template_to_entries(shared_template)
        else:
            # Fallback: use PHASE_DEFAULTS heuristic
            raw_quality = metrics.get("quality_sessions_per_week")
            quality_count: Optional[int] = int(raw_quality) if raw_quality is not None else None
            strength_count = metrics.get(
                "strength_sessions_per_week",
                defaults["strength"],
            )
            if strength_count is None:
                strength_count = defaults["strength"]

            default_run_types: list[str] = list(defaults["run_types"])
            _qual = {"tempo", "intervals", "repetitions", "progression", "fartlek"}
            default_quality = sum(1 for r in default_run_types if r in _qual)

            if quality_count is not None:
                if quality_count > default_quality:
                    for _ in range(quality_count - default_quality):
                        for i, rt in enumerate(default_run_types):
                            if rt == "easy":
                                default_run_types[i] = (
                                    "intervals" if phase_type == "peak" else "tempo"
                                )
                                break
                elif quality_count < default_quality:
                    removed = 0
                    for i, rt in enumerate(default_run_types):
                        if rt in _qual and removed < default_quality - quality_count:
                            default_run_types[i] = "easy"
                            removed += 1

            entries = _distribute_days(default_run_types, strength_count, rest_days)

        # Calculate volume for this week (linear progression within phase)
        vol_min = metrics.get("weekly_volume_min")
        vol_max = metrics.get("weekly_volume_max")

        if vol_min is not None and vol_max is not None:
            progress = week_in_phase / max(1, phase_duration - 1) if phase_duration > 1 else 0.5
            weekly_volume = vol_min + (vol_max - vol_min) * progress
        elif vol_min is not None:
            weekly_volume = vol_min
        elif vol_max is not None:
            weekly_volume = vol_max
        else:
            weekly_volume = None

        # Distribute volume across running sessions and set RunDetails
        if weekly_volume is not None and weekly_volume > 0:
            running_entries = [
                e for e in entries if e.training_type == "running" and e.run_details is not None
            ]
            if running_entries:
                # Determine long run volume pct from template or defaults
                has_long_run = any(
                    e.run_details and e.run_details.run_type == "long_run" for e in running_entries
                )
                if (per_week_template or shared_template) and has_long_run:
                    # Template path: use 0.30 default for long run share
                    long_run_pct: float = 0.30
                else:
                    long_run_pct = defaults["long_run_volume_pct"]
                long_run_km = weekly_volume * long_run_pct if long_run_pct > 0 else 0.0

                remaining_km = weekly_volume - long_run_km
                non_long = [
                    e
                    for e in running_entries
                    if e.run_details and e.run_details.run_type != "long_run"
                ]
                _qual_vol = {"tempo", "intervals", "repetitions", "progression", "fartlek"}
                quality_entries = [
                    e for e in non_long if e.run_details and e.run_details.run_type in _qual_vol
                ]
                easy_entries = [
                    e for e in non_long if e.run_details and e.run_details.run_type not in _qual_vol
                ]

                quality_km_each = remaining_km * QUALITY_VOLUME_PCT if quality_entries else 0.0
                quality_total_km = quality_km_each * len(quality_entries)
                easy_total_km = remaining_km - quality_total_km
                easy_km_each = easy_total_km / len(easy_entries) if easy_entries else 0.0

                for entry in running_entries:
                    if entry.run_details is None:
                        continue
                    rt = entry.run_details.run_type
                    if rt == "long_run":
                        dist = long_run_km
                    elif rt in _qual_vol:
                        dist = quality_km_each
                    else:
                        dist = easy_km_each

                    entry.run_details = _build_run_details(rt, dist, race_pace)

        result.append((week_start, entries))

    return result
