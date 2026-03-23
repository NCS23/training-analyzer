"""Evidenzbasierte Pacing-Strategie-Empfehlung.

Deterministische Regellogik fuer strategy + elevation_preset,
KI (Claude) nur fuer den Begruendungstext (reasoning).

Sportwissenschaftliche Grundlage:
- Abbiss & Laursen (2005/2008): Even Pacing energetisch optimal
- Hanley (2016): WR-Analysen zeigen even/minimal negative Splits
- El Helou et al. (2012): Hitze-Einfluss auf optimale Strategie
"""

from __future__ import annotations

import json
import logging
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.ai.ai_service import ai_service
from app.models.pacing import PacingRecommendationRequest, PacingRecommendationResponse
from app.services.ai_log_service import AICallData, log_ai_call

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bekannte Rennen → Elevation Preset
# ---------------------------------------------------------------------------

_KNOWN_RACES: dict[str, ElevationPresetType] = {
    # Flach
    "berlin": "flat",
    "hamburg": "flat",
    "amsterdam": "flat",
    "rotterdam": "flat",
    "chicago": "flat",
    "london": "flat",
    "hannover": "flat",
    "düsseldorf": "flat",
    "duesseldorf": "flat",
    "kopenhagen": "flat",
    "copenhagen": "flat",
    "valencia": "flat",
    "wien": "flat",
    "vienna": "flat",
    "münchen": "flat",
    "muenchen": "flat",
    "munich": "flat",
    # Wellig
    "frankfurt": "rolling",
    "köln": "rolling",
    "koeln": "rolling",
    "new york": "rolling",
    "boston": "rolling",
    "dresden": "rolling",
    "mainz": "rolling",
    "freiburg": "rolling",
    "paris": "rolling",
    "tokyo": "rolling",
    # Hügelig
    "zürich": "hilly",
    "zuerich": "hilly",
    "zurich": "hilly",
    "jena": "hilly",
    "Stuttgart": "hilly",
    "stuttgart": "hilly",
    "heidelberg": "hilly",
    "innsbruck": "hilly",
    "salzburg": "hilly",
    "luzern": "hilly",
    "trail": "hilly",
}

# ---------------------------------------------------------------------------
# Schwellenwerte
# ---------------------------------------------------------------------------

_HEAT_THRESHOLD_C = 20.0
_HM_DISTANCE_RANGE = (15.0, 25.0)
_MARATHON_DISTANCE_RANGE = (35.0, 45.0)


# ---------------------------------------------------------------------------
# Deterministische Strategieauswahl
# ---------------------------------------------------------------------------


StrategyType = Literal["even", "negative", "effort_based"]
ElevationPresetType = Literal["flat", "rolling", "hilly"]


def determine_elevation_preset(race_name: str | None) -> ElevationPresetType:
    """Bestimmt das Hoehenprofil anhand des Rennnamens.

    Durchsucht den Rennnamen nach bekannten Strecken.
    Fallback: 'flat' (sicherste Annahme).
    """
    if not race_name:
        return "flat"

    name_lower = race_name.lower()
    for keyword, preset in _KNOWN_RACES.items():
        if keyword in name_lower:
            return preset

    return "flat"


def determine_strategy(
    distance_km: float,
    elevation_preset: str,
    experience_level: str | None,
    temperature_celsius: float | None,
) -> StrategyType:
    """Evidenzbasierter Entscheidungsbaum fuer die Pacing-Strategie.

    Schritt 1: Hoehenprofil (dominanter Faktor)
      - hilly/rolling → effort_based (konstanter Effort bei variablem Terrain)

    Schritt 2: Distanz
      - 5K-10K  → even (zu kurz fuer Negative-Split-Vorteil)
      - Marathon → even (Glykogen-Management, Einbruch-Praevention)
      - Ultra    → even (Energie-Management noch kritischer)
      - HM      → weiter zu Schritt 3

    Schritt 3: HM-spezifisch (einzige Distanz wo negativ sinnvoll)
      - Hitze >20°C        → even (konservativer Start bei Hitze Pflicht)
      - Beginner           → even (negative Splits schwer umsetzbar)
      - Intermediate/Advanced + gute Bedingungen → negative
      - Default            → even
    """
    # Schritt 1: Hoehenprofil
    if elevation_preset in ("hilly", "rolling"):
        return "effort_based"

    # Schritt 2: Distanz
    is_hm = _HM_DISTANCE_RANGE[0] <= distance_km <= _HM_DISTANCE_RANGE[1]
    if not is_hm:
        return "even"

    # Schritt 3: HM-spezifisch
    if temperature_celsius is not None and temperature_celsius > _HEAT_THRESHOLD_C:
        return "even"

    if experience_level is None or experience_level == "beginner":
        return "even"

    # Intermediate oder Advanced + HM + keine Hitze
    return "negative"


# ---------------------------------------------------------------------------
# KI-Reasoning (nur Begruendungstext)
# ---------------------------------------------------------------------------

_REASONING_SYSTEM_PROMPT = """\
Du bist ein erfahrener Lauftrainer und Sportwissenschaftler.
Die Pacing-Strategie wurde bereits festgelegt. Deine Aufgabe ist es,
die Entscheidung in 2-3 Saetzen auf Deutsch zu begruenden.

Antworte NUR mit einem JSON-Objekt:
{"reasoning": "<2-3 Saetze Begruendung>"}

Begruende sportwissenschaftlich fundiert:
- Warum diese Strategie fuer diese Distanz/Strecke/Bedingungen optimal ist
- Beziehe dich auf die konkreten Renn- und Athletendaten
- Vermeide generische Floskeln
"""


async def _get_ai_reasoning(
    request: PacingRecommendationRequest,
    strategy: str,
    elevation_preset: str,
    api_key: str,
    db: AsyncSession,
) -> str:
    """Holt KI-Begruendung fuer die bereits getroffene Strategieentscheidung."""
    strategy_labels = {
        "even": "Gleichmäßig (Even Pacing)",
        "negative": "Negative Splits (±1.5%)",
        "effort_based": "Effort-Based (konstanter Effort)",
    }
    elevation_labels = {
        "flat": "flach",
        "rolling": "wellig",
        "hilly": "hügelig",
    }

    pace_sec = request.target_time_seconds / request.distance_km
    pace_min = int(pace_sec // 60)
    pace_s = int(pace_sec % 60)

    parts = [
        f"Gewaehlte Strategie: {strategy_labels.get(strategy, strategy)}",
        f"Hoehenprofil: {elevation_labels.get(elevation_preset, elevation_preset)}",
        f"Distanz: {request.distance_km} km",
        f"Ziel-Pace: {pace_min}:{pace_s:02d}/km",
    ]
    if request.race_name:
        parts.append(f"Rennen: {request.race_name}")
    if request.experience_level:
        labels = {
            "beginner": "Anfänger",
            "intermediate": "Fortgeschritten",
            "advanced": "Erfahren",
        }
        parts.append(f"Erfahrung: {labels.get(request.experience_level, request.experience_level)}")
    if request.temperature_celsius is not None:
        parts.append(f"Temperatur: {request.temperature_celsius}°C")

    user_prompt = "\n".join(parts)

    try:
        response_text = await ai_service.chat(
            message=user_prompt,
            context={"system_prompt": _REASONING_SYSTEM_PROMPT},
            api_key=api_key,
        )

        await log_ai_call(
            db,
            AICallData(
                use_case="pacing_recommendation",
                provider=ai_service.get_active_provider() or "unknown",
                system_prompt=_REASONING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                raw_response=response_text,
                parsed_ok=True,
            ),
        )

        return _parse_reasoning(response_text)
    except Exception:
        logger.warning("KI-Reasoning fehlgeschlagen, verwende Fallback")
        return _fallback_reasoning(strategy, elevation_preset, request)


def _parse_reasoning(text: str) -> str:
    """Extrahiert den reasoning-Text aus der KI-Antwort."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(cleaned)
        return str(data.get("reasoning", cleaned))
    except (json.JSONDecodeError, ValueError):
        # Wenn kein JSON: den ganzen Text als Reasoning verwenden
        return cleaned


def _fallback_reasoning(
    strategy: str,
    elevation_preset: str,
    request: PacingRecommendationRequest,
) -> str:
    """Erzeugt einen Fallback-Begruendungstext ohne KI."""
    if strategy == "effort_based":
        return (
            f"Fuer die {request.distance_km} km Strecke mit {elevation_preset}em Profil "
            "ist eine Effort-Based Strategie optimal. Die Pace variiert mit dem "
            "Hoehenprofil, waehrend die Belastung konstant bleibt."
        )
    if strategy == "negative":
        return (
            f"Bei {request.distance_km} km auf flacher Strecke empfiehlt sich eine "
            "Negative-Split-Strategie: konservativer Start mit leichter Steigerung "
            "in der zweiten Haelfte (±1.5%)."
        )
    return (
        f"Gleichmaessiges Pacing ist fuer {request.distance_km} km die energetisch "
        "effizienteste Strategie. Konstante Pace minimiert den Energieverbrauch "
        "und reduziert das Risiko eines Leistungseinbruchs."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_pacing_recommendation(
    request: PacingRecommendationRequest,
    api_key: str,
    db: AsyncSession,
) -> PacingRecommendationResponse:
    """Deterministische Strategieempfehlung mit KI-Begruendung."""
    elevation_preset = determine_elevation_preset(request.race_name)
    strategy = determine_strategy(
        distance_km=request.distance_km,
        elevation_preset=elevation_preset,
        experience_level=request.experience_level,
        temperature_celsius=request.temperature_celsius,
    )

    reasoning = await _get_ai_reasoning(request, strategy, elevation_preset, api_key, db)

    return PacingRecommendationResponse(
        strategy=strategy,
        elevation_preset=elevation_preset,
        reasoning=reasoning,
    )
