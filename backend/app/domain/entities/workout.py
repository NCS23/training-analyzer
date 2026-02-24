from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Workout:
    id: Optional[int] = None
    date: datetime = datetime.now()
    workout_type: str = "running"  # running, strength
    subtype: Optional[str] = None  # quality, recovery, longrun, studio_tag1, studio_tag2

    # Running data
    duration_sec: Optional[int] = None
    distance_km: Optional[float] = None
    pace: Optional[str] = None  # "6:31"
    hr_avg: Optional[int] = None
    hr_max: Optional[int] = None
    hr_min: Optional[int] = None

    # Metadata
    csv_data: Optional[str] = None
    warnings: list[str] = None
    ai_analysis: Optional[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
