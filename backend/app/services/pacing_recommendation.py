"""Evidenzbasierte Pacing-Strategie-Empfehlung.

Ersetzt die vorherige KI-basierte Empfehlung durch deterministische Regeln.
Gleiche Inputs liefern immer die gleiche Empfehlung.

Quellen:
- Systematic Review Pacing Strategies in Marathons (2024, 39 Studien)
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11400961/
- Frontiers: Physiology & Psychology of Negative Splits (2025)
  https://doi.org/10.3389/fphys.2025.1639816
- Frontiers: Pacing Differences by Performance Level (2023)
  https://doi.org/10.3389/fpsyg.2023.1273451
- Abbiss & Laursen 2008: Pacing Strategies in Athletic Competition
  https://pubmed.ncbi.nlm.nih.gov/18278984/
"""

from __future__ import annotations

from typing import Literal

from app.models.pacing import (
    ElevationSegment,
    PacingRecommendationRequest,
    PacingRecommendationResponse,
)

# ---------------------------------------------------------------------------
# Schwellwerte (aus der Literatur)
# ---------------------------------------------------------------------------

# Hoehenprofil: ab 10m Gain pro km → huegelig (GAP-Forschung, LetsRun-Konsens)
HILLY_THRESHOLD_M_PER_KM = 10.0
# Hoehenprofil: ab 5m Gain pro km → wellig
ROLLING_THRESHOLD_M_PER_KM = 5.0

# Temperatur: ab 25°C → ~5% Performance-Loss, Thermoregulation kritisch
HEAT_THRESHOLD_CELSIUS = 25.0

# Distanz: unter 10km ist Negative-Split-Effekt minimal (Systematic Review 2024)
SHORT_DISTANCE_KM = 10.0
# Distanz: ab 21km wird Energiemanagement kritisch (Marathon-Review)
LONG_DISTANCE_KM = 21.0


# ---------------------------------------------------------------------------
# Rennstrecken-Lookup (bekannte Streckenprofile)
# ---------------------------------------------------------------------------

_KNOWN_RACES: dict[str, Literal["flat", "rolling", "hilly"]] = {
    # Flach
    "berlin": "flat",
    "hamburg": "flat",
    "amsterdam": "flat",
    "rotterdam": "flat",
    "valencia": "flat",
    "chicago": "flat",
    "london": "flat",
    "hannover": "flat",
    "dubai": "flat",
    "wien": "flat",
    "vienna": "flat",
    # Wellig
    "frankfurt": "rolling",
    "köln": "rolling",
    "koeln": "rolling",
    "münchen": "rolling",
    "muenchen": "rolling",
    "munich": "rolling",
    "paris": "rolling",
    "new york": "rolling",
    "stockholm": "rolling",
    "kopenhagen": "rolling",
    "copenhagen": "rolling",
    # Hügelig
    "zürich": "hilly",
    "zurich": "hilly",
    "jena": "hilly",
    "tübingen": "hilly",
    "tuebingen": "hilly",
    "boston": "hilly",
    "luzern": "hilly",
    "lucerne": "hilly",
    "san francisco": "hilly",
}


# ---------------------------------------------------------------------------
# Begründungstexte (evidenzbasiert, deutsch)
# ---------------------------------------------------------------------------

_REASON_HILLY = (
    "Effort-Based Pacing ist bei hügeligen Strecken die evidenzbasierte Wahl: "
    "Konstante Pace bei Steigungen treibt dich über die Laktatschwelle und "
    "entleert die Glykogenspeicher schneller. Stattdessen hältst du die "
    "Belastung konstant — bergauf langsamer, bergab schneller."
)

_REASON_BEGINNER = (
    "Gleichmäßiges Pacing ist für Einsteiger die sicherste Strategie: "
    "Die Forschung zeigt, dass erfahrenere Läufer gleichmäßiger pacen. "
    "Eine konstante Pace ist einfach umzusetzen und vermeidet das häufigste "
    "Problem — in der ersten Hälfte zu schnell zu starten."
)

_REASON_SHORT_DISTANCE = (
    "Bei Distanzen unter 10 km ist gleichmäßiges Pacing am effizientesten: "
    "Systematic Reviews zeigen, dass der Unterschied zwischen Even und "
    "Negative Splits bei kürzeren Distanzen minimal ist."
)

_REASON_HEAT = (
    "Bei hohen Temperaturen ist ein konservativer Start entscheidend: "
    "Die Thermoregulation ist in der ersten Rennhälfte am wichtigsten. "
    "Starte bewusst zurückhaltend und steigere dich, wenn sich der Körper "
    "stabilisiert hat."
)

_REASON_ADVANCED = (
    "Negative Splits nutzen deine Erfahrung optimal: Ein kontrollierter Start "
    "schont die Glykogenspeicher und ermöglicht ein starkes Finish. Die Forschung "
    "zeigt, dass Weltrekorde mit Even bis leicht negativem Pacing gelaufen werden."
)

_REASON_INTERMEDIATE_LONG = (
    "Ab Halbmarathon-Distanz wird das Energiemanagement kritisch: "
    "Ein konservativer Start mit Negative Splits verhindert das typische "
    "Einbrechen in der zweiten Hälfte."
)

_REASON_EVEN_DEFAULT = (
    "Gleichmäßiges Pacing ist die physiologisch optimale Strategie: "
    "Systematic Reviews zeigen, dass konstante Pace den Glykogenverbrauch "
    "und die Laktatakkumulation minimiert."
)


# ---------------------------------------------------------------------------
# Elevation-Klassifizierung
# ---------------------------------------------------------------------------


def _classify_elevation_from_segments(
    segments: list[ElevationSegment],
    distance_km: float,
) -> Literal["flat", "rolling", "hilly"]:
    """Klassifiziert das Höhenprofil aus GPX-Segmenten."""
    if not segments:
        return "flat"
    total_gain = sum(s.gain_m for s in segments)
    avg_gain = total_gain / distance_km if distance_km > 0 else 0.0
    if avg_gain >= HILLY_THRESHOLD_M_PER_KM:
        return "hilly"
    if avg_gain >= ROLLING_THRESHOLD_M_PER_KM:
        return "rolling"
    return "flat"


def _classify_elevation_from_race_name(
    race_name: str | None,
) -> Literal["flat", "rolling", "hilly"] | None:
    """Versucht das Höhenprofil aus dem Rennnamen abzuleiten."""
    if not race_name:
        return None
    name_lower = race_name.lower()
    for keyword, preset in _KNOWN_RACES.items():
        if keyword in name_lower:
            return preset
    return None


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------


StrategyType = Literal["even", "negative", "effort_based"]


def _determine_strategy(
    request: PacingRecommendationRequest,
    is_hilly: bool,
) -> tuple[StrategyType, str]:
    """Bestimmt Strategie und Begründung anhand des Entscheidungsbaums.

    Prioritätsreihenfolge:
    1. Höhenprofil hügelig → effort_based
    2. Anfänger → even
    3. Distanz < 10km → even
    4. Hitze ≥ 25°C (intermediate/advanced) → negative
    5. Advanced ≥ 10km oder Intermediate ≥ 21km → negative
    6. Default → even
    """
    if is_hilly:
        return "effort_based", _REASON_HILLY
    if request.experience_level == "beginner":
        return "even", _REASON_BEGINNER
    if request.distance_km < SHORT_DISTANCE_KM:
        return "even", _REASON_SHORT_DISTANCE
    if (
        request.temperature_celsius is not None
        and request.temperature_celsius >= HEAT_THRESHOLD_CELSIUS
    ):
        return "negative", _REASON_HEAT
    is_negative = request.experience_level == "advanced" or request.distance_km >= LONG_DISTANCE_KM
    if is_negative:
        reason = (
            _REASON_ADVANCED
            if request.experience_level == "advanced"
            else _REASON_INTERMEDIATE_LONG
        )
        return "negative", reason
    return "even", _REASON_EVEN_DEFAULT


def recommend_pacing(
    request: PacingRecommendationRequest,
) -> PacingRecommendationResponse:
    """Gibt eine deterministische, evidenzbasierte Pacing-Empfehlung zurück."""
    # Elevation bestimmen (Priorität: GPX > manuelles Preset > Rennname)
    elevation: Literal["flat", "rolling", "hilly"] | None
    if request.elevation_segments:
        elevation = _classify_elevation_from_segments(
            request.elevation_segments, request.distance_km
        )
    elif request.elevation_preset:
        elevation = request.elevation_preset
    else:
        elevation = _classify_elevation_from_race_name(request.race_name)

    strategy, reasoning = _determine_strategy(request, is_hilly=elevation == "hilly")

    return PacingRecommendationResponse(
        strategy=strategy,
        elevation_preset=elevation,
        reasoning=reasoning,
    )
