"""Tests for OSRM Client and Routing API (#520)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.infrastructure.external.osrm import OSRMClient, _offset_point

BASE = "/api/v1/routes"

# Mock OSRM route response
OSRM_ROUTE_RESPONSE = {
    "code": "Ok",
    "routes": [
        {
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [9.993, 53.567],
                    [9.991, 53.568],
                    [9.990, 53.570],
                    [9.988, 53.569],
                    [9.993, 53.567],
                ],
            },
            "distance": 1250.5,
            "duration": 520.3,
        }
    ],
    "waypoints": [
        {"location": [9.993, 53.567], "name": "Alsterufer"},
        {"location": [9.990, 53.570], "name": "Fährdamm"},
        {"location": [9.993, 53.567], "name": "Alsterufer"},
    ],
}

OSRM_NEAREST_RESPONSE = {
    "code": "Ok",
    "waypoints": [
        {"location": [9.993, 53.567], "distance": 5.2, "name": "Alsterufer"},
    ],
}


# ---------------------------------------------------------------------------
# Unit Tests: OSRMClient
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_osrm_route() -> None:
    client = OSRMClient()
    client.client.get = AsyncMock(return_value=OSRM_ROUTE_RESPONSE)

    result = await client.route(
        [
            {"lat": 53.567, "lng": 9.993},
            {"lat": 53.570, "lng": 9.990},
            {"lat": 53.567, "lng": 9.993},
        ]
    )

    assert result is not None
    assert result["distance_m"] == 1250.5
    assert result["duration_s"] == 520.3
    assert len(result["points"]) == 5
    assert result["points"][0]["lat"] == 53.567
    assert len(result["snapped_waypoints"]) == 3


@pytest.mark.anyio
async def test_osrm_route_error() -> None:
    client = OSRMClient()
    client.client.get = AsyncMock(return_value={"code": "NoRoute"})

    result = await client.route(
        [
            {"lat": 53.567, "lng": 9.993},
            {"lat": 53.570, "lng": 9.990},
        ]
    )
    assert result is None


@pytest.mark.anyio
async def test_osrm_route_none_response() -> None:
    client = OSRMClient()
    client.client.get = AsyncMock(return_value=None)

    result = await client.route(
        [
            {"lat": 53.567, "lng": 9.993},
            {"lat": 53.570, "lng": 9.990},
        ]
    )
    assert result is None


@pytest.mark.anyio
async def test_osrm_route_min_waypoints() -> None:
    client = OSRMClient()
    result = await client.route([{"lat": 53.567, "lng": 9.993}])
    assert result is None


@pytest.mark.anyio
async def test_osrm_nearest() -> None:
    client = OSRMClient()
    client.client.get = AsyncMock(return_value=OSRM_NEAREST_RESPONSE)

    result = await client.nearest(53.567, 9.993)
    assert result is not None
    assert result["lat"] == 53.567
    assert result["lng"] == 9.993
    assert result["distance_m"] == 5.2
    assert result["name"] == "Alsterufer"


@pytest.mark.anyio
async def test_osrm_nearest_error() -> None:
    client = OSRMClient()
    client.client.get = AsyncMock(return_value=None)

    result = await client.nearest(53.567, 9.993)
    assert result is None


@pytest.mark.anyio
async def test_osrm_round_trip() -> None:
    client = OSRMClient()
    client.client.get = AsyncMock(return_value=OSRM_ROUTE_RESPONSE)

    results = await client.generate_round_trip(
        start_lat=53.567,
        start_lng=9.993,
        target_distance_km=5.0,
        num_alternatives=2,
    )

    assert len(results) == 2
    for r in results:
        assert "points" in r
        assert "distance_km" in r
        assert "deviation_percent" in r
        assert "direction_deg" in r

    # Sortiert nach geringster Abweichung
    assert results[0]["deviation_percent"] <= results[1]["deviation_percent"]


def test_offset_point() -> None:
    """Punkt verschieben in gegebener Richtung + Distanz."""
    result = _offset_point(53.567, 9.993, 1.0, 0.0)  # 1km nach Norden
    assert result["lat"] > 53.567  # Nördlicher
    assert abs(result["lng"] - 9.993) < 0.001  # Länge fast gleich


def test_offset_point_east() -> None:
    result = _offset_point(53.567, 9.993, 1.0, 1.5708)  # ~90° = Osten
    assert abs(result["lat"] - 53.567) < 0.01  # Breite fast gleich
    assert result["lng"] > 9.993  # Östlicher


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_snap_route_api(client: AsyncClient) -> None:
    with patch("app.api.v1.training_routes.OSRMClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.route.return_value = {
            "points": [
                {"lat": 53.567, "lng": 9.993},
                {"lat": 53.570, "lng": 9.990},
            ],
            "distance_m": 800.0,
            "duration_s": 350.0,
            "snapped_waypoints": [
                {"lat": 53.567, "lng": 9.993},
                {"lat": 53.570, "lng": 9.990},
            ],
        }
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        resp = await client.post(
            f"{BASE}/snap",
            json={
                "waypoints": [
                    {"lat": 53.567, "lng": 9.993},
                    {"lat": 53.570, "lng": 9.990},
                ]
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["distance_km"] == 0.8
    assert len(body["points"]) == 2


@pytest.mark.anyio
async def test_snap_route_api_osrm_down(client: AsyncClient) -> None:
    with patch("app.api.v1.training_routes.OSRMClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.route.return_value = None
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        resp = await client.post(
            f"{BASE}/snap",
            json={
                "waypoints": [
                    {"lat": 53.567, "lng": 9.993},
                    {"lat": 53.570, "lng": 9.990},
                ]
            },
        )

    assert resp.status_code == 502


@pytest.mark.anyio
async def test_generate_round_trip_api(client: AsyncClient) -> None:
    with patch("app.api.v1.training_routes.OSRMClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.generate_round_trip.return_value = [
            {
                "points": [{"lat": 53.567, "lng": 9.993}, {"lat": 53.570, "lng": 9.990}],
                "distance_km": 10.2,
                "duration_s": 3600.0,
                "target_distance_km": 10.0,
                "deviation_percent": 2.0,
                "direction_deg": 45.0,
            }
        ]
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        resp = await client.post(
            f"{BASE}/generate-round-trip",
            json={
                "start_lat": 53.567,
                "start_lng": 9.993,
                "target_distance_km": 10.0,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["options"]) == 1
    assert body["options"][0]["distance_km"] == 10.2


@pytest.mark.anyio
async def test_generate_round_trip_validation(client: AsyncClient) -> None:
    resp = await client.post(
        f"{BASE}/generate-round-trip",
        json={
            "start_lat": 100.0,  # Invalid lat
            "start_lng": 9.993,
            "target_distance_km": 10.0,
        },
    )
    assert resp.status_code == 422
