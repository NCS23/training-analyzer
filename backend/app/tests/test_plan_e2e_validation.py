"""End-to-End Validierung: Generierter Plan ist trainingswissenschaftlich sinnvoll.

Generiert einen kompletten Plan und prüft die resultierenden Wochenpläne
auf Plausibilität — nicht nur isolierte Service-Tests.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock

from app.services.plan_generator import generate_weekly_plans


def _make_plan(start: str, end: str) -> MagicMock:
    plan = MagicMock()
    plan.start_date = date.fromisoformat(start)
    plan.end_date = date.fromisoformat(end)
    return plan


def _make_phase(
    plan_id: int,
    phase_type: str,
    start_week: int,
    end_week: int,
    vol_min: float,
    vol_max: float,
) -> MagicMock:
    import json

    phase = MagicMock()
    phase.training_plan_id = plan_id
    phase.phase_type = phase_type
    phase.start_week = start_week
    phase.end_week = end_week
    phase.target_metrics_json = json.dumps(
        {
            "weekly_volume_min": vol_min,
            "weekly_volume_max": vol_max,
            "quality_sessions_per_week": 1 if phase_type in ("build", "peak") else 0,
            "strength_sessions_per_week": 2 if phase_type == "base" else 1,
        }
    )
    phase.weekly_template_json = None
    phase.weekly_templates_json = None
    return phase


def _make_goal(distance_km: float, time_sec: int, race_date: str) -> MagicMock:
    goal = MagicMock()
    goal.distance_km = distance_km
    goal.target_time_seconds = time_sec
    goal.race_date = date.fromisoformat(race_date)
    return goal


class TestPeakVolumeEstimation:
    """Die _estimate_peak_volume Funktion erzeugt sinnvolle Werte."""

    def test_hm_peak_at_least_55km(self) -> None:
        """HM Sub-1:50 mit 28 Wochen → Peak mindestens 55 km."""
        from app.services.chat_tool_handlers import _estimate_peak_volume

        peak = _estimate_peak_volume(21.0975, 20.0, weeks=28)
        assert peak >= 55.0, f"HM Peak {peak:.0f} km zu niedrig (soll ≥55)"

    def test_marathon_peak_at_least_65km(self) -> None:
        """Marathon mit 20 Wochen → Peak mindestens 65 km."""
        from app.services.chat_tool_handlers import _estimate_peak_volume

        peak = _estimate_peak_volume(42.195, 30.0, weeks=20)
        assert peak >= 65.0, f"Marathon Peak {peak:.0f} km zu niedrig (soll ≥65)"

    def test_short_plan_lower_peak(self) -> None:
        """Kurzer Plan (10 Wochen) hat niedrigeres Peak."""
        from app.services.chat_tool_handlers import _estimate_peak_volume

        short = _estimate_peak_volume(21.0975, 20.0, weeks=10)
        long = _estimate_peak_volume(21.0975, 20.0, weeks=28)
        assert short < long

    def test_higher_current_km_higher_peak(self) -> None:
        """Mehr aktuelles Volumen → höheres Peak."""
        from app.services.chat_tool_handlers import _estimate_peak_volume

        low = _estimate_peak_volume(21.0975, 15.0, weeks=20)
        high = _estimate_peak_volume(21.0975, 40.0, weeks=20)
        assert high >= low


class TestGeneratedPlanE2E:
    """End-to-End: Generierter HM Sub-1:50 Plan ist brauchbar."""

    def _generate_hm_plan(self) -> list:
        """Generiert Plan mit realistischen Phasen-Metriken aus _estimate_peak_volume."""
        from app.services.chat_tool_handlers import _VOLUME_FACTORS, _estimate_peak_volume

        plan = _make_plan("2026-04-06", "2026-10-04")  # 26 Wochen
        goal = _make_goal(21.0975, 6600, "2026-10-04")  # 1:50:00

        # Echte Peak-Volumen-Berechnung wie im Produktivcode
        current_km = 20.0
        peak_vol = _estimate_peak_volume(21.0975, current_km, weeks=26)

        phases: list[Any] = [
            _make_phase(
                1,
                "base",
                1,
                10,
                peak_vol * _VOLUME_FACTORS["base"] * 0.9,
                peak_vol * _VOLUME_FACTORS["base"] * 1.1,
            ),
            _make_phase(
                1,
                "build",
                11,
                18,
                peak_vol * _VOLUME_FACTORS["build"] * 0.9,
                peak_vol * _VOLUME_FACTORS["build"] * 1.1,
            ),
            _make_phase(1, "peak", 19, 24, peak_vol * 0.9, peak_vol * 1.1),
            _make_phase(
                1,
                "taper",
                25,
                26,
                peak_vol * _VOLUME_FACTORS["taper"] * 0.9,
                peak_vol * _VOLUME_FACTORS["taper"] * 1.1,
            ),
        ]
        from app.services.vdot_calculator import estimate_vdot

        vdot = estimate_vdot(21.0975, 6600)

        return generate_weekly_plans(
            plan=plan,
            phases=phases,
            rest_days=[0, 6],
            goal=goal,
            vdot=vdot,
        )

    def test_all_running_sessions_have_paces(self) -> None:
        """Jede Running-Session muss Paces haben (nicht None)."""
        weekly_data = self._generate_hm_plan()
        sessions_without_paces = []
        for week_start, entries in weekly_data:
            for entry in entries:
                for sess in entry.sessions:
                    if sess.training_type != "running" or not sess.run_details:
                        continue
                    if not sess.run_details.segments:
                        continue
                    # Mindestens ein Segment muss Paces haben
                    has_pace = any(s.target_pace_min is not None for s in sess.run_details.segments)
                    if not has_pace:
                        sessions_without_paces.append(f"W{week_start}: {sess.run_details.run_type}")

        assert len(sessions_without_paces) == 0, (
            f"{len(sessions_without_paces)} Sessions ohne Paces: {sessions_without_paces[:10]}"
        )

    def test_peak_long_run_at_least_75_minutes(self) -> None:
        """Long Runs in Peak-Phase müssen mindestens 75 Min sein für HM."""
        weekly_data = self._generate_hm_plan()
        # Peak ist Woche 19-24 (Index 18-23)
        peak_long_run_durs = []
        for i, (_, entries) in enumerate(weekly_data):
            week_num = i + 1
            if 19 <= week_num <= 24:
                for entry in entries:
                    for sess in entry.sessions:
                        if (
                            sess.training_type == "running"
                            and sess.run_details
                            and sess.run_details.run_type == "long_run"
                        ):
                            dur = sess.run_details.target_duration_minutes or 0
                            peak_long_run_durs.append(dur)

        assert len(peak_long_run_durs) > 0, "Peak-Phase hat keine Long Runs"
        max_lr = max(peak_long_run_durs)
        assert max_lr >= 75, (
            f"Längster Peak Long Run nur {max_lr} Min — für HM sollten es ≥75 Min sein"
        )

    def test_total_peak_volume_adequate(self) -> None:
        """Peak-Wochen sollten ≥250 Min Gesamtvolumen haben."""
        weekly_data = self._generate_hm_plan()
        peak_totals = []
        for i, (_, entries) in enumerate(weekly_data):
            week_num = i + 1
            if 19 <= week_num <= 24:
                total = 0
                for entry in entries:
                    for sess in entry.sessions:
                        if sess.training_type == "running" and sess.run_details:
                            total += sess.run_details.target_duration_minutes or 0
                peak_totals.append(total)

        assert len(peak_totals) > 0
        max_total = max(peak_totals)
        assert max_total >= 250, f"Peak-Volumen max {max_total} Min — sollte ≥250 Min für HM sein"

    def test_easy_pace_slower_than_race_pace(self) -> None:
        """Easy-Pace muss langsamer als Race-Pace sein (5:13/km für HM 1:50)."""
        weekly_data = self._generate_hm_plan()
        race_pace_sec = 313  # 5:13/km
        for _, entries in weekly_data:
            for entry in entries:
                for sess in entry.sessions:
                    if (
                        sess.training_type == "running"
                        and sess.run_details
                        and sess.run_details.run_type == "easy"
                        and sess.run_details.segments
                    ):
                        seg = sess.run_details.segments[0]
                        if seg.target_pace_min:
                            m, s = seg.target_pace_min.split(":")
                            pace_sec = int(m) * 60 + int(s)
                            assert pace_sec > race_pace_sec, (
                                f"Easy pace {seg.target_pace_min} schneller als Race pace 5:13"
                            )

    def test_taper_volume_less_than_peak(self) -> None:
        """Taper-Wochen haben weniger Volumen als Peak-Wochen."""
        weekly_data = self._generate_hm_plan()
        peak_max = 0
        taper_totals = []
        for i, (_, entries) in enumerate(weekly_data):
            week_num = i + 1
            total = 0
            for entry in entries:
                for sess in entry.sessions:
                    if sess.training_type == "running" and sess.run_details:
                        if sess.run_details.run_type == "race":
                            continue
                        total += sess.run_details.target_duration_minutes or 0
            if 19 <= week_num <= 24:
                peak_max = max(peak_max, total)
            if 25 <= week_num <= 26:
                taper_totals.append(total)

        assert len(taper_totals) > 0
        for t in taper_totals:
            assert t < peak_max, f"Taper {t} Min sollte < Peak max {peak_max} Min"
