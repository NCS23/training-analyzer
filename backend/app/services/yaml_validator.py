"""YAML training plan validation service.

Pure function — no DB access. Validates the parsed YAML dict (after yaml.safe_load,
before _yaml_to_plan_create) and returns structured errors and warnings.
"""

import math
import re
from datetime import date

from app.models.taxonomy import (
    SEGMENT_TYPE_MIGRATION,
    SEGMENT_TYPES,
    SESSION_TYPE_MIGRATION,
    SESSION_TYPES,
)
from app.models.yaml_validation import YamlValidationIssue, YamlValidationResult

_VALID_PHASE_TYPES = {"base", "build", "peak", "taper", "transition"}
_VALID_TRAINING_TYPES = {"strength", "running"}
_PACE_REGEX = re.compile(r"^\d{1,2}:\d{2}$")
_DOW_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _dow_name(dow: object) -> str:
    """Return short German day name for a day_of_week int, e.g. '2 (Mi)'."""
    if isinstance(dow, int) and 0 <= dow <= 6:
        return f"{dow} ({_DOW_NAMES[dow]})"
    return str(dow) if dow is not None else "?"


def validate_yaml_plan(raw: dict[str, object]) -> YamlValidationResult:
    """Validate a parsed YAML training plan dict.

    Returns structured errors (block import) and warnings (allow import).
    """
    errors: list[YamlValidationIssue] = []
    warnings: list[YamlValidationIssue] = []

    errors += _check_required_fields(raw)
    dates = _check_dates(raw, errors)
    _check_goal(raw, errors)
    _check_event_date(raw, dates, warnings)

    phases = raw.get("phases")
    if isinstance(phases, list) and dates:
        total_weeks = math.ceil((dates[1] - dates[0]).days / 7)
        _check_phases(phases, total_weeks, errors, warnings)

    return YamlValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _check_required_fields(raw: dict[str, object]) -> list[YamlValidationIssue]:
    issues: list[YamlValidationIssue] = []
    for field in ("name", "start_date", "end_date"):
        if not raw.get(field):
            issues.append(
                YamlValidationIssue(
                    code="missing_required_field",
                    level="error",
                    message=f"Pflichtfeld '{field}' fehlt.",
                    location=field,
                )
            )
    return issues


def _parse_date(value: object) -> date | None:
    """Try to parse a date from a string or date object."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def _check_dates(
    raw: dict[str, object],
    errors: list[YamlValidationIssue],
) -> tuple[date, date] | None:
    """Validate date fields. Returns (start_date, end_date) or None."""
    start = _parse_date(raw.get("start_date"))
    end = _parse_date(raw.get("end_date"))

    if raw.get("start_date") and start is None:
        errors.append(
            YamlValidationIssue(
                code="invalid_date_format",
                level="error",
                message=f"Ungueltiges Datumsformat fuer 'start_date': '{raw['start_date']}'. Erwartet: YYYY-MM-DD.",
                location="start_date",
            )
        )
    if raw.get("end_date") and end is None:
        errors.append(
            YamlValidationIssue(
                code="invalid_date_format",
                level="error",
                message=f"Ungueltiges Datumsformat fuer 'end_date': '{raw['end_date']}'. Erwartet: YYYY-MM-DD.",
                location="end_date",
            )
        )

    if start and end and start >= end:
        errors.append(
            YamlValidationIssue(
                code="date_range_invalid",
                level="error",
                message=f"'start_date' ({start}) muss vor 'end_date' ({end}) liegen.",
                location="end_date",
            )
        )
        return None

    if start and end:
        return (start, end)
    return None


def _check_goal(
    raw: dict[str, object],
    errors: list[YamlValidationIssue],
) -> None:
    goal = raw.get("goal")
    if not isinstance(goal, dict):
        return

    target_time = goal.get("target_time")
    if target_time is not None and "target_time_seconds" not in goal:
        try:
            _parse_time_to_seconds(str(target_time))
        except (ValueError, IndexError):
            errors.append(
                YamlValidationIssue(
                    code="invalid_target_time_format",
                    level="error",
                    message=f"Ungueltiges Zeitformat fuer 'goal.target_time': '{target_time}'. Erwartet: H:MM:SS oder MM:SS.",
                    location="goal.target_time",
                )
            )


def _parse_time_to_seconds(time_str: str) -> int:
    """Parse 'H:MM:SS' or 'MM:SS' to total seconds."""
    parts = time_str.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(time_str)


def _check_event_date(
    raw: dict[str, object],
    dates: tuple[date, date] | None,
    warnings: list[YamlValidationIssue],
) -> None:
    if not dates:
        return
    event_val = raw.get("target_event_date")
    if event_val is None:
        return
    event = _parse_date(event_val)
    if event and (event < dates[0] or event > dates[1]):
        warnings.append(
            YamlValidationIssue(
                code="event_date_outside_range",
                level="warning",
                message=f"'target_event_date' ({event}) liegt ausserhalb des Planzeitraums ({dates[0]} bis {dates[1]}).",
                location="target_event_date",
            )
        )


def _check_phases(
    phases: list[object],
    total_weeks: int,
    errors: list[YamlValidationIssue],
    warnings: list[YamlValidationIssue],
) -> None:
    """Validate all phases and cross-phase consistency."""
    parsed_ranges: list[tuple[int, int, str]] = []

    for i, phase in enumerate(phases):
        if not isinstance(phase, dict):
            continue
        loc = f"phases[{i}]"
        name = str(phase.get("name", f"Phase {i + 1}"))

        # phase_type
        ptype = phase.get("type") or phase.get("phase_type")
        if ptype and str(ptype) not in _VALID_PHASE_TYPES:
            errors.append(
                YamlValidationIssue(
                    code="invalid_phase_type",
                    level="error",
                    message=f"Ungueltiger Phasentyp '{ptype}' in '{name}'. Erlaubt: {', '.join(sorted(_VALID_PHASE_TYPES))}.",
                    location=f"{loc}.type",
                )
            )

        # start_week / end_week
        sw = phase.get("start_week")
        ew = phase.get("end_week")
        if isinstance(sw, int) and isinstance(ew, int):
            if ew < sw:
                errors.append(
                    YamlValidationIssue(
                        code="phase_end_before_start",
                        level="error",
                        message=f"In '{name}': end_week ({ew}) ist kleiner als start_week ({sw}).",
                        location=f"{loc}.end_week",
                    )
                )
            else:
                parsed_ranges.append((sw, ew, name))

                # Phase exceeds plan
                if ew > total_weeks:
                    warnings.append(
                        YamlValidationIssue(
                            code="phase_exceeds_plan_duration",
                            level="warning",
                            message=f"'{name}' endet in Woche {ew}, aber der Plan hat nur {total_weeks} Wochen.",
                            location=f"{loc}.end_week",
                        )
                    )

        # weekly_template checks
        wt = phase.get("weekly_template")
        if isinstance(wt, list):
            _check_weekly_template(wt, name, loc, errors, warnings)

        # target_metrics checks
        tm = phase.get("target_metrics")
        if isinstance(tm, dict):
            _check_metrics(tm, name, loc, warnings)

    # Phase overlaps
    _check_phase_overlaps(parsed_ranges, warnings)

    # Coverage gaps
    if parsed_ranges:
        _check_phase_coverage(parsed_ranges, total_weeks, warnings)


def _check_weekly_template(
    days: list[object],
    phase_name: str,
    phase_loc: str,
    errors: list[YamlValidationIssue],
    warnings: list[YamlValidationIssue],
) -> None:
    """Validate a weekly_template day list."""
    seen_days: dict[int, int] = {}
    for j, day_entry in enumerate(days):
        if not isinstance(day_entry, dict):
            continue
        day_loc = f"{phase_loc}.weekly_template[{j}]"
        dow = day_entry.get("day")
        if isinstance(dow, int):
            if dow in seen_days:
                warnings.append(
                    YamlValidationIssue(
                        code="duplicate_day_of_week",
                        level="warning",
                        message=f"In '{phase_name}': Tag {dow} ist doppelt definiert (Eintrag {seen_days[dow] + 1} und {j + 1}).",
                        location=day_loc,
                    )
                )
            seen_days[dow] = j

        # training_type check
        training_type = day_entry.get("type")
        if (
            training_type
            and not day_entry.get("rest")
            and str(training_type) not in _VALID_TRAINING_TYPES
        ):
            errors.append(
                YamlValidationIssue(
                    code="invalid_training_type",
                    level="error",
                    message=(
                        f"In '{phase_name}', Tag {_dow_name(dow)}: "
                        f"Trainingstyp '{training_type}' ist ungueltig. "
                        f"Erlaubt: {', '.join(sorted(_VALID_TRAINING_TYPES))}."
                    ),
                    location=f"{day_loc}.type",
                )
            )

        # run_type check (outer)
        outer_run_type = day_entry.get("run_type")
        if outer_run_type:
            _check_type_value(
                str(outer_run_type),
                SESSION_TYPES,
                SESSION_TYPE_MIGRATION,
                "run_type",
                "invalid_run_type",
                "legacy_run_type",
                phase_name,
                dow,
                day_loc,
                errors,
                warnings,
            )

        rd = day_entry.get("run_details")

        # run_type consistency
        if isinstance(rd, dict) and outer_run_type:
            inner_run_type = rd.get("run_type")
            if inner_run_type and str(outer_run_type) != str(inner_run_type):
                warnings.append(
                    YamlValidationIssue(
                        code="run_type_mismatch",
                        level="warning",
                        message=f"In '{phase_name}', Tag {_dow_name(dow)}: run_type '{outer_run_type}' widerspricht run_details.run_type '{inner_run_type}'.",
                        location=f"{day_loc}.run_type",
                    )
                )

        # run_details checks
        if isinstance(rd, dict):
            # run_details.run_type check
            inner_rt = rd.get("run_type")
            if inner_rt:
                _check_type_value(
                    str(inner_rt),
                    SESSION_TYPES,
                    SESSION_TYPE_MIGRATION,
                    "run_details.run_type",
                    "invalid_run_type",
                    "legacy_run_type",
                    phase_name,
                    dow,
                    day_loc,
                    errors,
                    warnings,
                )

            _check_pace_fields(rd, f"{day_loc}.run_details", warnings)

            # Interval checks
            intervals = rd.get("intervals")
            if isinstance(intervals, list):
                for k, interval in enumerate(intervals):
                    if isinstance(interval, dict):
                        # Segment type check
                        seg_type = interval.get("type")
                        if seg_type:
                            _check_segment_type(
                                str(seg_type),
                                phase_name,
                                dow,
                                k,
                                day_loc,
                                errors,
                                warnings,
                            )
                        _check_pace_fields(
                            interval,
                            f"{day_loc}.run_details.intervals[{k}]",
                            warnings,
                        )


def _check_type_value(
    value: str,
    valid_set: frozenset[str],
    migration_map: dict[str, str],
    field_name: str,
    error_code: str,
    legacy_code: str,
    phase_name: str,
    dow: object,
    day_loc: str,
    errors: list[YamlValidationIssue],
    warnings: list[YamlValidationIssue],
) -> None:
    """Check a type value against a canonical set and legacy migration map."""
    if value in valid_set:
        return
    migration = migration_map.get(value)
    if migration:
        warnings.append(
            YamlValidationIssue(
                code=legacy_code,
                level="warning",
                message=(
                    f"In '{phase_name}', Tag {_dow_name(dow)}: "
                    f"{field_name} '{value}' wird automatisch zu '{migration}' migriert."
                ),
                location=f"{day_loc}.{field_name}",
            )
        )
    else:
        errors.append(
            YamlValidationIssue(
                code=error_code,
                level="error",
                message=(
                    f"In '{phase_name}', Tag {_dow_name(dow)}: "
                    f"{field_name} '{value}' ist ungueltig. "
                    f"Erlaubt: {', '.join(sorted(valid_set))}."
                ),
                location=f"{day_loc}.{field_name}",
            )
        )


def _check_segment_type(
    value: str,
    phase_name: str,
    dow: object,
    interval_idx: int,
    day_loc: str,
    errors: list[YamlValidationIssue],
    warnings: list[YamlValidationIssue],
) -> None:
    """Check an interval segment type against SEGMENT_TYPES + migration map."""
    if value in SEGMENT_TYPES:
        return
    migration = SEGMENT_TYPE_MIGRATION.get(value)
    loc = f"{day_loc}.run_details.intervals[{interval_idx}].type"
    if migration:
        warnings.append(
            YamlValidationIssue(
                code="legacy_segment_type",
                level="warning",
                message=(
                    f"In '{phase_name}', Tag {_dow_name(dow)}, "
                    f"Intervall {interval_idx + 1}: Typ '{value}' "
                    f"wird automatisch zu '{migration}' migriert."
                ),
                location=loc,
            )
        )
    else:
        errors.append(
            YamlValidationIssue(
                code="invalid_segment_type",
                level="error",
                message=(
                    f"In '{phase_name}', Tag {_dow_name(dow)}, "
                    f"Intervall {interval_idx + 1}: Typ '{value}' ist ungueltig. "
                    f"Erlaubt: {', '.join(sorted(SEGMENT_TYPES))}."
                ),
                location=loc,
            )
        )


def _check_pace_fields(
    obj: dict[str, object],
    loc: str,
    warnings: list[YamlValidationIssue],
) -> None:
    """Check pace format and min/max consistency."""
    pace_min = obj.get("target_pace_min")
    pace_max = obj.get("target_pace_max")

    for field, val in [("target_pace_min", pace_min), ("target_pace_max", pace_max)]:
        if val is not None and not _PACE_REGEX.match(str(val)):
            warnings.append(
                YamlValidationIssue(
                    code="invalid_pace_format",
                    level="warning",
                    message=f"Pace '{val}' hat ungueltiges Format. Erwartet: M:SS (z.B. '5:30').",
                    location=f"{loc}.{field}",
                )
            )

    # Inverted pace range (pace_min should be faster = lower value)
    if (
        pace_min is not None
        and pace_max is not None
        and _PACE_REGEX.match(str(pace_min))
        and _PACE_REGEX.match(str(pace_max))
    ):
        min_secs = _pace_to_seconds(str(pace_min))
        max_secs = _pace_to_seconds(str(pace_max))
        if min_secs > max_secs:
            warnings.append(
                YamlValidationIssue(
                    code="inverted_range",
                    level="warning",
                    message=f"Pace-Bereich invertiert: target_pace_min ({pace_min}) ist langsamer als target_pace_max ({pace_max}).",
                    location=f"{loc}.target_pace_min",
                )
            )

    # HR range check
    hr_min = obj.get("target_hr_min")
    hr_max = obj.get("target_hr_max")
    if isinstance(hr_min, int | float) and isinstance(hr_max, int | float) and hr_min > hr_max:
        warnings.append(
            YamlValidationIssue(
                code="inverted_range",
                level="warning",
                message=f"HR-Bereich invertiert: target_hr_min ({hr_min}) ist groesser als target_hr_max ({hr_max}).",
                location=f"{loc}.target_hr_min",
            )
        )


def _pace_to_seconds(pace_str: str) -> int:
    """Convert 'M:SS' pace to seconds."""
    parts = pace_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _check_metrics(
    metrics: dict[str, object],
    phase_name: str,
    phase_loc: str,
    warnings: list[YamlValidationIssue],
) -> None:
    """Check target_metrics for inverted ranges."""
    vol_min = metrics.get("weekly_volume_min")
    vol_max = metrics.get("weekly_volume_max")
    if isinstance(vol_min, int | float) and isinstance(vol_max, int | float) and vol_min > vol_max:
        warnings.append(
            YamlValidationIssue(
                code="inverted_range",
                level="warning",
                message=f"In '{phase_name}': weekly_volume_min ({vol_min}) ist groesser als weekly_volume_max ({vol_max}).",
                location=f"{phase_loc}.target_metrics.weekly_volume_min",
            )
        )


def _check_phase_overlaps(
    ranges: list[tuple[int, int, str]],
    warnings: list[YamlValidationIssue],
) -> None:
    """Check for overlapping phase week ranges."""
    for i in range(len(ranges)):
        for j in range(i + 1, len(ranges)):
            s1, e1, n1 = ranges[i]
            s2, e2, n2 = ranges[j]
            if s1 <= e2 and s2 <= e1:
                overlap_start = max(s1, s2)
                overlap_end = min(e1, e2)
                warnings.append(
                    YamlValidationIssue(
                        code="phase_overlap",
                        level="warning",
                        message=f"Phasen '{n1}' und '{n2}' ueberlappen sich in Woche {overlap_start}-{overlap_end}.",
                        location="phases",
                    )
                )


def _check_phase_coverage(
    ranges: list[tuple[int, int, str]],
    total_weeks: int,
    warnings: list[YamlValidationIssue],
) -> None:
    """Check for weeks not covered by any phase."""
    covered: set[int] = set()
    for sw, ew, _ in ranges:
        for w in range(sw, min(ew, total_weeks) + 1):
            covered.add(w)

    uncovered = sorted(w for w in range(1, total_weeks + 1) if w not in covered)
    if uncovered:
        if len(uncovered) <= 5:
            week_str = ", ".join(str(w) for w in uncovered)
        else:
            week_str = (
                ", ".join(str(w) for w in uncovered[:5]) + f" (und {len(uncovered) - 5} weitere)"
            )
        warnings.append(
            YamlValidationIssue(
                code="phase_coverage_gap",
                level="warning",
                message=f"Wochen ohne Phase: {week_str}. Diese Wochen werden als Ruhewochen generiert.",
                location="phases",
            )
        )
