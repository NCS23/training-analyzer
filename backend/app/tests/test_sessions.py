"""Integration tests fuer Session API (E01-S01)."""

import io

import pytest
from httpx import AsyncClient

# Apple Watch CSV Format: Semikolon-getrennt, Komma-Dezimaltrennzeichen
RUNNING_CSV = """\
date;timestamp;ISO8601;since_start;hr (count/min);cadence (count/min);distance (meter);speed (m/s);lap;latitude;longitude;elevation (meter)
2024-03-15;1710488400;2024-03-15T07:00:00;0;120;160;0;0;1;52,52;13,40;35
2024-03-15;1710488460;2024-03-15T07:01:00;60;130;162;180;3,0;1;52,52;13,40;35
2024-03-15;1710488520;2024-03-15T07:02:00;120;135;164;360;3,0;1;52,52;13,40;36
2024-03-15;1710488580;2024-03-15T07:03:00;180;138;165;540;3,0;1;52,52;13,40;36
2024-03-15;1710488640;2024-03-15T07:04:00;240;140;166;720;3,0;1;52,52;13,40;36
2024-03-15;1710488700;2024-03-15T07:05:00;300;142;168;900;3,0;1;52,52;13,41;37
2024-03-15;1710488760;2024-03-15T07:06:00;360;165;178;1100;3,33;2;52,52;13,41;37
2024-03-15;1710488820;2024-03-15T07:07:00;420;170;180;1300;3,33;2;52,52;13,41;37
2024-03-15;1710488880;2024-03-15T07:08:00;480;175;182;1500;3,33;2;52,52;13,41;38
2024-03-15;1710488940;2024-03-15T07:09:00;540;172;180;1700;3,33;2;52,52;13,41;38
2024-03-15;1710489000;2024-03-15T07:10:00;600;168;178;1900;3,33;2;52,52;13,42;38
2024-03-15;1710489060;2024-03-15T07:11:00;660;140;162;2050;2,5;3;52,52;13,42;38
2024-03-15;1710489120;2024-03-15T07:12:00;720;135;160;2200;2,5;3;52,52;13,42;37
2024-03-15;1710489180;2024-03-15T07:13:00;780;130;158;2350;2,5;3;52,52;13,42;37
2024-03-15;1710489240;2024-03-15T07:14:00;840;125;155;2500;2,5;3;52,52;13,42;36
"""

STRENGTH_CSV = """\
date;timestamp;ISO8601;since_start;hr (count/min)
2024-03-16;1710576000;2024-03-16T07:00:00;0;80
2024-03-16;1710576010;2024-03-16T07:00:10;10;85
2024-03-16;1710576020;2024-03-16T07:00:20;20;95
2024-03-16;1710576030;2024-03-16T07:00:30;30;110
2024-03-16;1710576040;2024-03-16T07:00:40;40;125
2024-03-16;1710576050;2024-03-16T07:00:50;50;130
2024-03-16;1710576060;2024-03-16T07:01:00;60;140
2024-03-16;1710576070;2024-03-16T07:01:10;70;145
2024-03-16;1710576080;2024-03-16T07:01:20;80;135
2024-03-16;1710576090;2024-03-16T07:01:30;90;130
"""

INVALID_CSV = """\
name;age;city
Alice;30;Berlin
Bob;25;Hamburg
"""


def _make_csv_upload(csv_content: str, filename: str = "training.csv") -> dict:
    """Erstellt Upload-Daten fuer den Test."""
    return {
        "csv_file": (filename, io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }


# --- Upload Tests ---


@pytest.mark.anyio
async def test_upload_running_csv(client: AsyncClient) -> None:
    """Upload einer Lauf-CSV erstellt Session in DB."""
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV),
        data={
            "training_date": "2024-03-15",
            "training_type": "running",
            "training_subtype": "interval",
            "notes": "Gutes Training",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["session_id"] is not None
    assert body["data"]["laps"] is not None
    assert body["data"]["summary"] is not None
    assert body["data"]["hr_zones"] is not None


@pytest.mark.anyio
async def test_upload_strength_csv(client: AsyncClient) -> None:
    """Upload einer Kraft-CSV erstellt Session in DB."""
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(STRENGTH_CSV),
        data={
            "training_date": "2024-03-16",
            "training_type": "strength",
            "training_subtype": "knee_dominant",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["session_id"] is not None
    assert body["data"]["summary"] is not None


@pytest.mark.anyio
async def test_upload_invalid_csv_format(client: AsyncClient) -> None:
    """CSV mit falschen Spalten gibt Fehler zurueck."""
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(INVALID_CSV),
        data={
            "training_date": "2024-03-15",
            "training_type": "running",
        },
    )
    assert response.status_code == 201  # Parser gibt success=False zurueck, kein HTTP-Fehler
    body = response.json()
    assert body["success"] is False
    assert body["errors"] is not None
    assert len(body["errors"]) > 0


@pytest.mark.anyio
async def test_upload_non_csv_file(client: AsyncClient) -> None:
    """Nicht-CSV-Datei wird abgelehnt."""
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files={
            "csv_file": (
                "training.txt",
                io.BytesIO(b"hello world"),
                "text/plain",
            )
        },
        data={
            "training_date": "2024-03-15",
            "training_type": "running",
        },
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_upload_empty_csv(client: AsyncClient) -> None:
    """Leere CSV-Datei wird abgelehnt."""
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files={
            "csv_file": ("empty.csv", io.BytesIO(b""), "text/csv"),
        },
        data={
            "training_date": "2024-03-15",
            "training_type": "running",
        },
    )
    assert response.status_code == 400


# --- List/Get/Delete Tests ---


@pytest.mark.anyio
async def test_list_sessions_empty(client: AsyncClient) -> None:
    """Leere DB gibt leere Liste zurueck."""
    response = await client.get("/api/v1/sessions")
    assert response.status_code == 200
    body = response.json()
    assert body["sessions"] == []
    assert body["total"] == 0


@pytest.mark.anyio
async def test_list_sessions_after_upload(client: AsyncClient) -> None:
    """Nach Upload erscheint Session in der Liste."""
    # Upload
    await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV),
        data={"training_date": "2024-03-15", "training_type": "running"},
    )
    # List
    response = await client.get("/api/v1/sessions")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["sessions"][0]["workout_type"] == "running"


@pytest.mark.anyio
async def test_list_sessions_filter_by_type(client: AsyncClient) -> None:
    """Filter nach Trainingstyp funktioniert."""
    # Upload running
    await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV),
        data={"training_date": "2024-03-15", "training_type": "running"},
    )
    # Upload strength
    await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(STRENGTH_CSV),
        data={"training_date": "2024-03-16", "training_type": "strength"},
    )
    # Filter running
    response = await client.get("/api/v1/sessions?workout_type=running")
    body = response.json()
    assert body["total"] == 1
    assert body["sessions"][0]["workout_type"] == "running"

    # Filter strength
    response = await client.get("/api/v1/sessions?workout_type=strength")
    body = response.json()
    assert body["total"] == 1
    assert body["sessions"][0]["workout_type"] == "strength"


@pytest.mark.anyio
async def test_get_session_detail(client: AsyncClient) -> None:
    """Session-Detail enthaelt Laps und HR-Zonen."""
    upload = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV),
        data={
            "training_date": "2024-03-15",
            "training_type": "running",
            "training_subtype": "interval",
        },
    )
    session_id = upload.json()["session_id"]

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == session_id
    assert body["workout_type"] == "running"
    assert body["subtype"] == "interval"
    assert body["laps"] is not None
    assert len(body["laps"]) > 0
    assert body["hr_zones"] is not None


@pytest.mark.anyio
async def test_get_session_not_found(client: AsyncClient) -> None:
    """Nicht existierende Session gibt 404."""
    response = await client.get("/api/v1/sessions/9999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_session(client: AsyncClient) -> None:
    """Session kann geloescht werden."""
    upload = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV),
        data={"training_date": "2024-03-15", "training_type": "running"},
    )
    session_id = upload.json()["session_id"]

    # Delete
    response = await client.delete(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_session_not_found(client: AsyncClient) -> None:
    """Loeschen nicht existierender Session gibt 404."""
    response = await client.delete("/api/v1/sessions/9999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_upload_persists_notes(client: AsyncClient) -> None:
    """Notizen werden korrekt gespeichert."""
    upload = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV),
        data={
            "training_date": "2024-03-15",
            "training_type": "running",
            "notes": "Beine schwer, aber gutes Tempo",
        },
    )
    session_id = upload.json()["session_id"]

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.json()["notes"] == "Beine schwer, aber gutes Tempo"


@pytest.mark.anyio
async def test_pagination(client: AsyncClient) -> None:
    """Paginierung funktioniert korrekt."""
    # Upload 3 sessions
    for i in range(3):
        await client.post(
            "/api/v1/sessions/upload/csv",
            files=_make_csv_upload(RUNNING_CSV),
            data={"training_date": f"2024-03-{15 + i}", "training_type": "running"},
        )

    # Page 1, size 2
    response = await client.get("/api/v1/sessions?page=1&page_size=2")
    body = response.json()
    assert body["total"] == 3
    assert len(body["sessions"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2

    # Page 2, size 2
    response = await client.get("/api/v1/sessions?page=2&page_size=2")
    body = response.json()
    assert len(body["sessions"]) == 1


# --- Lap Override Tests (E01-S02) ---


async def _upload_running_session(client: AsyncClient) -> int:
    """Hilfsfunktion: Upload Running CSV, gibt session_id zurueck."""
    upload = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV),
        data={
            "training_date": "2024-03-15",
            "training_type": "running",
            "training_subtype": "interval",
        },
    )
    return upload.json()["session_id"]


@pytest.mark.anyio
async def test_patch_lap_overrides(client: AsyncClient) -> None:
    """Lap-Type Overrides werden gespeichert."""
    session_id = await _upload_running_session(client)

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/laps",
        json={
            "overrides": [
                {"lap_number": 1, "user_override": "warmup"},
                {"lap_number": 3, "user_override": "cooldown"},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    # Verify overrides in response
    laps = body["laps"]
    lap1 = next(lap for lap in laps if lap["lap_number"] == 1)
    lap3 = next(lap for lap in laps if lap["lap_number"] == 3)
    assert lap1["user_override"] == "warmup"
    assert lap3["user_override"] == "cooldown"


@pytest.mark.anyio
async def test_patch_lap_overrides_persisted(client: AsyncClient) -> None:
    """Lap-Overrides sind nach GET noch vorhanden."""
    session_id = await _upload_running_session(client)

    # Patch
    await client.patch(
        f"/api/v1/sessions/{session_id}/laps",
        json={"overrides": [{"lap_number": 2, "user_override": "interval"}]},
    )

    # Get session detail
    response = await client.get(f"/api/v1/sessions/{session_id}")
    body = response.json()
    lap2 = next(lap for lap in body["laps"] if lap["lap_number"] == 2)
    assert lap2["user_override"] == "interval"


@pytest.mark.anyio
async def test_patch_lap_overrides_returns_working_metrics(client: AsyncClient) -> None:
    """PATCH gibt Working-Laps Summary und HR-Zonen zurueck."""
    session_id = await _upload_running_session(client)

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/laps",
        json={
            "overrides": [
                {"lap_number": 1, "user_override": "warmup"},
                {"lap_number": 3, "user_override": "cooldown"},
            ]
        },
    )
    body = response.json()

    # Working metrics should exclude warmup (lap 1) and cooldown (lap 3)
    assert body["summary_working"] is not None
    assert body["summary_working"]["total_duration_seconds"] > 0
    assert body["hr_zones_working"] is not None
    assert "zone_1_recovery" in body["hr_zones_working"]


@pytest.mark.anyio
async def test_patch_lap_overrides_not_found(client: AsyncClient) -> None:
    """PATCH fuer nicht existierende Session gibt 404."""
    response = await client.patch(
        "/api/v1/sessions/9999/laps",
        json={"overrides": [{"lap_number": 1, "user_override": "warmup"}]},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_patch_lap_overrides_no_laps(client: AsyncClient) -> None:
    """PATCH fuer Session ohne Laps gibt 400."""
    # Upload strength CSV (hat keine Laps)
    upload = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(STRENGTH_CSV),
        data={
            "training_date": "2024-03-16",
            "training_type": "strength",
        },
    )
    session_id = upload.json()["session_id"]

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/laps",
        json={"overrides": [{"lap_number": 1, "user_override": "warmup"}]},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_patch_lap_overrides_working_excludes_warmup_cooldown(
    client: AsyncClient,
) -> None:
    """Working-Laps Metriken schliessen Warmup/Cooldown/Pause aus."""
    session_id = await _upload_running_session(client)

    # Get original detail to compare
    detail = await client.get(f"/api/v1/sessions/{session_id}")
    all_laps = detail.json()["laps"]
    total_duration_all = sum(lap["duration_seconds"] for lap in all_laps)

    # Override first as warmup, last as cooldown
    response = await client.patch(
        f"/api/v1/sessions/{session_id}/laps",
        json={
            "overrides": [
                {"lap_number": 1, "user_override": "warmup"},
                {"lap_number": 3, "user_override": "cooldown"},
            ]
        },
    )
    body = response.json()

    # Working duration should be less than total
    working_duration = body["summary_working"]["total_duration_seconds"]
    assert working_duration < total_duration_all
    assert working_duration > 0
