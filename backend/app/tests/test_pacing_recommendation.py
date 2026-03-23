"""Tests fuer die evidenzbasierte Pacing-Empfehlung (deterministisch)."""

from app.services.pacing_recommendation import (
    determine_elevation_preset,
    determine_strategy,
)

# ---------------------------------------------------------------------------
# Elevation Preset (Rennen-Lookup)
# ---------------------------------------------------------------------------


class TestDetermineElevationPreset:
    """Tests fuer die Rennen → Hoehenprofil Zuordnung."""

    def test_known_flat_race(self) -> None:
        assert determine_elevation_preset("Berlin Halbmarathon") == "flat"

    def test_known_rolling_race(self) -> None:
        assert determine_elevation_preset("Frankfurt Marathon") == "rolling"

    def test_known_hilly_race(self) -> None:
        assert determine_elevation_preset("Zürich Marathon") == "hilly"

    def test_case_insensitive(self) -> None:
        assert determine_elevation_preset("BERLIN marathon") == "flat"
        assert determine_elevation_preset("zürich") == "hilly"

    def test_unknown_race_defaults_to_flat(self) -> None:
        assert determine_elevation_preset("Kleinstadtlauf Hintertupfingen") == "flat"

    def test_none_defaults_to_flat(self) -> None:
        assert determine_elevation_preset(None) == "flat"

    def test_partial_match(self) -> None:
        """Auch Teilstring-Matches funktionieren."""
        assert determine_elevation_preset("Haspa Hamburg Marathon") == "flat"
        assert determine_elevation_preset("Mainova Frankfurt Marathon") == "rolling"

    def test_umlaut_variants(self) -> None:
        """Sowohl Umlaut als auch ASCII-Variante matchen."""
        assert determine_elevation_preset("Köln Marathon") == "rolling"
        assert determine_elevation_preset("Koeln Marathon") == "rolling"
        assert determine_elevation_preset("Düsseldorf Marathon") == "flat"
        assert determine_elevation_preset("Duesseldorf Marathon") == "flat"


# ---------------------------------------------------------------------------
# Strategie-Entscheidungsbaum
# ---------------------------------------------------------------------------


class TestDetermineStrategy:
    """Tests fuer den evidenzbasierten Entscheidungsbaum.

    Nur ein Faktor: Hoehenprofil.
    - Flach → even (energetisch optimal, Abbiss & Laursen 2005)
    - Wellig/Huegelig → effort_based (konstanter Effort)
    """

    def test_hilly_effort_based(self) -> None:
        assert determine_strategy("hilly") == "effort_based"

    def test_rolling_effort_based(self) -> None:
        assert determine_strategy("rolling") == "effort_based"

    def test_flat_even(self) -> None:
        assert determine_strategy("flat") == "even"

    def test_deterministic(self) -> None:
        """Gleiche Inputs muessen immer das gleiche Ergebnis liefern."""
        results = [determine_strategy("flat") for _ in range(100)]
        assert all(r == results[0] for r in results)

    # Integration: Rennname → Preset → Strategie (End-to-End)

    def test_berlin_hm_always_even(self) -> None:
        """Berlin HM ist immer even — kein Muenzwurf."""
        preset = determine_elevation_preset("Berlin Halbmarathon")
        assert determine_strategy(preset) == "even"

    def test_zuerich_marathon_always_effort_based(self) -> None:
        preset = determine_elevation_preset("Zürich Marathon")
        assert determine_strategy(preset) == "effort_based"

    def test_frankfurt_hm_always_effort_based(self) -> None:
        """Frankfurt (wellig) ist immer effort_based."""
        preset = determine_elevation_preset("Frankfurt Halbmarathon")
        assert determine_strategy(preset) == "effort_based"

    def test_unknown_race_always_even(self) -> None:
        """Unbekanntes Rennen → flat → even."""
        preset = determine_elevation_preset("Dorflauf Hintertupfingen")
        assert determine_strategy(preset) == "even"
