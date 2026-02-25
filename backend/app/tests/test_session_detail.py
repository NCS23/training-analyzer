"""Tests fuer Session Detail View API (E01-S05)."""

import io

import pytest
from httpx import AsyncClient

# --- Test CSV Fixture ---

RUNNING_CSV = """\
date;timestamp;ISO8601;since_start;hr (count/min);cadence (count/min);distance (meter);speed (m/s);lap;latitude;longitude;elevation (meter)
2025-02-25;1740466800;2025-02-25T08:00:00;0;130;160;0;0;1;52,52;13,40;35
2025-02-25;1740466860;2025-02-25T08:01:00;60;135;162;180;3,0;1;52,52;13,40;35
2025-02-25;1740466920;2025-02-25T08:02:00;120;138;164;360;3,0;1;52,52;13,40;36
2025-02-25;1740466980;2025-02-25T08:03:00;180;140;165;540;3,0;1;52,52;13,40;36
2025-02-25;1740467040;2025-02-25T08:04:00;240;142;166;720;3,0;1;52,52;13,41;36
2025-02-25;1740467100;2025-02-25T08:05:00;300;145;168;900;3,0;2;52,52;13,41;37
2025-02-25;1740467160;2025-02-25T08:06:00;360;150;170;1100;3,33;2;52,52;13,41;37
2025-02-25;1740467220;2025-02-25T08:07:00;420;155;172;1300;3,33;2;52,52;13,41;37
2025-02-25;1740467280;2025-02-25T08:08:00;480;152;170;1500;3,33;2;52,52;13,41;38
2025-02-25;1740467340;2025-02-25T08:09:00;540;148;168;1700;3,33;2;52,52;13,42;38
"""


def _upload_csv(csv_content: str = RUNNING_CSV) -> dict:
    return {
        "csv_file": ("training.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }


async def _create_session(client: AsyncClient, notes: str | None = None) -> int:
    """Erstellt eine Session und gibt die ID zurueck."""
    data = {
        "training_date": "2025-02-25",
        "training_type": "running",
    }
    if notes:
        data["notes"] = notes
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_upload_csv(),
        data=data,
    )
    assert response.status_code == 201
    session_id = response.json()["session_id"]
    assert session_id is not None
    return session_id


# --- GET /sessions/{id} Tests ---


@pytest.mark.anyio
async def test_get_session_returns_full_data(client: AsyncClient) -> None:
    """GET liefert vollstaendige Session-Daten."""
    session_id = await _create_session(client, notes="Testnotiz")

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200

    session = response.json()
    assert session["id"] == session_id
    assert session["date"] == "2025-02-25"
    assert session["workout_type"] == "running"
    assert session["notes"] == "Testnotiz"
    assert session["duration_sec"] is not None
    assert session["created_at"] is not None
    assert session["updated_at"] is not None


@pytest.mark.anyio
async def test_get_session_includes_laps(client: AsyncClient) -> None:
    """GET liefert Laps mit allen Feldern."""
    session_id = await _create_session(client)

    response = await client.get(f"/api/v1/sessions/{session_id}")
    session = response.json()

    assert session["laps"] is not None
    assert len(session["laps"]) > 0

    lap = session["laps"][0]
    assert "lap_number" in lap
    assert "duration_formatted" in lap
    assert "duration_seconds" in lap


@pytest.mark.anyio
async def test_get_session_includes_hr_zones(client: AsyncClient) -> None:
    """GET liefert HR-Zonen Verteilung."""
    session_id = await _create_session(client)

    response = await client.get(f"/api/v1/sessions/{session_id}")
    session = response.json()

    assert session["hr_zones"] is not None
    # Sollte mindestens eine Zone haben
    assert len(session["hr_zones"]) > 0
    # Jede Zone hat percentage und label
    for zone in session["hr_zones"].values():
        assert "percentage" in zone
        assert "label" in zone


@pytest.mark.anyio
async def test_get_session_not_found(client: AsyncClient) -> None:
    """GET auf nicht-existierende Session gibt 404."""
    response = await client.get("/api/v1/sessions/99999")
    assert response.status_code == 404


# --- PATCH /sessions/{id}/notes Tests ---


@pytest.mark.anyio
async def test_update_notes(client: AsyncClient) -> None:
    """PATCH aktualisiert Notizen."""
    session_id = await _create_session(client)

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/notes",
        json={"notes": "Neuer Notiztext"},
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Neuer Notiztext"


@pytest.mark.anyio
async def test_update_notes_persists(client: AsyncClient) -> None:
    """Notizen-Update bleibt nach GET erhalten."""
    session_id = await _create_session(client)

    await client.patch(
        f"/api/v1/sessions/{session_id}/notes",
        json={"notes": "Persistierte Notiz"},
    )

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.json()["notes"] == "Persistierte Notiz"


@pytest.mark.anyio
async def test_update_notes_to_null(client: AsyncClient) -> None:
    """Notizen koennen geloescht werden (null)."""
    session_id = await _create_session(client, notes="Alte Notiz")

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/notes",
        json={"notes": None},
    )
    assert response.status_code == 200
    assert response.json()["notes"] is None


@pytest.mark.anyio
async def test_update_notes_not_found(client: AsyncClient) -> None:
    """PATCH auf nicht-existierende Session gibt 404."""
    response = await client.patch(
        "/api/v1/sessions/99999/notes",
        json={"notes": "Test"},
    )
    assert response.status_code == 404


# --- DELETE /sessions/{id} Tests ---


@pytest.mark.anyio
async def test_delete_session(client: AsyncClient) -> None:
    """DELETE loescht die Session."""
    session_id = await _create_session(client)

    response = await client.delete(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_session_not_found(client: AsyncClient) -> None:
    """DELETE auf nicht-existierende Session gibt 404."""
    response = await client.delete("/api/v1/sessions/99999")
    assert response.status_code == 404


# --- Session List nach Delete ---


@pytest.mark.anyio
async def test_deleted_session_not_in_list(client: AsyncClient) -> None:
    """Geloeschte Session erscheint nicht mehr in der Liste."""
    session_id = await _create_session(client)

    await client.delete(f"/api/v1/sessions/{session_id}")

    response = await client.get("/api/v1/sessions")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    session_ids = [s["id"] for s in sessions]
    assert session_id not in session_ids
