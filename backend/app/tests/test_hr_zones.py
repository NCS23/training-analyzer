"""Tests fuer HR Zone Calculator und Athlete Settings API (E01-S03)."""

import io

import pytest
from httpx import AsyncClient

from app.services.hr_zone_calculator import (
    calculate_karvonen_zones,
    calculate_zone_distribution,
    karvonen_bpm,
)

# --- Unit Tests: Karvonen-Formel ---


def test_karvonen_bpm_basic() -> None:
    """Karvonen: Ruhe=50, Max=190, 70% → 148."""
    # HRR = 190 - 50 = 140, 70% von 140 = 98, 50 + 98 = 148
    assert karvonen_bpm(50, 190, 0.70) == 148


def test_karvonen_bpm_boundaries() -> None:
    """Karvonen: 0% = Ruhe-HR, 100% = Max-HR."""
    assert karvonen_bpm(50, 190, 0.0) == 50
    assert karvonen_bpm(50, 190, 1.0) == 190


def test_karvonen_bpm_rounding() -> None:
    """Karvonen rundet auf naechsten Integer."""
    # Ruhe=48, Max=185, 65% → 48 + (137 * 0.65) = 48 + 89.05 = 137.05 → 137
    result = karvonen_bpm(48, 185, 0.65)
    assert isinstance(result, int)


def test_calculate_karvonen_zones_count() -> None:
    """5 Zonen werden generiert."""
    zones = calculate_karvonen_zones(50, 190)
    assert len(zones) == 5


def test_calculate_karvonen_zones_order() -> None:
    """Zonen sind aufsteigend nach BPM."""
    zones = calculate_karvonen_zones(50, 190)
    for i in range(len(zones) - 1):
        assert zones[i]["upper_bpm"] <= zones[i + 1]["upper_bpm"]


def test_calculate_karvonen_zones_coverage() -> None:
    """Zone 1 beginnt bei 50%, Zone 5 endet bei 100%."""
    zones = calculate_karvonen_zones(50, 190)
    assert zones[0]["pct_min"] == 0.50
    assert zones[-1]["pct_max"] == 1.00


def test_calculate_karvonen_zones_names() -> None:
    """Zonen haben korrekte Namen."""
    zones = calculate_karvonen_zones(50, 190)
    names = [z["name"] for z in zones]
    assert names == ["Recovery", "Base", "Tempo", "Threshold", "VO2max"]


# --- Unit Tests: Zone Distribution ---


def test_zone_distribution_3zone_fallback() -> None:
    """Ohne Athleten-Daten: 3-Zonen Fallback."""
    hr_values = [120, 130, 140, 155, 165, 170]
    result = calculate_zone_distribution(hr_values)
    assert "zone_1_recovery" in result
    assert "zone_2_base" in result
    assert "zone_3_tempo" in result
    assert len(result) == 3


def test_zone_distribution_karvonen_5zones() -> None:
    """Mit Athleten-Daten: 5-Zonen Karvonen."""
    hr_values = [100, 120, 140, 155, 165, 175, 185]
    result = calculate_zone_distribution(hr_values, resting_hr=50, max_hr=190)
    assert len(result) == 5
    # Alle Zonen sollten zone/name/color haben
    for zone_data in result.values():
        assert "seconds" in zone_data
        assert "percentage" in zone_data
        assert "zone" in zone_data
        assert "name" in zone_data
        assert "color" in zone_data


def test_zone_distribution_percentages_sum_to_100() -> None:
    """Prozentsaetze summieren sich auf ~100%."""
    hr_values = [130, 145, 155, 165, 180] * 20
    result = calculate_zone_distribution(hr_values, resting_hr=50, max_hr=190)
    total_pct = sum(z["percentage"] for z in result.values())
    assert abs(total_pct - 100.0) < 0.5  # Rundungstoleranzen


def test_zone_distribution_empty() -> None:
    """Leere HR-Werte geben leeres Dict."""
    result = calculate_zone_distribution([])
    assert result == {}


# --- Integration Tests: Athlete Settings API ---


@pytest.mark.anyio
async def test_get_athlete_settings_default(client: AsyncClient) -> None:
    """GET /athlete/settings erstellt Singleton und gibt leere Werte."""
    response = await client.get("/api/v1/athlete/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["resting_hr"] is None
    assert body["max_hr"] is None
    assert body["karvonen_zones"] is None


@pytest.mark.anyio
async def test_update_athlete_settings(client: AsyncClient) -> None:
    """PUT /athlete/settings speichert HR-Werte."""
    response = await client.put(
        "/api/v1/athlete/settings",
        json={"resting_hr": 50, "max_hr": 190},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resting_hr"] == 50
    assert body["max_hr"] == 190
    assert body["karvonen_zones"] is not None
    assert len(body["karvonen_zones"]) == 5


@pytest.mark.anyio
async def test_athlete_settings_persist(client: AsyncClient) -> None:
    """Settings sind nach GET noch vorhanden."""
    await client.put(
        "/api/v1/athlete/settings",
        json={"resting_hr": 48, "max_hr": 185},
    )
    response = await client.get("/api/v1/athlete/settings")
    body = response.json()
    assert body["resting_hr"] == 48
    assert body["max_hr"] == 185


@pytest.mark.anyio
async def test_athlete_settings_karvonen_zones_correct(client: AsyncClient) -> None:
    """Karvonen-Zonen haben korrekte BPM-Grenzen."""
    await client.put(
        "/api/v1/athlete/settings",
        json={"resting_hr": 50, "max_hr": 190},
    )
    response = await client.get("/api/v1/athlete/settings")
    zones = response.json()["karvonen_zones"]

    # Zone 1: 50 + 140*0.50=120 bis 50 + 140*0.60=134
    assert zones[0]["lower_bpm"] == 120
    assert zones[0]["upper_bpm"] == 134

    # Zone 5: 50 + 140*0.90=176 bis 50 + 140*1.00=190
    assert zones[4]["lower_bpm"] == 176
    assert zones[4]["upper_bpm"] == 190


# --- Integration Tests: Upload mit Karvonen ---


RUNNING_CSV = """\
date;timestamp;ISO8601;since_start;hr (count/min);cadence (count/min);distance (meter);speed (m/s);lap;latitude;longitude;elevation (meter)
2024-03-15;1710488400;2024-03-15T07:00:00;0;120;160;0;0;1;52,52;13,40;35
2024-03-15;1710488460;2024-03-15T07:01:00;60;130;162;180;3,0;1;52,52;13,40;35
2024-03-15;1710488520;2024-03-15T07:02:00;120;135;164;360;3,0;1;52,52;13,40;36
2024-03-15;1710488580;2024-03-15T07:03:00;180;165;178;540;3,0;2;52,52;13,41;37
2024-03-15;1710488640;2024-03-15T07:04:00;240;170;180;720;3,33;2;52,52;13,41;37
2024-03-15;1710488700;2024-03-15T07:05:00;300;140;162;900;2,5;3;52,52;13,42;38
"""


@pytest.mark.anyio
async def test_upload_with_karvonen_zones(client: AsyncClient) -> None:
    """Upload mit Athleten-Daten gibt 5-Zonen Karvonen zurueck."""
    # Setup athlete
    await client.put(
        "/api/v1/athlete/settings",
        json={"resting_hr": 50, "max_hr": 190},
    )

    # Upload
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files={"csv_file": ("training.csv", io.BytesIO(RUNNING_CSV.encode("utf-8")), "text/csv")},
        data={"training_date": "2024-03-15", "training_type": "running"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True

    hr_zones = body["data"]["hr_zones"]
    assert len(hr_zones) == 5
    assert body["metadata"]["hr_zone_method"] == "karvonen"


@pytest.mark.anyio
async def test_upload_without_athlete_uses_3zone_fallback(client: AsyncClient) -> None:
    """Upload ohne Athleten-Daten gibt 3-Zonen Fallback zurueck."""
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files={"csv_file": ("training.csv", io.BytesIO(RUNNING_CSV.encode("utf-8")), "text/csv")},
        data={"training_date": "2024-03-15", "training_type": "running"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True

    hr_zones = body["data"]["hr_zones"]
    assert len(hr_zones) == 3
    assert body["metadata"]["hr_zone_method"] == "fixed_3zone"
