"""Pydantic Models für KI-Trainingsempfehlungen (E06-S02)."""

from enum import Enum

from pydantic import BaseModel


class RecommendationType(str, Enum):
    """Typ der Empfehlung — bestimmt welche Aktion vorgeschlagen wird."""

    ADJUST_PACE = "adjust_pace"
    ADJUST_VOLUME = "adjust_volume"
    ADD_REST = "add_rest"
    SKIP_SESSION = "skip_session"
    INCREASE_VOLUME = "increase_volume"
    REDUCE_INTENSITY = "reduce_intensity"
    CHANGE_SESSION_TYPE = "change_session_type"
    EXTEND_WARMUP_COOLDOWN = "extend_warmup_cooldown"
    GENERAL = "general"


class RecommendationPriority(str, Enum):
    """Prioritaet der Empfehlung."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationStatus(str, Enum):
    """Status einer Empfehlung."""

    PENDING = "pending"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class RecommendationResponse(BaseModel):
    """Einzelne Empfehlung — Response."""

    id: int
    session_id: int
    type: RecommendationType
    title: str
    target_session_id: int | None = None
    current_value: str | None = None
    suggested_value: str | None = None
    reasoning: str
    priority: RecommendationPriority
    status: RecommendationStatus = RecommendationStatus.PENDING
    created_at: str


class RecommendationsListResponse(BaseModel):
    """Liste von Empfehlungen fuer eine Session."""

    recommendations: list[RecommendationResponse]
    session_id: int
    provider: str
    cached: bool = False


class RecommendationStatusUpdate(BaseModel):
    """Request zum Aendern des Empfehlungs-Status."""

    status: RecommendationStatus
