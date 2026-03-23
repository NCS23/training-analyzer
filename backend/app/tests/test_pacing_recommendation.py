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
    """Tests fuer den evidenzbasierten Entscheidungsbaum."""

    # Schritt 1: Hoehenprofil (dominanter Faktor)

    def test_hilly_always_effort_based(self) -> None:
        """Huegelig → effort_based, unabhaengig von Distanz/Level."""
        assert determine_strategy(21.1, "hilly", "beginner", None) == "effort_based"
        assert determine_strategy(42.195, "hilly", "advanced", None) == "effort_based"
        assert determine_strategy(10.0, "hilly", None, None) == "effort_based"

    def test_rolling_always_effort_based(self) -> None:
        """Wellig → effort_based."""
        assert determine_strategy(21.1, "rolling", "advanced", None) == "effort_based"
        assert determine_strategy(5.0, "rolling", "beginner", None) == "effort_based"

    # Schritt 2: Distanz (bei flacher Strecke)

    def test_5k_always_even(self) -> None:
        """5K → even (zu kurz fuer Negative-Split-Vorteil)."""
        assert determine_strategy(5.0, "flat", "advanced", None) == "even"

    def test_10k_always_even(self) -> None:
        """10K → even."""
        assert determine_strategy(10.0, "flat", "advanced", None) == "even"

    def test_marathon_always_even(self) -> None:
        """Marathon → even (Glykogen-Management)."""
        assert determine_strategy(42.195, "flat", "advanced", None) == "even"

    def test_ultra_always_even(self) -> None:
        """Ultra → even (Energie-Management)."""
        assert determine_strategy(50.0, "flat", "advanced", None) == "even"
        assert determine_strategy(100.0, "flat", "advanced", None) == "even"

    # Schritt 3: HM-spezifisch

    def test_hm_beginner_even(self) -> None:
        """HM + Anfaenger → even (negative Splits schwer umsetzbar)."""
        assert determine_strategy(21.1, "flat", "beginner", None) == "even"

    def test_hm_no_level_even(self) -> None:
        """HM + kein Level → even (sicherster Default)."""
        assert determine_strategy(21.1, "flat", None, None) == "even"

    def test_hm_intermediate_no_heat_negative(self) -> None:
        """HM + Fortgeschritten + keine Hitze → negative."""
        assert determine_strategy(21.1, "flat", "intermediate", None) == "negative"

    def test_hm_advanced_no_heat_negative(self) -> None:
        """HM + Erfahren + keine Hitze → negative."""
        assert determine_strategy(21.1, "flat", "advanced", None) == "negative"

    def test_hm_advanced_cool_negative(self) -> None:
        """HM + Erfahren + kuehle Bedingungen → negative."""
        assert determine_strategy(21.1, "flat", "advanced", 12.0) == "negative"

    def test_hm_heat_forces_even(self) -> None:
        """HM + Hitze > 20°C → even (auch fuer Erfahrene)."""
        assert determine_strategy(21.1, "flat", "advanced", 25.0) == "even"
        assert determine_strategy(21.1, "flat", "intermediate", 21.0) == "even"

    def test_hm_exactly_20_not_heat(self) -> None:
        """Genau 20°C ist noch keine Hitze (Schwelle ist >20°C)."""
        assert determine_strategy(21.1, "flat", "advanced", 20.0) == "negative"

    # Determinismus-Check

    def test_deterministic_same_input_same_output(self) -> None:
        """Gleiche Inputs muessen immer das gleiche Ergebnis liefern."""
        results = [determine_strategy(21.1, "flat", "advanced", 15.0) for _ in range(100)]
        assert all(r == results[0] for r in results)

    # Grenzfaelle Distanz

    def test_15km_counts_as_hm(self) -> None:
        """15 km liegt im HM-Bereich."""
        assert determine_strategy(15.0, "flat", "advanced", None) == "negative"

    def test_25km_counts_as_hm(self) -> None:
        """25 km liegt noch im HM-Bereich."""
        assert determine_strategy(25.0, "flat", "advanced", None) == "negative"

    def test_14km_not_hm(self) -> None:
        """14 km ist kein HM → even."""
        assert determine_strategy(14.0, "flat", "advanced", None) == "even"

    def test_26km_not_hm(self) -> None:
        """26 km ist kein HM mehr → even."""
        assert determine_strategy(26.0, "flat", "advanced", None) == "even"
