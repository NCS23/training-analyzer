"""API routes for Training Routes (#508)."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    SessionTemplateModel,
    TrainingRouteModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.training_route import (
    RouteSegment,
    TrainingRouteCreate,
    TrainingRouteListResponse,
    TrainingRouteResponse,
    TrainingRouteSummary,
    TrainingRouteUpdate,
    Waypoint,
)
from app.services.route_from_session import session_to_route_data

router = APIRouter(prefix="/routes")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_json_list(raw: Optional[str]) -> list:
    """Parse JSON-String zu Liste, leere Liste bei Fehler."""
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []


def _parse_json_dict(raw: Optional[str]) -> Optional[dict]:
    """Parse JSON-String zu Dict."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None


def _model_to_response(route: TrainingRouteModel) -> TrainingRouteResponse:
    waypoints_raw = _parse_json_list(str(route.waypoints_json))
    waypoints = [Waypoint(**wp) for wp in waypoints_raw]

    segments: Optional[list[RouteSegment]] = None
    segments_raw = _parse_json_list(
        str(route.route_segments_json) if route.route_segments_json else None
    )
    if segments_raw:
        segments = [RouteSegment(**seg) for seg in segments_raw]

    return TrainingRouteResponse(
        id=route.id,
        name=str(route.name),
        description=str(route.description) if route.description else None,
        distance_km=float(route.distance_km),
        elevation_gain_m=float(route.elevation_gain_m),
        elevation_loss_m=float(route.elevation_loss_m),
        location_name=str(route.location_name) if route.location_name else None,
        surface=_parse_json_dict(str(route.surface_json) if route.surface_json else None),
        waypoints=waypoints,
        route_segments=segments,
        pacing_strategy=(str(route.pacing_strategy) if route.pacing_strategy else None),
        linked_session_template_id=route.linked_session_template_id,
        tags=_parse_json_list(str(route.tags_json) if route.tags_json else None) or None,
        is_favorite=bool(route.is_favorite),
        created_at=route.created_at,
        updated_at=route.updated_at,
    )


def _model_to_summary(route: TrainingRouteModel) -> TrainingRouteSummary:
    waypoints_raw = _parse_json_list(str(route.waypoints_json))
    segments_raw = _parse_json_list(
        str(route.route_segments_json) if route.route_segments_json else None
    )

    return TrainingRouteSummary(
        id=route.id,
        name=str(route.name),
        distance_km=float(route.distance_km),
        elevation_gain_m=float(route.elevation_gain_m),
        location_name=str(route.location_name) if route.location_name else None,
        pacing_strategy=(str(route.pacing_strategy) if route.pacing_strategy else None),
        tags=_parse_json_list(str(route.tags_json) if route.tags_json else None) or None,
        is_favorite=bool(route.is_favorite),
        waypoint_count=len(waypoints_raw),
        segment_count=len(segments_raw),
        created_at=route.created_at,
        updated_at=route.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=TrainingRouteResponse, status_code=201)
async def create_route(
    data: TrainingRouteCreate,
    db: AsyncSession = Depends(get_db),
) -> TrainingRouteResponse:
    """Neue Trainingsroute erstellen."""
    # FK-Validierung
    if data.linked_session_template_id is not None:
        result = await db.execute(
            select(SessionTemplateModel.id).where(
                SessionTemplateModel.id == data.linked_session_template_id
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=422,
                detail="Session Template nicht gefunden",
            )

    route = TrainingRouteModel(
        name=data.name,
        description=data.description,
        distance_km=data.distance_km,
        elevation_gain_m=data.elevation_gain_m,
        elevation_loss_m=data.elevation_loss_m,
        location_name=data.location_name,
        surface_json=(json.dumps(data.surface) if data.surface else None),
        waypoints_json=json.dumps([wp.model_dump() for wp in data.waypoints]),
        route_segments_json=(
            json.dumps([seg.model_dump() for seg in data.route_segments])
            if data.route_segments
            else None
        ),
        pacing_strategy=data.pacing_strategy,
        linked_session_template_id=data.linked_session_template_id,
        tags_json=json.dumps(data.tags) if data.tags else None,
        is_favorite=data.is_favorite,
    )
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return _model_to_response(route)


@router.get("", response_model=TrainingRouteListResponse)
async def list_routes(
    is_favorite: Optional[bool] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> TrainingRouteListResponse:
    """Alle Trainingsrouten auflisten (ohne Waypoints)."""
    query = select(TrainingRouteModel).order_by(TrainingRouteModel.updated_at.desc())

    if is_favorite is not None:
        query = query.where(TrainingRouteModel.is_favorite == is_favorite)

    if tag:
        query = query.where(TrainingRouteModel.tags_json.contains(f'"{tag}"'))

    if search:
        pattern = f"%{search}%"
        query = query.where(
            TrainingRouteModel.name.ilike(pattern) | TrainingRouteModel.location_name.ilike(pattern)
        )

    result = await db.execute(query)
    routes = list(result.scalars().all())

    # Total count (same filters)
    count_q = select(func.count(TrainingRouteModel.id))
    if is_favorite is not None:
        count_q = count_q.where(TrainingRouteModel.is_favorite == is_favorite)
    if tag:
        count_q = count_q.where(TrainingRouteModel.tags_json.contains(f'"{tag}"'))
    if search:
        pattern = f"%{search}%"
        count_q = count_q.where(
            TrainingRouteModel.name.ilike(pattern) | TrainingRouteModel.location_name.ilike(pattern)
        )

    total = (await db.execute(count_q)).scalar() or 0

    return TrainingRouteListResponse(
        routes=[_model_to_summary(r) for r in routes],
        total=total,
    )


@router.post("/from-session/{session_id}", response_model=TrainingRouteResponse, status_code=201)
async def create_route_from_session(
    session_id: int,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> TrainingRouteResponse:
    """Route aus einer bestehenden Session mit GPS-Daten erstellen."""
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    if not workout.gps_track_json:
        raise HTTPException(status_code=422, detail="Session hat keine GPS-Daten")

    try:
        route_data = session_to_route_data(workout, name=name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    route = TrainingRouteModel(
        name=route_data["name"],
        distance_km=route_data["distance_km"],
        elevation_gain_m=route_data["elevation_gain_m"],
        elevation_loss_m=route_data["elevation_loss_m"],
        location_name=route_data["location_name"],
        surface_json=json.dumps(route_data["surface"]) if route_data["surface"] else None,
        waypoints_json=json.dumps(route_data["waypoints"]),
        route_segments_json=(
            json.dumps(route_data["route_segments"]) if route_data["route_segments"] else None
        ),
    )
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return _model_to_response(route)


@router.get("/{route_id}", response_model=TrainingRouteResponse)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
) -> TrainingRouteResponse:
    """Einzelne Route mit allen Details abrufen."""
    result = await db.execute(select(TrainingRouteModel).where(TrainingRouteModel.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route nicht gefunden")
    return _model_to_response(route)


@router.patch("/{route_id}", response_model=TrainingRouteResponse)
async def update_route(
    route_id: int,
    data: TrainingRouteUpdate,
    db: AsyncSession = Depends(get_db),
) -> TrainingRouteResponse:
    """Route teilweise aktualisieren."""
    result = await db.execute(select(TrainingRouteModel).where(TrainingRouteModel.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "waypoints" and value is not None:
            route.waypoints_json = json.dumps(
                [wp.model_dump() for wp in data.waypoints]  # type: ignore[union-attr]
            )
        elif field == "route_segments" and value is not None:
            route.route_segments_json = json.dumps(
                [seg.model_dump() for seg in data.route_segments]  # type: ignore[union-attr]
            )
        elif field == "surface" and value is not None:
            route.surface_json = json.dumps(value)
        elif field == "tags" and value is not None:
            route.tags_json = json.dumps(value)
        elif hasattr(route, field):
            setattr(route, field, value)

    await db.commit()
    await db.refresh(route)
    return _model_to_response(route)


@router.delete("/{route_id}", status_code=204)
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Route löschen."""
    result = await db.execute(select(TrainingRouteModel).where(TrainingRouteModel.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route nicht gefunden")
    await db.delete(route)
    await db.commit()
