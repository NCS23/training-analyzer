"""FIT File Parser for Garmin/Wahoo/etc. training exports."""

from datetime import datetime
from typing import Optional

from app.models.training import TrainingType
from app.services.gps_extractor import extract_gps_track
from app.services.parser_interface import TrainingParser, classify_laps


class TrainingFITParser(TrainingParser):
    """
    Parser for ANT+ FIT files (Garmin, Wahoo, Suunto, etc.)

    Uses fitparse library to extract:
    - Session summary (duration, distance, HR, cadence)
    - Lap data (splits, HR per lap, pace)
    - Record data (second-by-second HR timeseries)
    """

    def parse(
        self,
        file_content: bytes,
        training_type: TrainingType,
        training_subtype: Optional[str] = None,
    ) -> dict:
        try:
            import fitparse  # type: ignore[import-untyped]
        except ImportError:
            return {
                "success": False,
                "errors": ["fitparse library not installed. Run: pip install fitparse"],
            }

        try:
            fitfile = fitparse.FitFile(file_content)
            fitfile.parse()

            # Extract data from FIT messages
            session_data = self._extract_session(fitfile)
            laps_data = self._extract_laps(fitfile)
            records_data = self._extract_records(fitfile)

            # Auto-detect training type from FIT sport field
            detected_type = self._detect_training_type(session_data, training_type)

            # Build summary
            summary = self._build_summary(session_data, records_data, detected_type)

            # Build laps (only for running)
            laps = None
            if detected_type == TrainingType.RUNNING and laps_data:
                laps = self._build_laps(laps_data)
                laps = classify_laps(laps, training_subtype)

            # Build HR timeseries (for strength or as raw data)
            hr_timeseries = self._build_hr_timeseries(records_data)

            # Extract GPS track
            gps_track = extract_gps_track(records_data)

            result: dict = {
                "success": True,
                "metadata": {
                    "training_type": detected_type.value,
                    "training_subtype": training_subtype,
                    "total_rows": len(records_data),
                    "parsed_at": datetime.utcnow().isoformat(),
                    "source_format": "FIT",
                },
                "summary": summary,
            }

            if laps:
                result["laps"] = laps
            if hr_timeseries:
                result["hr_timeseries"] = hr_timeseries
            if gps_track:
                result["gps_track"] = gps_track

            return result

        except Exception as e:
            return {
                "success": False,
                "errors": [f"FIT Parse Error: {str(e)}"],
            }

    def _extract_session(self, fitfile) -> dict:
        """Extract session-level data from FIT file."""
        session = {}
        for record in fitfile.get_messages("session"):
            for field in record:
                session[field.name] = field.value
        return session

    def _extract_laps(self, fitfile) -> list[dict]:
        """Extract lap data from FIT file."""
        laps = []
        for record in fitfile.get_messages("lap"):
            lap = {}
            for field in record:
                lap[field.name] = field.value
            laps.append(lap)
        return laps

    def _extract_records(self, fitfile) -> list[dict]:
        """Extract second-by-second record data."""
        records = []
        for record in fitfile.get_messages("record"):
            row = {}
            for field in record:
                row[field.name] = field.value
            records.append(row)
        return records

    def _detect_training_type(self, session_data: dict, fallback: TrainingType) -> TrainingType:
        """Detect training type from FIT sport field."""
        sport = session_data.get("sport")
        if sport is not None:
            sport_str = str(sport).lower()
            if sport_str in ("running", "trail_running", "treadmill_running"):
                return TrainingType.RUNNING
            # Strength-related sports
            if sport_str in ("training", "fitness_equipment", "generic"):
                return TrainingType.STRENGTH
        return fallback

    def _build_summary(
        self, session_data: dict, records: list[dict], training_type: TrainingType
    ) -> dict:
        """Build summary dict matching CSV parser format."""
        total_duration = session_data.get("total_timer_time")
        total_distance = session_data.get("total_distance")
        avg_hr = session_data.get("avg_heart_rate")
        max_hr = session_data.get("max_heart_rate")
        avg_cadence = session_data.get("avg_running_cadence") or session_data.get("avg_cadence")

        # Compute min HR from records if not in session
        min_hr = None
        hr_values = [int(r["heart_rate"]) for r in records if r.get("heart_rate") is not None]
        if hr_values:
            min_hr = min(hr_values)

        duration_sec = int(total_duration) if total_duration else 0
        distance_km = (total_distance / 1000.0) if total_distance else None

        # Pace (min/km)
        avg_pace = None
        avg_pace_formatted = None
        if distance_km and distance_km > 0 and duration_sec > 0:
            avg_pace = (duration_sec / 60.0) / distance_km
            pace_min = int(avg_pace)
            pace_sec = int((avg_pace - pace_min) * 60)
            avg_pace_formatted = f"{pace_min}:{pace_sec:02d}"

        summary: dict = {
            "total_duration_seconds": duration_sec,
            "total_duration_formatted": self._format_duration(duration_sec),
            "avg_hr_bpm": int(avg_hr) if avg_hr else None,
            "max_hr_bpm": int(max_hr) if max_hr else None,
            "min_hr_bpm": int(min_hr) if min_hr else None,
        }

        if training_type == TrainingType.RUNNING:
            summary.update(
                {
                    "total_distance_km": round(distance_km, 2) if distance_km else None,
                    "avg_pace_min_per_km": round(avg_pace, 2) if avg_pace else None,
                    "avg_pace_formatted": avg_pace_formatted,
                    "avg_cadence_spm": int(avg_cadence * 2) if avg_cadence else None,
                    # FIT stores half-cycles, multiply by 2 for spm
                }
            )

        return summary

    def _build_laps(self, laps_data: list[dict]) -> list[dict]:
        """Build lap list matching CSV parser format."""
        laps = []
        for i, lap in enumerate(laps_data, start=1):
            duration = lap.get("total_timer_time", 0)
            distance = lap.get("total_distance")
            avg_hr = lap.get("avg_heart_rate")
            max_hr = lap.get("max_heart_rate")
            min_hr = lap.get("min_heart_rate")
            cadence = lap.get("avg_running_cadence") or lap.get("avg_cadence")

            duration_sec = int(duration) if duration else 0
            distance_km = round(distance / 1000.0, 2) if distance else None

            pace = None
            pace_formatted = None
            if distance_km and distance_km > 0 and duration_sec > 0:
                pace = (duration_sec / 60.0) / distance_km
                pace_min = int(pace)
                pace_sec = int((pace - pace_min) * 60)
                pace_formatted = f"{pace_min}:{pace_sec:02d}"

            laps.append(
                {
                    "lap_number": i,
                    "duration_seconds": duration_sec,
                    "duration_formatted": self._format_duration(duration_sec),
                    "distance_km": distance_km,
                    "pace_min_per_km": round(pace, 2) if pace else None,
                    "pace_formatted": pace_formatted,
                    "avg_hr_bpm": int(avg_hr) if avg_hr else None,
                    "max_hr_bpm": int(max_hr) if max_hr else None,
                    "min_hr_bpm": int(min_hr) if min_hr else None,
                    "avg_cadence_spm": int(cadence * 2) if cadence else None,
                    "suggested_type": None,
                    "confidence": None,
                    "user_override": None,
                }
            )
        return laps

    def _build_hr_timeseries(self, records: list[dict]) -> list[dict]:
        """Build HR timeseries from record messages."""
        timeseries = []
        start_ts = None

        for record in records:
            hr = record.get("heart_rate")
            ts = record.get("timestamp")
            if hr and ts:
                if start_ts is None:
                    start_ts = ts
                elapsed = (ts - start_ts).total_seconds() if start_ts else 0
                timeseries.append(
                    {
                        "seconds": int(elapsed),
                        "hr_bpm": int(hr),
                        "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                    }
                )

        return timeseries

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds to HH:MM:SS or MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
