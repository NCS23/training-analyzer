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
