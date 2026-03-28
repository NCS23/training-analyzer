"""Tests for Training Routes API (#508 / #509 / #513)."""

import json

import pytest
from httpx import AsyncClient

BASE = "/api/v1/routes"

WAYPOINTS = [
    {"lat": 53.567, "lng": 9.993, "alt": 12.0, "km_marker": 0.0},
    {"lat": 53.570, "lng": 9.990, "alt": 14.0, "km_marker": 3.5},
    {"lat": 53.572, "lng": 9.988, "alt": 10.0, "km_marker": 7.0},
    {"lat": 53.567, "lng": 9.993, "alt": 12.0, "km_marker": 10.5},
]

SEGMENTS = [
    {
        "segment_type": "warmup",
        "start_km": 0.0,
        "end_km": 2.0,
        "target_pace_min": "5:30",
        "target_pace_max": "6:00",
        "notes": "Locker einlaufen",
    },
    {
        "segment_type": "steady",
        "start_km": 2.0,
        "end_km": 8.5,
        "target_pace_min": "4:45",
        "target_pace_max": "5:00",
        "target_hr_min": 155,
        "target_hr_max": 165,
    },
    {
        "segment_type": "cooldown",
        "start_km": 8.5,
        "end_km": 10.5,
        "target_pace_min": "5:30",
        "target_pace_max": "6:30",
    },
]

ROUTE_DATA = {
    "name": "Alsterrunde 10k",
    "description": "Schöne Runde um die Außenalster",
    "distance_km": 10.5,
    "elevation_gain_m": 45.0,
    "elevation_loss_m": 45.0,
    "location_name": "Alster, Hamburg",
    "surface": {"Asphalt": 70.0, "Schotter": 30.0},
    "waypoints": WAYPOINTS,
    "route_segments": SEGMENTS,
    "pacing_strategy": "even",
    "tags": ["dauerlauf", "alster"],
    "is_favorite": True,
}

ROUTE_MINIMAL = {
    "name": "Kurzroute",
    "distance_km": 3.0,
    "waypoints": [
        {"lat": 53.55, "lng": 9.99},
        {"lat": 53.56, "lng": 9.98},
    ],
}


# ---------------------------------------------------------------------------
# CRUD Happy Path
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_route(client: AsyncClient) -> None:
    resp = await client.post(BASE, json=ROUTE_DATA)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Alsterrunde 10k"
    assert body["distance_km"] == 10.5
    assert body["elevation_gain_m"] == 45.0
    assert body["location_name"] == "Alster, Hamburg"
    assert body["pacing_strategy"] == "even"
    assert body["is_favorite"] is True
    assert body["tags"] == ["dauerlauf", "alster"]
    assert body["surface"] == {"Asphalt": 70.0, "Schotter": 30.0}
    assert len(body["waypoints"]) == 4
    assert len(body["route_segments"]) == 3
    assert body["route_segments"][0]["segment_type"] == "warmup"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.anyio
async def test_create_route_minimal(client: AsyncClient) -> None:
    resp = await client.post(BASE, json=ROUTE_MINIMAL)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Kurzroute"
    assert body["distance_km"] == 3.0
    assert body["elevation_gain_m"] == 0
    assert body["elevation_loss_m"] == 0
    assert body["is_favorite"] is False
    assert body["pacing_strategy"] is None
    assert body["route_segments"] is None
    assert body["tags"] is None
    assert len(body["waypoints"]) == 2


@pytest.mark.anyio
async def test_list_routes(client: AsyncClient) -> None:
    await client.post(BASE, json=ROUTE_DATA)
    await client.post(BASE, json=ROUTE_MINIMAL)

    resp = await client.get(BASE)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["routes"]) == 2

    # Summary hat keine Waypoints
    summary = body["routes"][0]
    assert "waypoints" not in summary
    assert "route_segments" not in summary
    assert "waypoint_count" in summary
    assert "segment_count" in summary


@pytest.mark.anyio
async def test_get_route(client: AsyncClient) -> None:
    create = await client.post(BASE, json=ROUTE_DATA)
    route_id = create.json()["id"]

    resp = await client.get(f"{BASE}/{route_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == route_id
    assert len(body["waypoints"]) == 4
    assert body["route_segments"][1]["target_hr_min"] == 155


@pytest.mark.anyio
async def test_update_route(client: AsyncClient) -> None:
    create = await client.post(BASE, json=ROUTE_MINIMAL)
    route_id = create.json()["id"]

    resp = await client.patch(
        f"{BASE}/{route_id}",
        json={"name": "Umbenannt", "is_favorite": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Umbenannt"
    assert body["is_favorite"] is True
    # Unveränderte Felder bleiben
    assert body["distance_km"] == 3.0


@pytest.mark.anyio
async def test_delete_route(client: AsyncClient) -> None:
    create = await client.post(BASE, json=ROUTE_MINIMAL)
    route_id = create.json()["id"]

    resp = await client.delete(f"{BASE}/{route_id}")
    assert resp.status_code == 204

    resp = await client.get(f"{BASE}/{route_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Validierung
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_route_no_name(client: AsyncClient) -> None:
    data = {**ROUTE_MINIMAL, "name": ""}
    resp = await client.post(BASE, json=data)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_route_empty_waypoints(client: AsyncClient) -> None:
    data = {**ROUTE_MINIMAL, "waypoints": []}
    resp = await client.post(BASE, json=data)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_route_single_waypoint(client: AsyncClient) -> None:
    data = {**ROUTE_MINIMAL, "waypoints": [{"lat": 53.55, "lng": 9.99}]}
    resp = await client.post(BASE, json=data)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_route_invalid_lat(client: AsyncClient) -> None:
    data = {
        **ROUTE_MINIMAL,
        "waypoints": [
            {"lat": 99.0, "lng": 9.99},
            {"lat": 53.56, "lng": 9.98},
        ],
    }
    resp = await client.post(BASE, json=data)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_route_invalid_pacing(client: AsyncClient) -> None:
    data = {**ROUTE_MINIMAL, "pacing_strategy": "sprint"}
    resp = await client.post(BASE, json=data)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_route_segment_end_before_start(client: AsyncClient) -> None:
    data = {
        **ROUTE_MINIMAL,
        "route_segments": [
            {"segment_type": "warmup", "start_km": 2.0, "end_km": 1.0},
        ],
    }
    resp = await client.post(BASE, json=data)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_routes_filter_favorite(client: AsyncClient) -> None:
    await client.post(BASE, json=ROUTE_DATA)  # is_favorite=True
    await client.post(BASE, json=ROUTE_MINIMAL)  # is_favorite=False

    resp = await client.get(BASE, params={"is_favorite": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["routes"][0]["is_favorite"] is True


@pytest.mark.anyio
async def test_list_routes_filter_tag(client: AsyncClient) -> None:
    await client.post(BASE, json=ROUTE_DATA)  # tags: dauerlauf, alster
    await client.post(BASE, json=ROUTE_MINIMAL)  # keine tags

    resp = await client.get(BASE, params={"tag": "alster"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1


@pytest.mark.anyio
async def test_list_routes_search(client: AsyncClient) -> None:
    await client.post(BASE, json=ROUTE_DATA)  # name: Alsterrunde 10k
    await client.post(BASE, json=ROUTE_MINIMAL)  # name: Kurzroute

    resp = await client.get(BASE, params={"search": "alster"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["routes"][0]["name"] == "Alsterrunde 10k"


# ---------------------------------------------------------------------------
# 404
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_route_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"{BASE}/99999")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_update_route_not_found(client: AsyncClient) -> None:
    resp = await client.patch(f"{BASE}/99999", json={"name": "X"})
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_route_not_found(client: AsyncClient) -> None:
    resp = await client.delete(f"{BASE}/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_surface_roundtrip(client: AsyncClient) -> None:
    """Surface Dict wird korrekt gespeichert und zurückgegeben."""
    data = {
        **ROUTE_MINIMAL,
        "surface": {"Asphalt": 60.0, "Gras": 25.0, "Schotter": 15.0},
    }
    resp = await client.post(BASE, json=data)
    assert resp.status_code == 201
    body = resp.json()
    assert body["surface"]["Asphalt"] == 60.0
    assert body["surface"]["Gras"] == 25.0


@pytest.mark.anyio
async def test_update_waypoints(client: AsyncClient) -> None:
    """Waypoints können per PATCH aktualisiert werden."""
    create = await client.post(BASE, json=ROUTE_MINIMAL)
    route_id = create.json()["id"]

    new_waypoints = [
        {"lat": 53.0, "lng": 10.0},
        {"lat": 53.1, "lng": 10.1},
        {"lat": 53.2, "lng": 10.2},
    ]
    resp = await client.patch(f"{BASE}/{route_id}", json={"waypoints": new_waypoints})
    assert resp.status_code == 200
    assert len(resp.json()["waypoints"]) == 3


# ---------------------------------------------------------------------------
# From-Session Import (#513)
# ---------------------------------------------------------------------------

GPS_TRACK = {
    "points": [
        {"lat": 53.5670, "lng": 9.9930, "alt": 12.0, "seconds": 0, "hr": 130},
        {"lat": 53.5680, "lng": 9.9920, "alt": 14.0, "seconds": 60, "hr": 140},
        {"lat": 53.5690, "lng": 9.9910, "alt": 16.0, "seconds": 120, "hr": 150},
        {"lat": 53.5700, "lng": 9.9900, "alt": 13.0, "seconds": 180, "hr": 145},
        {"lat": 53.5710, "lng": 9.9890, "alt": 11.0, "seconds": 240, "hr": 135},
    ],
    "total_ascent_m": 4.0,
    "total_descent_m": 5.0,
}

LAPS_DATA = [
    {
        "lap_number": 1,
        "duration_seconds": 120,
        "distance_km": 0.5,
        "pace_formatted": "4:00",
        "avg_hr_bpm": 135,
        "max_hr_bpm": 140,
        "suggested_type": "warmup",
    },
    {
        "lap_number": 2,
        "duration_seconds": 120,
        "distance_km": 0.8,
        "pace_formatted": "3:30",
        "avg_hr_bpm": 155,
        "max_hr_bpm": 165,
        "suggested_type": "work",
    },
]


async def _create_session_with_gps(
    client: AsyncClient,
    has_gps: bool = True,
    with_laps: bool = False,
    location: str | None = "Alster, Hamburg",
    surface: dict | None = None,
) -> int:
    """Helper: Session mit GPS-Daten direkt in DB anlegen."""
    from datetime import datetime

    from app.infrastructure.database.models import WorkoutModel
    from app.infrastructure.database.session import get_db
    from app.main import app

    # Get DB session via dependency override
    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()

    workout = WorkoutModel(
        date=datetime(2026, 3, 15, 8, 0, 0),
        workout_type="running",
        duration_sec=240,
        distance_km=1.3,
        gps_track_json=json.dumps(GPS_TRACK) if has_gps else None,
        has_gps=has_gps,
        laps_json=json.dumps(LAPS_DATA) if with_laps else None,
        location_name=location,
        surface_json=json.dumps(surface) if surface else None,
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout.id


@pytest.mark.anyio
async def test_create_route_from_session(client: AsyncClient) -> None:
    session_id = await _create_session_with_gps(client, location="Alster, Hamburg")

    resp = await client.post(f"{BASE}/from-session/{session_id}")
    assert resp.status_code == 201
    body = resp.json()
    assert "Alster" in body["name"]
    assert body["distance_km"] > 0
    assert len(body["waypoints"]) >= 2
    assert body["waypoints"][0]["km_marker"] == 0.0
    assert body["location_name"] == "Alster, Hamburg"


@pytest.mark.anyio
async def test_create_route_from_session_custom_name(client: AsyncClient) -> None:
    session_id = await _create_session_with_gps(client)

    resp = await client.post(f"{BASE}/from-session/{session_id}", params={"name": "Meine Runde"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Meine Runde"


@pytest.mark.anyio
async def test_create_route_from_session_with_laps(client: AsyncClient) -> None:
    session_id = await _create_session_with_gps(client, with_laps=True)

    resp = await client.post(f"{BASE}/from-session/{session_id}")
    assert resp.status_code == 201
    body = resp.json()
    assert body["route_segments"] is not None
    assert len(body["route_segments"]) == 2
    assert body["route_segments"][0]["segment_type"] == "warmup"
    assert body["route_segments"][1]["segment_type"] == "work"


@pytest.mark.anyio
async def test_create_route_from_session_with_surface(client: AsyncClient) -> None:
    surface = {"Asphalt": 70.0, "Gras": 30.0}
    session_id = await _create_session_with_gps(client, surface=surface)

    resp = await client.post(f"{BASE}/from-session/{session_id}")
    assert resp.status_code == 201
    assert resp.json()["surface"]["Asphalt"] == 70.0


@pytest.mark.anyio
async def test_create_route_from_session_no_gps(client: AsyncClient) -> None:
    session_id = await _create_session_with_gps(client, has_gps=False)

    resp = await client.post(f"{BASE}/from-session/{session_id}")
    assert resp.status_code == 422
    assert "GPS" in resp.json()["detail"]


@pytest.mark.anyio
async def test_create_route_from_session_not_found(client: AsyncClient) -> None:
    resp = await client.post(f"{BASE}/from-session/99999")
    assert resp.status_code == 404
