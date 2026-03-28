"""Pydantic models for training routes.

A TrainingRoute combines GPS waypoints with training segment targets,
enabling route-aware workout planning with pace/HR goals per section.

Part of Epic #508 (Routenplaner).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.taxonomy import SEGMENT_TYPE_REGEX

PACING_STRATEGY_REGEX = "^(even|negative|effort_based)$"


# ---------------------------------------------------------------------------
# Sub-Models
# ---------------------------------------------------------------------------


class Waypoint(BaseModel):
    """Ein GPS-Punkt auf der Route."""

    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    alt: Optional[float] = None
    km_marker: Optional[float] = Field(default=None, ge=0)


class RouteSegment(BaseModel):
    """Ein Trainingsabschnitt auf der Route mit Zielen."""

    segment_type: str = Field(..., pattern=SEGMENT_TYPE_REGEX)
    start_km: float = Field(..., ge=0)
    end_km: float = Field(..., gt=0)

    target_pace_min: Optional[str] = Field(default=None, max_length=10)
    target_pace_max: Optional[str] = Field(default=None, max_length=10)
    target_hr_min: Optional[int] = Field(default=None, ge=60, le=220)
    target_hr_max: Optional[int] = Field(default=None, ge=60, le=220)

    elevation_gain_m: Optional[float] = Field(default=None, ge=0)
    elevation_loss_m: Optional[float] = Field(default=None, ge=0)
    surface: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def end_after_start(self) -> RouteSegment:
        if self.end_km <= self.start_km:
            msg = f"end_km ({self.end_km}) muss größer als start_km ({self.start_km}) sein"
            raise ValueError(msg)
        return self


# ---------------------------------------------------------------------------
# CRUD Schemas
# ---------------------------------------------------------------------------


class TrainingRouteCreate(BaseModel):
    """Schema zum Erstellen einer Trainingsroute."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    distance_km: float = Field(..., gt=0)
    elevation_gain_m: float = Field(default=0, ge=0)
    elevation_loss_m: float = Field(default=0, ge=0)
    location_name: Optional[str] = Field(default=None, max_length=200)
    surface: Optional[dict[str, float]] = None
    waypoints: list[Waypoint] = Field(..., min_length=2)
    route_segments: Optional[list[RouteSegment]] = None
    pacing_strategy: Optional[str] = Field(default=None, pattern=PACING_STRATEGY_REGEX)
    linked_session_template_id: Optional[int] = None
    tags: Optional[list[str]] = None
    is_favorite: bool = False


class TrainingRouteUpdate(BaseModel):
    """Schema zum Aktualisieren einer Trainingsroute (Partial Update)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    distance_km: Optional[float] = Field(default=None, gt=0)
    elevation_gain_m: Optional[float] = Field(default=None, ge=0)
    elevation_loss_m: Optional[float] = Field(default=None, ge=0)
    location_name: Optional[str] = Field(default=None, max_length=200)
    surface: Optional[dict[str, float]] = None
    waypoints: Optional[list[Waypoint]] = Field(default=None, min_length=2)
    route_segments: Optional[list[RouteSegment]] = None
    pacing_strategy: Optional[str] = Field(default=None, pattern=PACING_STRATEGY_REGEX)
    linked_session_template_id: Optional[int] = None
    tags: Optional[list[str]] = None
    is_favorite: Optional[bool] = None


class TrainingRouteResponse(BaseModel):
    """Vollständige Antwort für eine einzelne Route."""

    id: int
    name: str
    description: Optional[str] = None
    distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float
    location_name: Optional[str] = None
    surface: Optional[dict[str, float]] = None
    waypoints: list[Waypoint]
    route_segments: Optional[list[RouteSegment]] = None
    pacing_strategy: Optional[str] = None
    linked_session_template_id: Optional[int] = None
    tags: Optional[list[str]] = None
    is_favorite: bool
    created_at: datetime
    updated_at: datetime


class TrainingRouteSummary(BaseModel):
    """Leichtgewichtige Zusammenfassung für Listen (ohne Waypoints)."""

    id: int
    name: str
    distance_km: float
    elevation_gain_m: float
    location_name: Optional[str] = None
    pacing_strategy: Optional[str] = None
    tags: Optional[list[str]] = None
    is_favorite: bool
    waypoint_count: int
    segment_count: int
    created_at: datetime
    updated_at: datetime


class TrainingRouteListResponse(BaseModel):
    """Paginierte Antwort für Routen-Liste."""

    routes: list[TrainingRouteSummary]
    total: int
