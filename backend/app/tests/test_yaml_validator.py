"""Tests for YAML training plan validation service."""

from typing import Any

import pytest
from httpx import AsyncClient

from app.services.yaml_validator import validate_yaml_plan

VALID_RAW: dict[str, Any] = {
    "name": "Test Plan",
    "start_date": "2026-04-06",
    "end_date": "2026-07-26",
    "status": "draft",
}


def _has_code(issues: list, code: str) -> bool:  # type: ignore[type-arg]
    return any(i.code == code for i in issues)


class TestRequiredFields:
    def test_valid_minimal_plan(self) -> None:
        result = validate_yaml_plan(VALID_RAW)
        assert result.valid is True
        assert result.errors == []

    def test_missing_name(self) -> None:
        raw = {k: v for k, v in VALID_RAW.items() if k != "name"}
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "missing_required_field")

    def test_missing_start_date(self) -> None:
        raw = {k: v for k, v in VALID_RAW.items() if k != "start_date"}
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "missing_required_field")

    def test_missing_end_date(self) -> None:
        raw = {k: v for k, v in VALID_RAW.items() if k != "end_date"}
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "missing_required_field")

    def test_multiple_missing_fields(self) -> None:
        result = validate_yaml_plan({})
        assert result.valid is False
        missing = [e for e in result.errors if e.code == "missing_required_field"]
        assert len(missing) == 3


class TestDateValidation:
    def test_invalid_date_format(self) -> None:
        raw = {**VALID_RAW, "start_date": "not-a-date"}
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "invalid_date_format")

    def test_start_after_end(self) -> None:
        raw = {**VALID_RAW, "start_date": "2026-08-01", "end_date": "2026-07-01"}
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "date_range_invalid")

    def test_start_equals_end(self) -> None:
        raw = {**VALID_RAW, "start_date": "2026-07-01", "end_date": "2026-07-01"}
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "date_range_invalid")

    def test_event_date_outside_range(self) -> None:
        raw = {**VALID_RAW, "target_event_date": "2025-01-01"}
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "event_date_outside_range")


class TestGoalValidation:
    def test_valid_target_time(self) -> None:
        raw = {
            **VALID_RAW,
            "goal": {
                "title": "HM",
                "distance_km": 21.1,
                "target_time": "1:59:00",
            },
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert not _has_code(result.errors, "invalid_target_time_format")

    def test_invalid_target_time(self) -> None:
        raw = {
            **VALID_RAW,
            "goal": {
                "title": "HM",
                "distance_km": 21.1,
                "target_time": "banana",
            },
        }
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "invalid_target_time_format")

    def test_target_time_weird_format(self) -> None:
        raw = {
            **VALID_RAW,
            "goal": {
                "title": "HM",
                "distance_km": 21.1,
                "target_time": "1h59m",
            },
        }
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "invalid_target_time_format")

    def test_target_time_seconds_skips_validation(self) -> None:
        raw = {
            **VALID_RAW,
            "goal": {
                "title": "HM",
                "distance_km": 21.1,
                "target_time_seconds": 7140,
            },
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True


class TestPhaseValidation:
    def test_invalid_phase_type(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [{"name": "Bad", "type": "marathon", "start_week": 1, "end_week": 4}],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "invalid_phase_type")

    def test_end_before_start(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [{"name": "Bad", "type": "base", "start_week": 10, "end_week": 3}],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is False
        assert _has_code(result.errors, "phase_end_before_start")

    def test_phase_overlap(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {"name": "Base", "type": "base", "start_week": 1, "end_week": 6},
                {"name": "Build", "type": "build", "start_week": 5, "end_week": 10},
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "phase_overlap")

    def test_phase_coverage_gap(self) -> None:
        # 16-week plan with phases covering 1-4 and 8-12 -> gap at 5-7
        raw = {
            **VALID_RAW,
            "start_date": "2026-04-06",
            "end_date": "2026-07-27",  # ~16 weeks
            "phases": [
                {"name": "P1", "type": "base", "start_week": 1, "end_week": 4},
                {"name": "P2", "type": "build", "start_week": 8, "end_week": 12},
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "phase_coverage_gap")

    def test_phase_exceeds_plan(self) -> None:
        raw = {
            **VALID_RAW,
            "start_date": "2026-04-06",
            "end_date": "2026-06-01",  # ~8 weeks
            "phases": [{"name": "P1", "type": "base", "start_week": 1, "end_week": 20}],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "phase_exceeds_plan_duration")

    def test_valid_phases(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {"name": "Base", "type": "base", "start_week": 1, "end_week": 8},
                {"name": "Build", "type": "build", "start_week": 9, "end_week": 16},
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert not _has_code(result.warnings, "phase_overlap")


class TestWeeklyTemplateValidation:
    def test_duplicate_day_of_week(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "base",
                    "start_week": 1,
                    "end_week": 4,
                    "weekly_template": [
                        {"day": 0, "type": "running", "run_type": "easy"},
                        {"day": 0, "type": "strength"},
                        {"day": 2, "type": "running", "run_type": "easy"},
                        {"day": 3, "rest": True},
                        {"day": 4, "type": "running", "run_type": "long_run"},
                        {"day": 5, "type": "running", "run_type": "tempo"},
                        {"day": 6, "rest": True},
                    ],
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "duplicate_day_of_week")

    def test_run_type_mismatch(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "base",
                    "start_week": 1,
                    "end_week": 4,
                    "weekly_template": [
                        {
                            "day": 0,
                            "type": "running",
                            "run_type": "easy",
                            "run_details": {
                                "run_type": "intervals",
                                "target_duration_minutes": 60,
                            },
                        },
                        {"day": 1, "rest": True},
                        {"day": 2, "rest": True},
                        {"day": 3, "rest": True},
                        {"day": 4, "rest": True},
                        {"day": 5, "rest": True},
                        {"day": 6, "rest": True},
                    ],
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "run_type_mismatch")


class TestPaceValidation:
    def test_invalid_pace_format(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "base",
                    "start_week": 1,
                    "end_week": 4,
                    "weekly_template": [
                        {
                            "day": 0,
                            "type": "running",
                            "run_type": "easy",
                            "run_details": {
                                "run_type": "easy",
                                "target_pace_min": "banana",
                            },
                        },
                        {"day": 1, "rest": True},
                        {"day": 2, "rest": True},
                        {"day": 3, "rest": True},
                        {"day": 4, "rest": True},
                        {"day": 5, "rest": True},
                        {"day": 6, "rest": True},
                    ],
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "invalid_pace_format")

    def test_inverted_pace_range(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "base",
                    "start_week": 1,
                    "end_week": 4,
                    "weekly_template": [
                        {
                            "day": 0,
                            "type": "running",
                            "run_type": "easy",
                            "run_details": {
                                "run_type": "easy",
                                "target_pace_min": "6:00",
                                "target_pace_max": "5:00",
                            },
                        },
                        {"day": 1, "rest": True},
                        {"day": 2, "rest": True},
                        {"day": 3, "rest": True},
                        {"day": 4, "rest": True},
                        {"day": 5, "rest": True},
                        {"day": 6, "rest": True},
                    ],
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "inverted_range")

    def test_valid_pace_format(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "base",
                    "start_week": 1,
                    "end_week": 4,
                    "weekly_template": [
                        {
                            "day": 0,
                            "type": "running",
                            "run_type": "easy",
                            "run_details": {
                                "run_type": "easy",
                                "target_pace_min": "5:30",
                                "target_pace_max": "6:00",
                            },
                        },
                        {"day": 1, "rest": True},
                        {"day": 2, "rest": True},
                        {"day": 3, "rest": True},
                        {"day": 4, "rest": True},
                        {"day": 5, "rest": True},
                        {"day": 6, "rest": True},
                    ],
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert not _has_code(result.warnings, "invalid_pace_format")
        assert not _has_code(result.warnings, "inverted_range")

    def test_inverted_hr_range(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "base",
                    "start_week": 1,
                    "end_week": 4,
                    "weekly_template": [
                        {
                            "day": 0,
                            "type": "running",
                            "run_type": "easy",
                            "run_details": {
                                "run_type": "easy",
                                "target_hr_min": 180,
                                "target_hr_max": 120,
                            },
                        },
                        {"day": 1, "rest": True},
                        {"day": 2, "rest": True},
                        {"day": 3, "rest": True},
                        {"day": 4, "rest": True},
                        {"day": 5, "rest": True},
                        {"day": 6, "rest": True},
                    ],
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert _has_code(result.warnings, "inverted_range")

    def test_interval_pace_check(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "peak",
                    "start_week": 1,
                    "end_week": 4,
                    "weekly_template": [
                        {
                            "day": 0,
                            "type": "running",
                            "run_type": "intervals",
                            "run_details": {
                                "run_type": "intervals",
                                "intervals": [
                                    {
                                        "type": "work",
                                        "duration_minutes": 3,
                                        "target_pace_min": "nope",
                                    }
                                ],
                            },
                        },
                        {"day": 1, "rest": True},
                        {"day": 2, "rest": True},
                        {"day": 3, "rest": True},
                        {"day": 4, "rest": True},
                        {"day": 5, "rest": True},
                        {"day": 6, "rest": True},
                    ],
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert _has_code(result.warnings, "invalid_pace_format")


class TestMetricsValidation:
    def test_inverted_volume_range(self) -> None:
        raw = {
            **VALID_RAW,
            "phases": [
                {
                    "name": "P1",
                    "type": "base",
                    "start_week": 1,
                    "end_week": 4,
                    "target_metrics": {
                        "weekly_volume_min": 50,
                        "weekly_volume_max": 30,
                    },
                }
            ],
        }
        result = validate_yaml_plan(raw)
        assert result.valid is True
        assert _has_code(result.warnings, "inverted_range")


class TestValidateYamlEndpoint:
    """API-level tests (require AsyncClient)."""

    @pytest.mark.anyio
    async def test_validate_valid_yaml(self, client: "AsyncClient") -> None:
        yaml_content = b"name: Test\nstart_date: 2026-04-06\nend_date: 2026-07-26\n"
        response = await client.post(
            "/api/v1/training-plans/validate-yaml",
            files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is True
        assert body["errors"] == []

    @pytest.mark.anyio
    async def test_validate_with_errors(self, client: "AsyncClient") -> None:
        yaml_content = b"start_date: 2026-04-06\nend_date: 2026-07-26\n"
        response = await client.post(
            "/api/v1/training-plans/validate-yaml",
            files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert len(body["errors"]) > 0

    @pytest.mark.anyio
    async def test_validate_non_yaml_file(self, client: "AsyncClient") -> None:
        response = await client.post(
            "/api/v1/training-plans/validate-yaml",
            files={"yaml_file": ("plan.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any(e["code"] == "invalid_file_extension" for e in body["errors"])

    @pytest.mark.anyio
    async def test_validate_empty_yaml(self, client: "AsyncClient") -> None:
        response = await client.post(
            "/api/v1/training-plans/validate-yaml",
            files={"yaml_file": ("plan.yaml", b"", "application/x-yaml")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any(e["code"] == "empty_file" for e in body["errors"])

    @pytest.mark.anyio
    async def test_validate_invalid_yaml_syntax(self, client: "AsyncClient") -> None:
        yaml_content = b"name: [\ninvalid yaml"
        response = await client.post(
            "/api/v1/training-plans/validate-yaml",
            files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any(e["code"] == "yaml_syntax_error" for e in body["errors"])

    @pytest.mark.anyio
    async def test_validate_with_warnings_only(self, client: "AsyncClient") -> None:
        yaml_content = (
            b"name: Test\nstart_date: 2026-04-06\nend_date: 2026-07-26\n"
            b"phases:\n"
            b"  - name: P1\n    type: base\n    start_week: 1\n    end_week: 6\n"
            b"  - name: P2\n    type: build\n    start_week: 5\n    end_week: 10\n"
        )
        response = await client.post(
            "/api/v1/training-plans/validate-yaml",
            files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is True
        assert len(body["warnings"]) > 0
