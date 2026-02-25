"""Test data factories for domain entities."""

from datetime import datetime
from typing import Optional

from app.domain.entities.workout import Workout


def make_workout(
    id: Optional[int] = 1,
    date: Optional[datetime] = None,
    workout_type: str = "running",
    subtype: Optional[str] = "interval",
    duration_sec: Optional[int] = 3600,
    distance_km: Optional[float] = 10.5,
    pace: Optional[str] = "5:43",
    hr_avg: Optional[int] = 155,
    hr_max: Optional[int] = 178,
    hr_min: Optional[int] = 120,
) -> Workout:
    """Create a Workout entity with sensible defaults."""
    return Workout(
        id=id,
        date=date or datetime(2024, 3, 15, 7, 30),
        workout_type=workout_type,
        subtype=subtype,
        duration_sec=duration_sec,
        distance_km=distance_km,
        pace=pace,
        hr_avg=hr_avg,
        hr_max=hr_max,
        hr_min=hr_min,
    )


def make_running_workout(**overrides) -> Workout:  # type: ignore[no-untyped-def]
    """Create a running workout."""
    return make_workout(workout_type="running", **overrides)


def make_strength_workout(**overrides) -> Workout:  # type: ignore[no-untyped-def]
    """Create a strength workout."""
    return make_workout(
        workout_type="strength",
        subtype="knee_dominant",
        distance_km=None,
        pace=None,
        duration_sec=2700,
        **overrides,
    )


SAMPLE_CSV_RUNNING = """\
Lap;Duration;Distance;Avg Pace;Avg Heart Rate;Max Heart Rate;Min Heart Rate;Avg Cadence
1;05:00;1.00;5:00;140;150;130;170
2;03:30;0.80;4:23;165;175;155;180
3;02:00;0.30;6:40;135;145;125;160
4;03:30;0.80;4:23;168;180;158;182
5;05:00;1.00;5:00;130;140;120;165
"""

SAMPLE_CSV_STRENGTH = """\
Timestamp;Heart Rate
2024-03-15 07:30:00;80
2024-03-15 07:30:10;85
2024-03-15 07:30:20;110
2024-03-15 07:30:30;130
2024-03-15 07:30:40;145
"""
