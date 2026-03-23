"""Tests fuer die evidenzbasierte Pacing-Strategie-Empfehlung.

Jeder Pfad im Entscheidungsbaum wird deterministisch getestet.
"""

from __future__ import annotations

import pytest

from app.models.pacing import (
    ElevationSegment,
    PacingRecommendationRequest,
)
from app.services.pacing_recommendation import (
    HEAT_THRESHOLD_CELSIUS,
    HILLY_THRESHOLD_M_PER_KM,
    LONG_DISTANCE_KM,
    ROLLING_THRESHOLD_M_PER_KM,
    SHORT_DISTANCE_KM,
    recommend_pacing,
)


def _req(
    *,
    distance_km: float = 21.1,
    target_time_seconds: int = 6600,
    experience_level: str = "intermediate",
    race_name: str | None = None,
    temperature_celsius: float | None = None,
    elevation_preset: str | None = None,
    elevation_segments: list[ElevationSegment] | None = None,
) -> PacingRecommendationRequest:
    """Erzeugt einen PacingRecommendationRequest mit sinnvollen Defaults."""
    return PacingRecommendationRequest(
        distance_km=distance_km,
        target_time_seconds=target_time_seconds,
        experience_level=experience_level,  # type: ignore[arg-type]
        race_name=race_name,
        temperature_celsius=temperature_celsius,
        elevation_preset=elevation_preset,  # type: ignore[arg-type]
        elevation_segments=elevation_segments,
    )


# -----------------------------------------------------------------------
# Determinismus: Gleicher Input → gleicher Output
# -----------------------------------------------------------------------


class TestDeterminism:
    """Gleiche Inputs muessen immer die gleiche Empfehlung liefern."""

    def test_same_input_same_output(self) -> None:
        req = _req(distance_km=21.1, experience_level="advanced")
        results = [recommend_pacing(req) for _ in range(50)]
        strategies = {r.strategy for r in results}
        assert len(strategies) == 1


# -----------------------------------------------------------------------
# Faktor 1: Höhenprofil
# -----------------------------------------------------------------------


class TestElevation:
    """Hügeliges Höhenprofil → effort_based, unabhaengig von Erfahrung."""

    def test_hilly_race_name_returns_effort_based(self) -> None:
        result = recommend_pacing(_req(race_name="Zürich Marathon", experience_level="beginner"))
        assert result.strategy == "effort_based"
        assert result.elevation_preset == "hilly"

    def test_hilly_gpx_returns_effort_based(self) -> None:
        segments = [ElevationSegment(km=i, gain_m=15.0, loss_m=5.0) for i in range(1, 22)]
        result = recommend_pacing(_req(elevation_segments=segments))
        assert result.strategy == "effort_based"
        assert result.elevation_preset == "hilly"

    def test_gpx_overrides_race_name(self) -> None:
        """GPX-Daten haben Vorrang vor Rennname-Lookup."""
        flat_segments = [ElevationSegment(km=i, gain_m=1.0, loss_m=1.0) for i in range(1, 22)]
        result = recommend_pacing(
            _req(race_name="Zürich Marathon", elevation_segments=flat_segments)
        )
        # GPX sagt flach → nicht effort_based, obwohl Zürich hügelig ist
        assert result.strategy != "effort_based"

    def test_rolling_race_name_sets_preset(self) -> None:
        result = recommend_pacing(_req(race_name="Frankfurt Marathon", experience_level="advanced"))
        assert result.elevation_preset == "rolling"
        assert result.strategy == "negative"  # Advanced + ≥10km → negative

    def test_flat_race_name_sets_preset(self) -> None:
        result = recommend_pacing(
            _req(race_name="Berlin Halbmarathon", experience_level="advanced")
        )
        assert result.elevation_preset == "flat"

    def test_unknown_race_returns_no_preset(self) -> None:
        result = recommend_pacing(_req(race_name="Dorflauf Hintertupfingen"))
        assert result.elevation_preset is None

    def test_no_race_name_returns_no_preset(self) -> None:
        result = recommend_pacing(_req(race_name=None))
        assert result.elevation_preset is None

    def test_hilly_overrides_advanced_negative(self) -> None:
        """Höhenprofil hat höchste Priorität — auch für erfahrene Läufer."""
        result = recommend_pacing(_req(race_name="Boston Marathon", experience_level="advanced"))
        assert result.strategy == "effort_based"

    def test_gpx_rolling_threshold(self) -> None:
        """Ø 5-10m/km → rolling, nicht hügelig."""
        segments = [ElevationSegment(km=i, gain_m=7.0, loss_m=3.0) for i in range(1, 22)]
        result = recommend_pacing(_req(elevation_segments=segments, experience_level="advanced"))
        assert result.elevation_preset == "rolling"
        assert result.strategy == "negative"  # rolling + advanced → negative

    def test_gpx_flat_threshold(self) -> None:
        """Ø <5m/km → flat."""
        segments = [ElevationSegment(km=i, gain_m=2.0, loss_m=2.0) for i in range(1, 22)]
        result = recommend_pacing(
            _req(elevation_segments=segments, experience_level="intermediate")
        )
        assert result.elevation_preset == "flat"

    def test_manual_preset_hilly_returns_effort_based(self) -> None:
        """Manuell gewähltes Preset 'hilly' → effort_based."""
        result = recommend_pacing(_req(elevation_preset="hilly", experience_level="advanced"))
        assert result.strategy == "effort_based"
        assert result.elevation_preset == "hilly"

    def test_manual_preset_flat_no_effort_based(self) -> None:
        """Manuell gewähltes Preset 'flat' → nicht effort_based."""
        result = recommend_pacing(_req(elevation_preset="flat", experience_level="advanced"))
        assert result.strategy == "negative"

    def test_gpx_overrides_manual_preset(self) -> None:
        """GPX hat Vorrang vor manuellem Preset."""
        flat_segments = [ElevationSegment(km=i, gain_m=1.0, loss_m=1.0) for i in range(1, 22)]
        result = recommend_pacing(_req(elevation_preset="hilly", elevation_segments=flat_segments))
        # GPX sagt flach → nicht effort_based, obwohl Preset hilly
        assert result.strategy != "effort_based"
        assert result.elevation_preset == "flat"

    def test_preset_overrides_race_name(self) -> None:
        """Manuelles Preset hat Vorrang vor Rennname."""
        result = recommend_pacing(
            _req(race_name="Berlin", elevation_preset="hilly", experience_level="beginner")
        )
        # Preset sagt hilly → effort_based, obwohl Berlin=flat
        assert result.strategy == "effort_based"
        assert result.elevation_preset == "hilly"


# -----------------------------------------------------------------------
# Faktor 2: Anfänger
# -----------------------------------------------------------------------


class TestBeginner:
    """Anfänger → even, immer (außer hügelig)."""

    def test_beginner_flat_returns_even(self) -> None:
        result = recommend_pacing(_req(experience_level="beginner", race_name="Berlin"))
        assert result.strategy == "even"

    def test_beginner_heat_still_returns_even(self) -> None:
        """Auch bei Hitze: Anfänger sollen nicht mit Negative Splits experimentieren."""
        result = recommend_pacing(
            _req(experience_level="beginner", temperature_celsius=30.0, race_name="Berlin")
        )
        assert result.strategy == "even"

    def test_beginner_marathon_returns_even(self) -> None:
        result = recommend_pacing(
            _req(experience_level="beginner", distance_km=42.2, target_time_seconds=18000)
        )
        assert result.strategy == "even"


# -----------------------------------------------------------------------
# Faktor 3: Kurze Distanz
# -----------------------------------------------------------------------


class TestShortDistance:
    """Distanz < 10km → even (zu kurz fuer Negative-Split-Effekt)."""

    def test_5k_advanced_returns_even(self) -> None:
        result = recommend_pacing(
            _req(distance_km=5.0, target_time_seconds=1200, experience_level="advanced")
        )
        assert result.strategy == "even"

    def test_9k_intermediate_returns_even(self) -> None:
        result = recommend_pacing(
            _req(distance_km=9.0, target_time_seconds=2700, experience_level="intermediate")
        )
        assert result.strategy == "even"

    def test_10k_advanced_returns_negative(self) -> None:
        """Exakt 10km ist NICHT kurz → Erfahrungsregeln greifen."""
        result = recommend_pacing(
            _req(distance_km=10.0, target_time_seconds=3000, experience_level="advanced")
        )
        assert result.strategy == "negative"


# -----------------------------------------------------------------------
# Faktor 4: Hitze
# -----------------------------------------------------------------------


class TestHeat:
    """Temperatur ≥ 25°C → negative (für intermediate/advanced)."""

    def test_heat_intermediate_returns_negative(self) -> None:
        result = recommend_pacing(
            _req(temperature_celsius=28.0, experience_level="intermediate", distance_km=15.0)
        )
        assert result.strategy == "negative"

    def test_heat_advanced_returns_negative(self) -> None:
        result = recommend_pacing(_req(temperature_celsius=30.0, experience_level="advanced"))
        assert result.strategy == "negative"

    def test_no_heat_intermediate_15k_returns_even(self) -> None:
        """Ohne Hitze: intermediate + 15km → even."""
        result = recommend_pacing(
            _req(temperature_celsius=18.0, experience_level="intermediate", distance_km=15.0)
        )
        assert result.strategy == "even"

    def test_exactly_25c_triggers_heat(self) -> None:
        """Exakt 25°C ist >= Schwellwert → negative."""
        result = recommend_pacing(
            _req(temperature_celsius=25.0, experience_level="intermediate", distance_km=15.0)
        )
        assert result.strategy == "negative"

    def test_24c_no_heat(self) -> None:
        """24°C ist unter Schwellwert → kein Heat-Override."""
        result = recommend_pacing(
            _req(temperature_celsius=24.0, experience_level="intermediate", distance_km=15.0)
        )
        assert result.strategy == "even"


# -----------------------------------------------------------------------
# Faktor 5: Erfahrung × Distanz
# -----------------------------------------------------------------------


class TestExperienceDistance:
    """Kombination aus Erfahrung und Distanz."""

    def test_advanced_half_marathon_returns_negative(self) -> None:
        result = recommend_pacing(_req(experience_level="advanced", distance_km=21.1))
        assert result.strategy == "negative"

    def test_advanced_marathon_returns_negative(self) -> None:
        result = recommend_pacing(
            _req(experience_level="advanced", distance_km=42.2, target_time_seconds=14400)
        )
        assert result.strategy == "negative"

    def test_intermediate_half_marathon_returns_negative(self) -> None:
        """Intermediate + ≥21km → negative."""
        result = recommend_pacing(_req(experience_level="intermediate", distance_km=21.1))
        assert result.strategy == "negative"

    def test_intermediate_15k_returns_even(self) -> None:
        """Intermediate + 15km (< 21km) → even."""
        result = recommend_pacing(_req(experience_level="intermediate", distance_km=15.0))
        assert result.strategy == "even"

    def test_intermediate_10k_returns_even(self) -> None:
        result = recommend_pacing(
            _req(experience_level="intermediate", distance_km=10.0, target_time_seconds=3000)
        )
        assert result.strategy == "even"


# -----------------------------------------------------------------------
# Schwellwert-Konsistenz
# -----------------------------------------------------------------------


class TestThresholds:
    """Schwellwerte muessen mit den exportierten Konstanten uebereinstimmen."""

    def test_hilly_threshold(self) -> None:
        assert HILLY_THRESHOLD_M_PER_KM == 10.0

    def test_rolling_threshold(self) -> None:
        assert ROLLING_THRESHOLD_M_PER_KM == 5.0

    def test_heat_threshold(self) -> None:
        assert HEAT_THRESHOLD_CELSIUS == 25.0

    def test_short_distance_threshold(self) -> None:
        assert SHORT_DISTANCE_KM == 10.0

    def test_long_distance_threshold(self) -> None:
        assert LONG_DISTANCE_KM == 21.0


# -----------------------------------------------------------------------
# Begründungstexte
# -----------------------------------------------------------------------


class TestReasoning:
    """Jede Empfehlung muss eine nicht-leere Begründung enthalten."""

    @pytest.mark.parametrize(
        ("kwargs", "expected_strategy"),
        [
            ({"race_name": "Zürich", "experience_level": "beginner"}, "effort_based"),
            ({"experience_level": "beginner"}, "even"),
            (
                {"distance_km": 5.0, "target_time_seconds": 1500, "experience_level": "advanced"},
                "even",
            ),
            ({"temperature_celsius": 30.0, "experience_level": "intermediate"}, "negative"),
            ({"experience_level": "advanced"}, "negative"),
            (
                {
                    "experience_level": "intermediate",
                    "distance_km": 42.2,
                    "target_time_seconds": 14400,
                },
                "negative",
            ),
            (
                {
                    "experience_level": "intermediate",
                    "distance_km": 15.0,
                    "target_time_seconds": 4500,
                },
                "even",
            ),
        ],
    )
    def test_reasoning_not_empty(self, kwargs: dict, expected_strategy: str) -> None:  # type: ignore[type-arg]
        result = recommend_pacing(_req(**kwargs))
        assert result.strategy == expected_strategy
        assert len(result.reasoning) > 20


# -----------------------------------------------------------------------
# Race-Name Matching
# -----------------------------------------------------------------------


class TestRaceNameLookup:
    """Case-insensitive Substring-Match auf Rennnamen."""

    def test_case_insensitive(self) -> None:
        result = recommend_pacing(_req(race_name="BERLIN marathon", experience_level="advanced"))
        assert result.elevation_preset == "flat"

    def test_substring_match(self) -> None:
        result = recommend_pacing(
            _req(race_name="35. Hamburg Marathon 2026", experience_level="advanced")
        )
        assert result.elevation_preset == "flat"

    def test_umlaut_match(self) -> None:
        result = recommend_pacing(_req(race_name="Zürich", experience_level="advanced"))
        assert result.elevation_preset == "hilly"

    def test_alternate_spelling(self) -> None:
        result = recommend_pacing(_req(race_name="Muenchen Marathon", experience_level="advanced"))
        assert result.elevation_preset == "rolling"
