"""Abstract interface for training file parsers (CSV, FIT, etc.)."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.training import TrainingType


class TrainingParser(ABC):
    """Common interface for all training file parsers.

    Every parser must implement `parse()` returning a dict with:
    - success: bool
    - errors: list[str]          (if success=False)
    - metadata: dict             (training_type, parsed_at, ...)
    - summary: dict              (total_distance_km, total_duration_seconds, ...)
    - laps: list[dict] | None    (for running)
    - hr_timeseries: list | None (for strength / raw HR data)
    """

    @abstractmethod
    def parse(
        self,
        file_content: bytes,
        training_type: TrainingType,
        training_subtype: Optional[str] = None,
    ) -> dict:
        """Parse a training file and return structured data."""
        ...


def classify_laps(laps: list[dict], training_subtype: Optional[str] = None) -> list[dict]:  # noqa: C901, PLR0912  # TODO: E16 Refactoring
    """Classify laps based on training subtype and metrics.

    Shared between CSV and FIT parsers. Adds suggested_type,
    confidence, and user_override fields to each lap.
    """
    if len(laps) == 0:
        return laps

    for i, lap in enumerate(laps):
        is_first = i == 0
        is_last = i == len(laps) - 1

        suggested_type = "steady"
        confidence = "low"

        avg_hr = lap.get("avg_hr_bpm")
        duration = lap.get("duration_seconds", 0)

        if training_subtype == "interval":
            if is_first and avg_hr and avg_hr < 140 and duration < 600:
                suggested_type = "warmup"
                confidence = "high"
            elif is_last and avg_hr and avg_hr < 150 and duration < 600:
                suggested_type = "cooldown"
                confidence = "high"
            elif avg_hr and avg_hr > 160:
                suggested_type = "work"
                confidence = "high" if avg_hr > 170 else "medium"
            elif avg_hr and avg_hr < 150:
                suggested_type = "rest"
                confidence = "medium"
            else:
                suggested_type = "work"
                confidence = "low"

        elif training_subtype in ("tempo", "longrun"):
            if is_first and duration < 600:
                suggested_type = "warmup"
                confidence = "medium"
            elif is_last and duration < 600:
                suggested_type = "cooldown"
                confidence = "medium"
            else:
                suggested_type = "steady"
                confidence = "high"

        elif training_subtype == "recovery":
            suggested_type = "recovery_jog"
            confidence = "high"

        # Fallback: heuristic based on metrics
        elif is_first and avg_hr and avg_hr < 140:
            suggested_type = "warmup"
            confidence = "low"
        elif is_last and avg_hr and avg_hr < 150:
            suggested_type = "cooldown"
            confidence = "low"
        elif avg_hr and avg_hr > 165:
            suggested_type = "work"
            confidence = "low"

        lap["suggested_type"] = suggested_type
        lap["confidence"] = confidence
        if "user_override" not in lap:
            lap["user_override"] = None

    return laps
