"""Tests für Laktatschwellen-Test API."""

import pytest
from httpx import AsyncClient

from app.services.hr_zone_calculator import calculate_friel_zones

# --- Unit Tests: Friel-Zonenberechnung ---


def test_friel_zones_count() -> None:
    """Friel berechnet 5 Zonen."""
    zones = calculate_friel_zones(170)
    assert len(zones) == 5


def test_friel_zones_boundaries() -> None:
    """Friel-Zonen haben korrekte LTHR-basierte Grenzen."""
    lthr = 170
    zones = calculate_friel_zones(lthr)

    # Zone 1 Recovery: 0-85% LTHR
    assert zones[0]["zone"] == 1
    assert zones[0]["name"] == "Recovery"
    assert zones[0]["lower_bpm"] == 0
    assert zones[0]["upper_bpm"] == round(170 * 0.85)  # 145

    # Zone 4 Sub-Threshold: 95-100% LTHR
    assert zones[3]["zone"] == 4
    assert zones[3]["lower_bpm"] == round(170 * 0.95)  # 162
    assert zones[3]["upper_bpm"] == 170  # 100% LTHR

    # Zone 5 Supra-Threshold: 100-106% LTHR
    assert zones[4]["zone"] == 5
    assert zones[4]["lower_bpm"] == 170  # 100% LTHR
    assert zones[4]["upper_bpm"] == round(170 * 1.06)  # 180


def test_friel_zones_have_colors() -> None:
    """Jede Friel-Zone hat eine Farbe."""
    zones = calculate_friel_zones(165)
    for z in zones:
        assert z["color"].startswith("#")


def test_friel_zone_distribution() -> None:
    """Zonenverteilung mit LTHR bevorzugt Friel-Modell."""
    from app.services.hr_zone_calculator import calculate_zone_distribution

    hr_values = [130, 145, 155, 165, 175]
    result = calculate_zone_distribution(hr_values, lthr=170)
    assert len(result) == 5
    # Friel-Zonennamen statt Karvonen
    assert "zone_1_recovery" in result
    assert "zone_2_aerobic" in result
    assert "zone_3_tempo" in result
    assert "zone_4_sub_threshold" in result
    assert "zone_5_supra_threshold" in result


def test_friel_takes_precedence_over_karvonen() -> None:
    """LTHR hat Vorrang vor Karvonen wenn beides vorhanden."""
    from app.services.hr_zone_calculator import calculate_zone_distribution

    hr_values = [130, 145, 155, 165, 175]
    # Beide Parameter gesetzt — Friel soll gewinnen
    result = calculate_zone_distribution(hr_values, resting_hr=50, max_hr=190, lthr=170)
    assert "zone_2_aerobic" in result  # Friel-Name, nicht "base"


# --- Integration Tests: Threshold Test API ---


class TestThresholdTestAPI:
    """Integration tests for threshold test endpoints."""

    async def test_list_empty(self, client: AsyncClient) -> None:
        """GET /threshold-tests gibt leere Liste wenn keine Tests."""
        response = await client.get("/api/v1/threshold-tests")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["tests"] == []

    async def test_latest_not_found(self, client: AsyncClient) -> None:
        """GET /threshold-tests/latest gibt 404 ohne Tests."""
        response = await client.get("/api/v1/threshold-tests/latest")
        assert response.status_code == 404

    async def test_create_test(self, client: AsyncClient) -> None:
        """POST /threshold-tests erstellt einen Test mit Friel-Zonen."""
        response = await client.post(
            "/api/v1/threshold-tests",
            json={
                "test_date": "2026-03-15",
                "lthr": 170,
                "max_hr_measured": 192,
                "avg_pace_sec": 300.0,
                "notes": "Friel 30-Min-Test auf Bahn",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["lthr"] == 170
        assert data["max_hr_measured"] == 192
        assert data["avg_pace_sec"] == 300.0
        assert data["notes"] == "Friel 30-Min-Test auf Bahn"
        assert len(data["friel_zones"]) == 5

    async def test_create_updates_athlete_max_hr(self, client: AsyncClient) -> None:
        """Test mit höherer Max-HR aktualisiert Athletenprofil."""
        # Athlete mit max_hr=185
        await client.put(
            "/api/v1/athlete/settings",
            json={"max_hr": 185, "resting_hr": 50},
        )

        # Test mit max_hr=192 → soll Athlete aktualisieren
        await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-03-16", "lthr": 170, "max_hr_measured": 192},
        )

        settings = await client.get("/api/v1/athlete/settings")
        assert settings.json()["max_hr"] == 192

    async def test_create_does_not_lower_max_hr(self, client: AsyncClient) -> None:
        """Test mit niedrigerer Max-HR ändert Athletenprofil nicht."""
        await client.put(
            "/api/v1/athlete/settings",
            json={"max_hr": 195, "resting_hr": 50},
        )

        await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-03-17", "lthr": 168, "max_hr_measured": 188},
        )

        settings = await client.get("/api/v1/athlete/settings")
        assert settings.json()["max_hr"] == 195

    async def test_list_returns_chronological(self, client: AsyncClient) -> None:
        """Tests werden neueste zuerst zurückgegeben."""
        await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-01-15", "lthr": 165},
        )
        await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-03-15", "lthr": 170},
        )

        response = await client.get("/api/v1/threshold-tests")
        data = response.json()
        assert data["total"] == 2
        assert data["tests"][0]["lthr"] == 170  # neuester zuerst
        assert data["tests"][1]["lthr"] == 165

    async def test_latest_returns_most_recent(self, client: AsyncClient) -> None:
        """GET /latest gibt den neuesten Test."""
        await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-01-15", "lthr": 165},
        )
        await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-03-15", "lthr": 170},
        )

        response = await client.get("/api/v1/threshold-tests/latest")
        assert response.status_code == 200
        assert response.json()["lthr"] == 170

    async def test_delete_test(self, client: AsyncClient) -> None:
        """DELETE /threshold-tests/{id} löscht den Test."""
        create_resp = await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-03-15", "lthr": 170},
        )
        test_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/threshold-tests/{test_id}")
        assert response.status_code == 204

        # Verify deleted
        list_resp = await client.get("/api/v1/threshold-tests")
        assert list_resp.json()["total"] == 0

    async def test_delete_not_found(self, client: AsyncClient) -> None:
        """DELETE auf nicht-existenten Test gibt 404."""
        response = await client.delete("/api/v1/threshold-tests/99999")
        assert response.status_code == 404

    async def test_athlete_settings_show_lthr(self, client: AsyncClient) -> None:
        """Athlete-Settings zeigen LTHR und Friel-Zonen nach Test."""
        await client.put(
            "/api/v1/athlete/settings",
            json={"resting_hr": 50, "max_hr": 190},
        )
        await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-03-15", "lthr": 170},
        )

        response = await client.get("/api/v1/athlete/settings")
        data = response.json()
        assert data["lthr"] == 170
        assert data["zone_method"] == "friel"
        assert data["hr_zones"] is not None
        assert len(data["hr_zones"]) == 5
        # Karvonen-Zonen bleiben auch verfügbar
        assert data["karvonen_zones"] is not None

    async def test_athlete_settings_without_test_uses_karvonen(self, client: AsyncClient) -> None:
        """Ohne Test nutzt Athlete-Settings Karvonen-Zonen."""
        await client.put(
            "/api/v1/athlete/settings",
            json={"resting_hr": 50, "max_hr": 190},
        )

        response = await client.get("/api/v1/athlete/settings")
        data = response.json()
        assert data["lthr"] is None
        assert data["zone_method"] == "karvonen"
        assert data["hr_zones"] is not None

    @pytest.mark.parametrize(
        "lthr",
        [99, 221],
        ids=["too_low", "too_high"],
    )
    async def test_create_validates_lthr_range(self, client: AsyncClient, lthr: int) -> None:
        """LTHR außerhalb 100-220 wird abgelehnt."""
        response = await client.post(
            "/api/v1/threshold-tests",
            json={"test_date": "2026-03-15", "lthr": lthr},
        )
        assert response.status_code == 422
