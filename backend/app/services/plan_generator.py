"""Generate weekly plans from a training plan's phases.

Uses phase type, target metrics, and optional goal pace to create
fully populated WeeklyPlanEntry data with RunDetails.
"""

import json
import math
from datetime import date, timedelta
from typing import Any, Optional

from app.infrastructure.database.models import RaceGoalModel, TrainingPhaseModel, TrainingPlanModel
from app.models.exercise import TemplateExercise
from app.models.segment import Segment
from app.models.training_plan import PhaseWeeklyTemplate, PhaseWeeklyTemplates
from app.models.weekly_plan import PlannedSession, RunDetails, WeeklyPlanEntry

# --- Phase Defaults ---

# Default session distribution per phase type.
# run_types: list of run types to distribute across available days.
# strength: default number of strength sessions per week.
# long_run_volume_pct: percentage of weekly volume for the long run.
PHASE_DEFAULTS: dict[str, dict[str, Any]] = {
    "base": {
        # Grundlagenphase: aerobe Basis aufbauen, kein harter Tempobereich
        # 3 Easy + 1 Long Run; Steigerungsläufe/Lauf-ABC über Notes
        "run_types": ["easy", "easy", "easy", "long_run"],
        "strength": 2,
        "long_run_volume_pct": 0.30,
    },
    "build": {
        # Aufbauphase: erste Qualitätseinheiten, Progression + Fartlek
        "run_types": ["easy", "progression", "fartlek", "long_run"],
        "strength": 1,
        "long_run_volume_pct": 0.28,
    },
    "peak": {
        # Spitzenphase: spezifisches Training, Intervalle + Tempo
        "run_types": ["easy", "intervals", "tempo", "long_run"],
        "strength": 1,
        "long_run_volume_pct": 0.25,
    },
    "taper": {
        # Tapering: Umfang runter, Intensität beibehalten
        "run_types": ["easy", "tempo", "easy"],
        "strength": 0,
        "long_run_volume_pct": 0.0,
    },
    "transition": {
        "run_types": ["easy", "easy"],
        "strength": 1,
        "long_run_volume_pct": 0.0,
    },
    "recovery": {
        # Erholungsphase: nur lockere Läufe, kein Krafttraining
        "run_types": ["easy", "easy", "easy"],
        "strength": 0,
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
        if phase.start_week <= week_number <= phase.end_week:
            return phase
    return None


def _parse_target_metrics(phase: TrainingPhaseModel) -> dict[str, Any]:
    """Parse phase target_metrics_json into a dict."""
    if not phase.target_metrics_json:
        return {}
    try:
        return json.loads(str(phase.target_metrics_json))
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


def _has_explicit_run_details(rd: RunDetails) -> bool:
    """Check whether RunDetails has user-provided values (not just a skeleton).

    Checks the primary segment for any target fields, or whether
    multiple segments exist (which implies an explicit structure).
    """
    if rd.segments and len(rd.segments) > 1:
        return True
    seg = rd.segments[0] if rd.segments else None
    if seg is None:
        return False
    return (
        seg.target_duration_minutes is not None
        or seg.target_pace_min is not None
        or seg.target_distance_km is not None
    )


def _template_to_entries(template: PhaseWeeklyTemplate) -> list[WeeklyPlanEntry]:
    """Convert a PhaseWeeklyTemplate into 7 WeeklyPlanEntry objects.

    Reads from day_entry.sessions (populated natively or via backwards-compat
    validator from legacy flat fields).
    """
    entries: list[WeeklyPlanEntry] = []
    for day_entry in template.days:
        sessions: list[PlannedSession] = []
        for ts in day_entry.sessions:
            run_details: Optional[RunDetails] = None
            if ts.run_details is not None:
                run_details = ts.run_details
            elif ts.training_type == "running" and ts.run_type:
                # Skeleton — validators will create a default segment
                run_details = RunDetails(run_type=ts.run_type)
            sessions.append(
                PlannedSession(
                    position=ts.position,
                    training_type=ts.training_type,
                    template_id=ts.template_id,
                    run_details=run_details,
                    notes=ts.notes,
                    exercises=ts.exercises,
                )
            )
        entries.append(
            WeeklyPlanEntry(
                day_of_week=day_entry.day_of_week,
                is_rest_day=day_entry.is_rest_day,
                notes=day_entry.notes,
                sessions=sessions,
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
    """Build RunDetails for a single running session.

    Populates data via a single 'steady' segment. The RunDetails validators
    will automatically compute top-level fields from this segment.
    """
    multipliers = PACE_MULTIPLIERS.get(run_type, PACE_MULTIPLIERS["easy"])
    pace_min: Optional[str] = None
    pace_max: Optional[str] = None
    duration_minutes: Optional[float] = None

    if race_pace:
        pace_slow = race_pace * multipliers[1]  # slower end
        pace_fast = race_pace * multipliers[0]  # faster end
        pace_min = _seconds_to_pace(pace_fast)
        pace_max = _seconds_to_pace(pace_slow)
        avg_pace = (pace_slow + pace_fast) / 2.0
        duration_minutes = float(_round_to_5(distance_km * avg_pace / 60.0))
    elif distance_km > 0:
        # No goal: estimate ~6:30/km average
        duration_minutes = float(_round_to_5(distance_km * 390.0 / 60.0))

    return RunDetails(
        run_type=run_type,
        segments=[
            Segment(
                position=0,
                segment_type="steady",
                target_duration_minutes=duration_minutes,
                target_pace_min=pace_min,
                target_pace_max=pace_max,
            )
        ],
    )


def _distribute_days(  # noqa: C901, PLR0912, PLR0915  # TODO: E16 Refactoring
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
                is_rest_day=True,
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
            sessions=[
                PlannedSession(
                    position=0,
                    training_type="running",
                    run_details=RunDetails(run_type=run_type),
                )
            ],
        )

    for day in strength_days:
        entries[day] = WeeklyPlanEntry(
            day_of_week=day,
            sessions=[
                PlannedSession(
                    position=0,
                    training_type="strength",
                )
            ],
        )

    # Abwechselnde Notes für Easy-Runs (Lauf-ABC, Steigerungsläufe etc.)
    _easy_notes = [
        "Inkl. 4×100m Steigerungsläufe am Ende",
        "Inkl. 10 Min. Lauf-ABC (Skippings, Anfersen, Kniehebelauf)",
        None,  # Reiner Easy Run ohne Zusatz
        "Inkl. 5×80m Steigerungsläufe + Koordination",
    ]
    for idx, (day, run_type) in enumerate(easy_days):
        note = _easy_notes[idx % len(_easy_notes)]
        entries[day] = WeeklyPlanEntry(
            day_of_week=day,
            sessions=[
                PlannedSession(
                    position=0,
                    training_type="running",
                    run_details=RunDetails(run_type=run_type),
                    notes=note,
                )
            ],
        )

    # Fill any remaining None entries as rest
    for day in range(7):
        if entries[day] is None:
            entries[day] = WeeklyPlanEntry(
                day_of_week=day,
                is_rest_day=True,
            )

    return [e for e in entries if e is not None]


# --- Session enrichment: Structured segments for quality sessions ---

# Interval progression: (repeats, distance_km, recovery_minutes)
_INTERVAL_PROGRESSION = [
    (4, 0.8, 2.0),  # 4×800m
    (5, 1.0, 1.5),  # 5×1000m
    (6, 1.0, 1.5),  # 6×1000m
    (4, 1.2, 2.0),  # 4×1200m
    (5, 1.2, 1.5),  # 5×1200m
    (3, 2.0, 2.5),  # 3×2000m
]

# Tempo progression: (tempo_minutes,)
_TEMPO_PROGRESSION = [15.0, 20.0, 25.0, 30.0, 35.0, 40.0]

# Easy run extras: None = plain easy run, list[tuple] = extra segments to append
_EASY_EXTRAS: list[list[tuple[str, float, int, float | None, str | None]] | None] = [
    # (segment_type, duration_min, repeats, target_distance_km, exercise_name)
    None,
    # Steigerungsläufe Set A
    [
        ("strides", 0.5, 4, 0.1, "Steigerungslauf 100m"),
        ("recovery_jog", 1.0, 3, None, None),
    ],
    # Lauf-ABC Set A: individuelle Übungen
    [
        ("drills", 2.0, 1, None, "Skippings"),
        ("drills", 2.0, 1, None, "Anfersen"),
        ("drills", 2.0, 1, None, "Kniehebelauf"),
        ("drills", 2.0, 1, None, "Hopserlauf"),
    ],
    None,
    # Steigerungsläufe Set B
    [
        ("strides", 0.5, 5, 0.08, "Steigerungslauf 80m"),
        ("recovery_jog", 1.0, 4, None, None),
    ],
    # Lauf-ABC Set B: andere Übungen
    [
        ("drills", 2.0, 1, None, "Seitgalopp"),
        ("drills", 2.0, 1, None, "Überkreuzlauf"),
        ("drills", 2.0, 1, None, "Kniehebelauf"),
        ("drills", 2.0, 1, None, "Koordinationsleiter"),
    ],
]

# Fartlek progressions: (fast_dur_min, slow_dur_min, repeats)
_FARTLEK_PROGRESSION = [
    (1.0, 2.0, 5),  # 5× (1' schnell / 2' locker)
    (1.5, 1.5, 6),  # 6× (1.5' schnell / 1.5' locker)
    (2.0, 1.5, 5),  # 5× (2' schnell / 1.5' locker)
    (2.0, 1.0, 6),  # 6× (2' schnell / 1' locker)
    (3.0, 2.0, 4),  # 4× (3' schnell / 2' locker)
    (3.0, 1.5, 5),  # 5× (3' schnell / 1.5' locker)
]

# Kraft-Übungen pro Phase-Typ: list[TemplateExercise-Dicts]
# (name, category, sets, reps, exercise_type)
_STRENGTH_EXERCISES: dict[str, list[tuple[str, str, int, int, str]]] = {
    "recovery": [
        ("Plank", "core", 3, 30, "kraft"),
        ("Seitstütz", "core", 2, 20, "kraft"),
        ("Hüftbrücke", "legs", 3, 15, "kraft"),
        ("Ausfallschritt", "legs", 2, 10, "kraft"),
    ],
    "base": [
        ("Kniebeugen", "legs", 3, 12, "kraft"),
        ("Rumänisches Kreuzheben", "legs", 3, 10, "kraft"),
        ("Wadenheben", "legs", 3, 15, "kraft"),
        ("Plank", "core", 3, 45, "kraft"),
        ("Ausfallschritte", "legs", 3, 10, "kraft"),
        ("Seitstütz", "core", 3, 30, "kraft"),
    ],
    "build": [
        ("Kniebeugen", "legs", 4, 8, "kraft"),
        ("Kreuzheben", "legs", 3, 8, "kraft"),
        ("Step-Ups", "legs", 3, 10, "kraft"),
        ("Wadenheben einbeinig", "legs", 3, 12, "kraft"),
        ("Plank mit Arm heben", "core", 3, 30, "kraft"),
        ("Russian Twist", "core", 3, 15, "kraft"),
    ],
    "peak": [
        ("Sprungkniebeugen", "legs", 3, 8, "kraft"),
        ("Einbeinige Kniebeuge", "legs", 3, 6, "kraft"),
        ("Box Jumps", "legs", 3, 8, "kraft"),
        ("Plank", "core", 3, 45, "kraft"),
        ("Bergsteiger", "core", 3, 20, "kraft"),
    ],
    "taper": [
        ("Kniebeugen leicht", "legs", 2, 10, "kraft"),
        ("Plank", "core", 2, 30, "kraft"),
        ("Hüftbrücke", "legs", 2, 12, "kraft"),
    ],
}


def _enrich_sessions_for_week(
    entries: list[WeeklyPlanEntry],
    week_in_phase: int,
    _phase_duration: int,
    phase_type: str,
    weekly_volume: float | None,
    race_pace: float | None,
) -> None:
    """Ersetzt generische Template-Segmente durch wochenspezifische Strukturen.

    Schreibt progressive Intervall-/Tempo-Segmente und Easy-Run-Extras
    direkt in die RunDetails-Segmente (nicht nur Notes).
    """
    easy_idx = 0
    for entry in entries:
        for sess in entry.sessions:
            # Kraft-Sessions mit Übungen anreichern
            if sess.training_type == "strength":
                _enrich_strength_exercises(sess, phase_type)
                continue

            if sess.training_type != "running" or not sess.run_details:
                continue
            # Sessions mit bereits strukturierten Segmenten (>1) überspringen
            if sess.run_details.segments and len(sess.run_details.segments) > 1:
                continue
            rt = sess.run_details.run_type
            if rt == "easy":
                _enrich_easy_segments(sess, week_in_phase, easy_idx, race_pace)
                easy_idx += 1
            elif rt == "long_run":
                _enrich_long_run_segments(
                    sess,
                    week_in_phase,
                    phase_type,
                    weekly_volume,
                    race_pace,
                )
            elif rt == "intervals":
                _enrich_interval_segments(sess, week_in_phase, phase_type, race_pace)
            elif rt == "tempo":
                _enrich_tempo_segments(sess, week_in_phase, phase_type, race_pace)
            elif rt == "progression":
                _enrich_progression_segments(sess, week_in_phase, race_pace)
            elif rt == "fartlek":
                _enrich_fartlek_segments(sess, week_in_phase, race_pace)


def _enrich_strength_exercises(sess: PlannedSession, phase_type: str) -> None:
    """Fügt Standard-Kraftübungen hinzu, wenn keine Übungen definiert sind.

    Nur wenn die Session noch keine exercises hat — manuelle Übungen
    werden nicht überschrieben.
    """
    if sess.exercises and len(sess.exercises) > 0:
        return

    exercises_data = _STRENGTH_EXERCISES.get(phase_type, _STRENGTH_EXERCISES["base"])
    sess.exercises = [
        TemplateExercise(
            name=name,
            category=category,
            sets=sets,
            reps=reps,
            weight_kg=None,
            exercise_type=exercise_type,
            notes=None,
        )
        for name, category, sets, reps, exercise_type in exercises_data
    ]


def _enrich_easy_segments(
    sess: PlannedSession,
    week_in_phase: int,
    easy_idx: int,
    _race_pace: float | None,
) -> None:
    """Fügt Easy Runs rotierende Extras hinzu (Strides, Drills als Segmente).

    Jede Übung/Steigerung wird als eigenes Segment angelegt, damit die
    Laufuhr den Athleten Schritt für Schritt durchführen kann.
    """
    rotation_idx = (week_in_phase * 3 + easy_idx) % len(_EASY_EXTRAS)
    extras = _EASY_EXTRAS[rotation_idx]
    if not extras:
        return

    rd = sess.run_details
    if not rd or not rd.segments:
        return

    # Gesamtdauer der Extras berechnen
    extra_total = sum(dur * reps for _, dur, reps, _, _ in extras)
    main_seg = rd.segments[0]
    main_dur = main_seg.target_duration_minutes or 30.0
    main_seg.target_duration_minutes = max(15.0, main_dur - extra_total)

    # Jede Übung als eigenes Segment
    pos = 1
    note_parts = []
    for seg_type, dur, reps, dist_km, exercise in extras:
        rd.segments.append(
            Segment(
                position=pos,
                segment_type=seg_type,
                target_duration_minutes=dur,
                target_distance_km=dist_km,
                repeats=reps,
                exercise_name=exercise,
            )
        )
        pos += 1
        if exercise:
            if reps > 1 and dist_km:
                note_parts.append(f"{reps}×{int(dist_km * 1000)}m {exercise}")
            elif reps > 1:
                note_parts.append(f"{reps}× {exercise}")
            else:
                note_parts.append(exercise)

    sess.notes = ", ".join(note_parts) if note_parts else None


def _enrich_long_run_segments(
    sess: PlannedSession,
    week_in_phase: int,
    phase_type: str,
    weekly_volume: float | None,
    race_pace: float | None,
) -> None:
    """Macht Long Runs progressiv: Warmup + Steady + ggf. Race-Pace + Cooldown."""
    rd = sess.run_details
    if not rd or not rd.segments:
        return

    total_dur = rd.segments[0].target_duration_minutes or 60.0
    long_dist = round(weekly_volume * 0.30, 1) if weekly_volume else 12.0

    easy_mults = PACE_MULTIPLIERS["long_run"]
    easy_pace_min = _seconds_to_pace(race_pace * easy_mults[0]) if race_pace else None
    easy_pace_max = _seconds_to_pace(race_pace * easy_mults[1]) if race_pace else None

    warmup_dur = 10.0
    cooldown_dur = 5.0
    main_dur = max(20.0, total_dur - warmup_dur - cooldown_dur)

    if phase_type in ("build", "peak") and race_pace:
        # Race-Pace-Abschnitt am Ende (progressiv länger)
        rp_fraction = min(0.15 + week_in_phase * 0.05, 0.40)
        rp_dur = round(main_dur * rp_fraction / 5) * 5
        steady_dur = main_dur - rp_dur
        rp_pace_min = _seconds_to_pace(race_pace * 0.98)
        rp_pace_max = _seconds_to_pace(race_pace * 1.02)

        rd.segments = [
            Segment(
                position=0,
                segment_type="warmup",
                target_duration_minutes=warmup_dur,
                target_pace_min=easy_pace_min,
                target_pace_max=easy_pace_max,
            ),
            Segment(
                position=1,
                segment_type="steady",
                target_duration_minutes=steady_dur,
                target_distance_km=round(long_dist * (1 - rp_fraction), 1),
                target_pace_min=easy_pace_min,
                target_pace_max=easy_pace_max,
            ),
            Segment(
                position=2,
                segment_type="work",
                target_duration_minutes=rp_dur,
                target_pace_min=rp_pace_min,
                target_pace_max=rp_pace_max,
                notes="Race Pace",
            ),
            Segment(
                position=3,
                segment_type="cooldown",
                target_duration_minutes=cooldown_dur,
                target_pace_min=easy_pace_min,
                target_pace_max=easy_pace_max,
            ),
        ]
        sess.notes = f"~{long_dist:.0f} km, davon {rp_dur:.0f} Min. Race Pace"
    else:
        rd.segments = [
            Segment(
                position=0,
                segment_type="warmup",
                target_duration_minutes=warmup_dur,
                target_pace_min=easy_pace_min,
                target_pace_max=easy_pace_max,
            ),
            Segment(
                position=1,
                segment_type="steady",
                target_duration_minutes=main_dur,
                target_distance_km=long_dist,
                target_pace_min=easy_pace_min,
                target_pace_max=easy_pace_max,
            ),
            Segment(
                position=2,
                segment_type="cooldown",
                target_duration_minutes=cooldown_dur,
                target_pace_min=easy_pace_min,
                target_pace_max=easy_pace_max,
            ),
        ]
        sess.notes = f"~{long_dist:.0f} km, gleichmäßig locker"


def _enrich_interval_segments(
    sess: PlannedSession,
    week_in_phase: int,
    phase_type: str,
    race_pace: float | None,
) -> None:
    """Baut echte Intervall-Segmente: Warmup + N×(Work+Recovery) + Cooldown."""
    offset = 2 if phase_type == "peak" else 0
    idx = min(offset + week_in_phase, len(_INTERVAL_PROGRESSION) - 1)
    repeats, dist_km, recovery_min = _INTERVAL_PROGRESSION[idx]

    if not race_pace:
        return

    mults = PACE_MULTIPLIERS["intervals"]
    work_pace_min = _seconds_to_pace(race_pace * mults[0])
    work_pace_max = _seconds_to_pace(race_pace * mults[1])
    easy_mults = PACE_MULTIPLIERS["easy"]
    easy_pace_min = _seconds_to_pace(race_pace * easy_mults[0])
    easy_pace_max = _seconds_to_pace(race_pace * easy_mults[1])

    segments = [
        Segment(
            position=0,
            segment_type="warmup",
            target_duration_minutes=10.0,
            target_pace_min=easy_pace_min,
            target_pace_max=easy_pace_max,
        ),
        Segment(
            position=1,
            segment_type="work",
            target_distance_km=dist_km,
            repeats=repeats,
            target_pace_min=work_pace_min,
            target_pace_max=work_pace_max,
        ),
        Segment(
            position=2,
            segment_type="recovery_jog",
            target_duration_minutes=recovery_min,
            repeats=max(1, repeats - 1),
            target_pace_min=easy_pace_min,
            target_pace_max=easy_pace_max,
        ),
        Segment(
            position=3,
            segment_type="cooldown",
            target_duration_minutes=10.0,
            target_pace_min=easy_pace_min,
            target_pace_max=easy_pace_max,
        ),
    ]

    sess.run_details = RunDetails(run_type="intervals", segments=segments)
    sess.notes = f"{repeats}×{int(dist_km * 1000)}m, {recovery_min:.0f} Min. Trabpause"


def _enrich_tempo_segments(
    sess: PlannedSession,
    week_in_phase: int,
    phase_type: str,
    race_pace: float | None,
) -> None:
    """Baut echte Tempo-Segmente: Warmup + Tempo-Block + Cooldown."""
    offset = 2 if phase_type == "peak" else 0
    idx = min(offset + week_in_phase, len(_TEMPO_PROGRESSION) - 1)
    tempo_dur = _TEMPO_PROGRESSION[idx]

    if not race_pace:
        return

    mults = PACE_MULTIPLIERS["tempo"]
    tempo_pace_min = _seconds_to_pace(race_pace * mults[0])
    tempo_pace_max = _seconds_to_pace(race_pace * mults[1])
    easy_mults = PACE_MULTIPLIERS["easy"]
    easy_pace_min = _seconds_to_pace(race_pace * easy_mults[0])
    easy_pace_max = _seconds_to_pace(race_pace * easy_mults[1])

    segments = [
        Segment(
            position=0,
            segment_type="warmup",
            target_duration_minutes=10.0,
            target_pace_min=easy_pace_min,
            target_pace_max=easy_pace_max,
        ),
        Segment(
            position=1,
            segment_type="work",
            target_duration_minutes=tempo_dur,
            target_pace_min=tempo_pace_min,
            target_pace_max=tempo_pace_max,
            notes="Schwellentempo",
        ),
        Segment(
            position=2,
            segment_type="cooldown",
            target_duration_minutes=10.0,
            target_pace_min=easy_pace_min,
            target_pace_max=easy_pace_max,
        ),
    ]

    sess.run_details = RunDetails(run_type="tempo", segments=segments)
    sess.notes = f"{tempo_dur:.0f} Min. Tempodauerlauf"


def _enrich_progression_segments(
    sess: PlannedSession,
    week_in_phase: int,
    race_pace: float | None,
) -> None:
    """Baut Progression-Segmente: Warmup + 3 Tempostufen + Cooldown.

    Jede Stufe wird schneller — die Uhr zeigt klare Pace-Ziele pro Abschnitt.
    """
    rd = sess.run_details
    if not rd or not rd.segments or not race_pace:
        return

    total_dur = rd.segments[0].target_duration_minutes or 40.0
    warmup_dur = 10.0
    cooldown_dur = 5.0
    main_dur = max(15.0, total_dur - warmup_dur - cooldown_dur)

    # Drei Stufen: locker → moderat → schnell (je 1/3)
    step_dur = round(main_dur / 3 / 5) * 5 or 5.0
    easy_mults = PACE_MULTIPLIERS["easy"]
    prog_mults = PACE_MULTIPLIERS["progression"]

    # Stufenweise schneller: 100% easy → 90% → Progression-Tempo
    mid_factor_fast = easy_mults[0] * 0.95
    mid_factor_slow = easy_mults[1] * 0.95

    # Progression wird mit Wochen etwas aggressiver
    fast_factor = max(prog_mults[0] - week_in_phase * 0.01, 0.90)

    rd.segments = [
        Segment(
            position=0,
            segment_type="warmup",
            target_duration_minutes=warmup_dur,
            target_pace_min=_seconds_to_pace(race_pace * easy_mults[0]),
            target_pace_max=_seconds_to_pace(race_pace * easy_mults[1]),
        ),
        Segment(
            position=1,
            segment_type="steady",
            target_duration_minutes=step_dur,
            target_pace_min=_seconds_to_pace(race_pace * easy_mults[0]),
            target_pace_max=_seconds_to_pace(race_pace * easy_mults[1]),
            notes="Locker einlaufen",
        ),
        Segment(
            position=2,
            segment_type="steady",
            target_duration_minutes=step_dur,
            target_pace_min=_seconds_to_pace(race_pace * mid_factor_fast),
            target_pace_max=_seconds_to_pace(race_pace * mid_factor_slow),
            notes="Moderate Steigerung",
        ),
        Segment(
            position=3,
            segment_type="work",
            target_duration_minutes=step_dur,
            target_pace_min=_seconds_to_pace(race_pace * fast_factor),
            target_pace_max=_seconds_to_pace(race_pace * prog_mults[1]),
            notes="Zügig, nahe HM-Pace",
        ),
        Segment(
            position=4,
            segment_type="cooldown",
            target_duration_minutes=cooldown_dur,
            target_pace_min=_seconds_to_pace(race_pace * easy_mults[0]),
            target_pace_max=_seconds_to_pace(race_pace * easy_mults[1]),
        ),
    ]
    sess.notes = f"Progressionslauf: 3 Stufen à {step_dur:.0f} Min."


def _enrich_fartlek_segments(
    sess: PlannedSession,
    week_in_phase: int,
    race_pace: float | None,
) -> None:
    """Baut Fartlek-Segmente: Warmup + alternierende schnell/locker Abschnitte + Cooldown.

    Jeder Tempowechsel wird als eigenes Segment angelegt, damit die Uhr
    den Athleten durch jeden Abschnitt führen kann.
    """
    rd = sess.run_details
    if not rd or not rd.segments or not race_pace:
        return

    idx = min(week_in_phase, len(_FARTLEK_PROGRESSION) - 1)
    fast_dur, slow_dur, repeats = _FARTLEK_PROGRESSION[idx]

    easy_mults = PACE_MULTIPLIERS["easy"]
    # Fartlek-Tempo: zwischen Tempo und Intervall-Pace
    fast_pace_min = _seconds_to_pace(race_pace * 0.92)
    fast_pace_max = _seconds_to_pace(race_pace * 1.02)
    easy_pace_min = _seconds_to_pace(race_pace * easy_mults[0])
    easy_pace_max = _seconds_to_pace(race_pace * easy_mults[1])

    segments: list[Segment] = [
        Segment(
            position=0,
            segment_type="warmup",
            target_duration_minutes=10.0,
            target_pace_min=easy_pace_min,
            target_pace_max=easy_pace_max,
        ),
    ]

    pos = 1
    for i in range(repeats):
        segments.append(
            Segment(
                position=pos,
                segment_type="work",
                target_duration_minutes=fast_dur,
                target_pace_min=fast_pace_min,
                target_pace_max=fast_pace_max,
                notes=f"Schnell ({i + 1}/{repeats})",
            )
        )
        pos += 1
        # Recovery nach jedem schnellen Abschnitt (außer dem letzten)
        if i < repeats - 1:
            segments.append(
                Segment(
                    position=pos,
                    segment_type="recovery_jog",
                    target_duration_minutes=slow_dur,
                    target_pace_min=easy_pace_min,
                    target_pace_max=easy_pace_max,
                )
            )
            pos += 1

    segments.append(
        Segment(
            position=pos,
            segment_type="cooldown",
            target_duration_minutes=10.0,
            target_pace_min=easy_pace_min,
            target_pace_max=easy_pace_max,
        )
    )

    rd.segments = segments
    sess.run_details = RunDetails(run_type="fartlek", segments=segments)
    sess.notes = f"{repeats}× ({fast_dur:.0f}' schnell / {slow_dur:.0f}' locker)"


def _insert_race_day(
    entries: list[WeeklyPlanEntry],
    race_date: date,
    goal: RaceGoalModel,
) -> None:
    """Fügt den Wettkampftag in den Wochenplan ein."""
    race_dow = race_date.weekday()  # 0=Mo, 6=So

    dist_km = float(goal.distance_km) if goal.distance_km else 21.0975
    race_pace = _compute_race_pace(goal)

    race_session = PlannedSession(
        position=0,
        training_type="running",
        run_details=_build_run_details("race", dist_km, race_pace),
        notes=f"🏁 WETTKAMPF: {goal.title or 'Rennen'}",
    )

    for entry in entries:
        if entry.day_of_week == race_dow:
            entry.is_rest_day = False
            entry.sessions = [race_session]
            entry.notes = f"Wettkampftag: {goal.title}"
            break


# --- Main Generator ---


def generate_weekly_plans(  # noqa: C901, PLR0912, PLR0915  # TODO: E16 Refactoring
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
                    is_rest_day=True,
                )
                for d in range(7)
            ]
            result.append((week_start, entries))
            continue

        phase_type = str(phase.phase_type)
        defaults = PHASE_DEFAULTS.get(phase_type, PHASE_DEFAULTS["base"])
        metrics = _parse_target_metrics(phase)

        # Compute week position within phase (needed for per-week templates + volume)
        phase_start_week = phase.start_week
        phase_end_week = phase.end_week
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
            # Collect all running PlannedSession objects with run_details
            running_sessions: list[PlannedSession] = []
            for e in entries:
                for s in e.sessions:
                    if s.training_type == "running" and s.run_details is not None:
                        running_sessions.append(s)

            if running_sessions:
                # Determine long run volume pct from template or defaults
                has_long_run = any(
                    s.run_details and s.run_details.run_type == "long_run" for s in running_sessions
                )
                if (per_week_template or shared_template) and has_long_run:
                    # Template path: use 0.30 default for long run share
                    long_run_pct: float = 0.30
                else:
                    long_run_pct = defaults["long_run_volume_pct"]
                long_run_km = weekly_volume * long_run_pct if long_run_pct > 0 else 0.0

                remaining_km = weekly_volume - long_run_km
                non_long = [
                    s
                    for s in running_sessions
                    if s.run_details and s.run_details.run_type != "long_run"
                ]
                _qual_vol = {"tempo", "intervals", "repetitions", "progression", "fartlek"}
                quality_sessions = [
                    s for s in non_long if s.run_details and s.run_details.run_type in _qual_vol
                ]
                easy_sessions = [
                    s for s in non_long if s.run_details and s.run_details.run_type not in _qual_vol
                ]

                quality_km_each = remaining_km * QUALITY_VOLUME_PCT if quality_sessions else 0.0
                quality_total_km = quality_km_each * len(quality_sessions)
                easy_total_km = remaining_km - quality_total_km
                easy_km_each = easy_total_km / len(easy_sessions) if easy_sessions else 0.0

                for sess in running_sessions:
                    if sess.run_details is None:
                        continue
                    # Skip sessions with explicit template RunDetails
                    if _has_explicit_run_details(sess.run_details):
                        continue
                    rt = sess.run_details.run_type
                    if rt == "long_run":
                        dist = long_run_km
                    elif rt in _qual_vol:
                        dist = quality_km_each
                    else:
                        dist = easy_km_each

                    sess.run_details = _build_run_details(rt, dist, race_pace)

        # Enrich sessions with structured segments (intervals, tempo, strides etc.)
        _enrich_sessions_for_week(
            entries,
            week_in_phase,
            phase_duration,
            phase_type,
            weekly_volume,
            race_pace,
        )

        # Add race day if this is the race week
        if goal and goal.race_date:
            race_date_obj = date(goal.race_date.year, goal.race_date.month, goal.race_date.day)
            if week_start <= race_date_obj < week_start + timedelta(days=7):
                _insert_race_day(entries, race_date_obj, goal)

        result.append((week_start, entries))

    return result
