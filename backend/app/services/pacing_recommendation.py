"""KI-basierte Pacing-Strategie-Empfehlung via Claude API."""

from __future__ import annotations

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.ai.ai_service import ai_service
from app.models.pacing import PacingRecommendationRequest, PacingRecommendationResponse
from app.services.ai_log_service import AICallData, log_ai_call

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Du bist ein erfahrener Lauftrainer und Sportwissenschaftler.
Der Athlet fragt dich, welche Pacing-Strategie er für ein Rennen wählen soll.

Antworte NUR mit einem JSON-Objekt (kein Markdown, kein Text drumherum):
{
  "strategy": "even" | "negative" | "effort_based",
  "elevation_preset": "flat" | "rolling" | "hilly",
  "reasoning": "<2-3 Sätze Begründung auf Deutsch>"
}

Regeln für die Empfehlung:
- even (Gleichmäßig): Gut für Anfänger und flache Strecken. Einfachste Strategie.
- negative (Negative Splits): Für erfahrene Läufer. Konservativer Start, starkes Finish.
- effort_based (Konstanter Effort): Für hügelige Strecken. Pace variiert, Belastung gleich.

Höhenprofil:
- flat: Flache Strecken (z.B. Berlin, Hamburg, Amsterdam)
- rolling: Leicht wellige Strecken (z.B. Frankfurt, Köln)
- hilly: Hügelige Strecken (z.B. Zürich, Jena)

Berücksichtige:
- Bekannte Rennstrecken und deren Profile
- Erfahrungslevel des Athleten
- Ambitionsniveau (Pace zur Distanz)
"""


async def get_pacing_recommendation(
    request: PacingRecommendationRequest,
    api_key: str,
    db: AsyncSession,
) -> PacingRecommendationResponse:
    """Holt eine KI-Empfehlung fuer die Pacing-Strategie."""
    user_prompt = _build_prompt(request)

    response_text = await ai_service.chat(
        message=user_prompt,
        context={"system_prompt": _SYSTEM_PROMPT},
        api_key=api_key,
    )

    parsed = _parse_response(response_text)

    await log_ai_call(
        db,
        AICallData(
            use_case="pacing_recommendation",
            provider=ai_service.get_active_provider() or "unknown",
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            raw_response=response_text,
            parsed_ok=parsed is not None,
        ),
    )

    if not parsed:
        raise ValueError("KI-Antwort konnte nicht verarbeitet werden")

    return parsed


def _build_prompt(request: PacingRecommendationRequest) -> str:
    """Baut den User-Prompt fuer die KI-Empfehlung."""
    pace_sec = request.target_time_seconds / request.distance_km
    pace_min = int(pace_sec // 60)
    pace_s = int(pace_sec % 60)

    hours = request.target_time_seconds // 3600
    mins = (request.target_time_seconds % 3600) // 60
    secs = request.target_time_seconds % 60
    time_str = f"{hours}:{mins:02d}:{secs:02d}" if hours else f"{mins}:{secs:02d}"

    parts = [
        f"Distanz: {request.distance_km} km",
        f"Zielzeit: {time_str} (Pace: {pace_min}:{pace_s:02d}/km)",
    ]
    if request.race_name:
        parts.insert(0, f"Rennen: {request.race_name}")
    if request.experience_level:
        labels = {
            "beginner": "Anfänger",
            "intermediate": "Fortgeschritten",
            "advanced": "Erfahren",
        }
        parts.append(f"Erfahrung: {labels.get(request.experience_level, request.experience_level)}")

    return "\n".join(parts)


def _parse_response(text: str) -> PacingRecommendationResponse | None:
    """Parst die KI-Antwort als JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(cleaned)
        return PacingRecommendationResponse(**data)
    except (json.JSONDecodeError, ValueError):
        logger.warning("KI-Antwort nicht als JSON parsbar: %s", text[:200])
        return None
