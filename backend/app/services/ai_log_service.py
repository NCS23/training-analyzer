"""Zentraler Logging-Service fuer alle KI-Aufrufe."""

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AIAnalysisLogModel

logger = logging.getLogger(__name__)


@dataclass
class AICallData:
    """Daten eines KI-Aufrufs fuer das Logging."""

    use_case: str
    provider: str
    system_prompt: str
    user_prompt: str
    raw_response: str
    parsed_ok: bool
    duration_ms: int | None = None
    workout_id: int | None = None
    context_label: str | None = None


async def log_ai_call(db: AsyncSession, data: AICallData) -> None:
    """Schreibt einen KI-Aufruf ins ai_analysis_log.

    Wird von allen Services verwendet, die KI-Aufrufe machen
    (Session-Analyse, Uebungs-Anreicherung, etc.).
    """
    db.add(
        AIAnalysisLogModel(
            use_case=data.use_case,
            provider=data.provider,
            system_prompt=data.system_prompt,
            user_prompt=data.user_prompt,
            raw_response=data.raw_response,
            parsed_ok=data.parsed_ok,
            duration_ms=data.duration_ms,
            workout_id=data.workout_id,
            context_label=data.context_label,
        )
    )
    await db.commit()
    logger.info("KI-Log geschrieben: use_case=%s, parsed_ok=%s", data.use_case, data.parsed_ok)
