"""Tests fuer Training Type Classifier (E01-S04)."""

import io

import pytest
from httpx import AsyncClient

from app.services.training_type_classifier import (
    ClassifierThresholds,
    classify_training_type,
)

# --- Unit Tests: Klassifizierung pro Training Type ---


def test_recovery_short_low_hr() -> None:
    """Recovery: Kurze Session mit niedriger HR."""
    result = classify_training_type(
        duration_sec=30 * 60,  # 30 min
        hr_avg=120,
        hr_max=135,
        distance_km=5.0,
        laps=None,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 80.0, "seconds": 1440, "label": "< 150"},
            "zone_2_base": {"percentage": 15.0, "seconds": 270, "label": "150-160"},
            "zone_3_tempo": {"percentage": 5.0, "seconds": 90, "label": "> 160"},
        },
    )
    assert result.training_type == "recovery"
    assert result.confidence >= 60


def test_easy_run_moderate_hr() -> None:
    """Easy Run: Moderate Dauer (ueber Recovery-Grenze), niedrige Intensitaet."""
    result = classify_training_type(
        duration_sec=50 * 60,  # 50 min — ueber Recovery-Max von 45 min
        hr_avg=140,
        hr_max=155,
        distance_km=8.5,
        laps=None,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 60.0, "seconds": 1800, "label": "< 150"},
            "zone_2_base": {"percentage": 30.0, "seconds": 900, "label": "150-160"},
            "zone_3_tempo": {"percentage": 10.0, "seconds": 300, "label": "> 160"},
        },
    )
    assert result.training_type == "easy"
    assert result.confidence >= 40


def test_long_run_high_duration() -> None:
    """Long Run: Lange Dauer >= 75 min, niedrige Intensitaet."""
    result = classify_training_type(
        duration_sec=90 * 60,  # 90 min
        hr_avg=145,
        hr_max=165,
        distance_km=16.0,
        laps=_make_laps(9, avg_hr=145, pace=5.6),
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 50.0, "seconds": 2700, "label": "Recovery"},
            "zone_2_base": {"percentage": 35.0, "seconds": 1890, "label": "Base"},
            "zone_3_tempo": {"percentage": 12.0, "seconds": 648, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 3.0, "seconds": 162, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 0.0, "seconds": 0, "label": "VO2max"},
        },
    )
    assert result.training_type == "long_run"
    assert result.confidence >= 65


def test_tempo_consistent_pace_zone3() -> None:
    """Tempo: Hoher Zone 3 Anteil + konstante Pace."""
    laps = _make_laps(5, avg_hr=165, pace=4.5)
    result = classify_training_type(
        duration_sec=35 * 60,  # 35 min
        hr_avg=165,
        hr_max=175,
        distance_km=8.0,
        laps=laps,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 5.0, "seconds": 105, "label": "Recovery"},
            "zone_2_base": {"percentage": 10.0, "seconds": 210, "label": "Base"},
            "zone_3_tempo": {"percentage": 55.0, "seconds": 1155, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 25.0, "seconds": 525, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 5.0, "seconds": 105, "label": "VO2max"},
        },
    )
    assert result.training_type == "tempo"
    assert result.confidence >= 55


def test_intervals_varying_hr_multiple_laps() -> None:
    """Intervals: Mehrere Laps mit variierender HR (hoch/niedrig)."""
    laps = [
        {
            "lap_number": 1,
            "avg_hr_bpm": 130,
            "duration_seconds": 600,
            "pace_min_per_km": 6.0,
            "suggested_type": "warmup",
        },
        {
            "lap_number": 2,
            "avg_hr_bpm": 175,
            "duration_seconds": 240,
            "pace_min_per_km": 3.8,
            "suggested_type": "work",
        },
        {
            "lap_number": 3,
            "avg_hr_bpm": 140,
            "duration_seconds": 120,
            "pace_min_per_km": 7.0,
            "suggested_type": "rest",
        },
        {
            "lap_number": 4,
            "avg_hr_bpm": 178,
            "duration_seconds": 240,
            "pace_min_per_km": 3.7,
            "suggested_type": "work",
        },
        {
            "lap_number": 5,
            "avg_hr_bpm": 138,
            "duration_seconds": 120,
            "pace_min_per_km": 7.2,
            "suggested_type": "rest",
        },
        {
            "lap_number": 6,
            "avg_hr_bpm": 180,
            "duration_seconds": 240,
            "pace_min_per_km": 3.6,
            "suggested_type": "work",
        },
        {
            "lap_number": 7,
            "avg_hr_bpm": 130,
            "duration_seconds": 600,
            "pace_min_per_km": 6.5,
            "suggested_type": "cooldown",
        },
    ]
    result = classify_training_type(
        duration_sec=2160,
        hr_avg=155,
        hr_max=180,
        distance_km=8.0,
        laps=laps,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 30.0, "seconds": 648, "label": "Recovery"},
            "zone_2_base": {"percentage": 15.0, "seconds": 324, "label": "Base"},
            "zone_3_tempo": {"percentage": 15.0, "seconds": 324, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 30.0, "seconds": 648, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 10.0, "seconds": 216, "label": "VO2max"},
        },
    )
    assert result.training_type == "intervals"
    assert result.confidence >= 60


def test_race_high_intensity_throughout() -> None:
    """Race: Durchgehend hohe Intensitaet (Zone 4+)."""
    result = classify_training_type(
        duration_sec=25 * 60,  # 25 min (5K Race)
        hr_avg=182,
        hr_max=195,
        distance_km=5.0,
        laps=_make_laps(5, avg_hr=182, pace=5.0),
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 0.0, "seconds": 0, "label": "Recovery"},
            "zone_2_base": {"percentage": 0.0, "seconds": 0, "label": "Base"},
            "zone_3_tempo": {"percentage": 10.0, "seconds": 150, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 50.0, "seconds": 750, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 40.0, "seconds": 600, "label": "VO2max"},
        },
    )
    assert result.training_type == "race"
    assert result.confidence >= 70


# --- Edge Cases ---


def test_no_hr_data_defaults_easy() -> None:
    """Ohne HR-Daten → Fallback auf easy (basierend auf Dauer)."""
    result = classify_training_type(
        duration_sec=50 * 60,  # 50 min (ueber Recovery-Grenze)
        hr_avg=None,
        hr_max=None,
        distance_km=7.0,
        laps=None,
        hr_zone_distribution=None,
    )
    assert result.training_type == "easy"
    assert result.confidence >= 20  # Mindest-Konfidenz vorhanden


def test_short_session_no_laps() -> None:
    """Sehr kurze Session ohne Laps."""
    result = classify_training_type(
        duration_sec=10 * 60,  # 10 min
        hr_avg=130,
        hr_max=140,
        distance_km=1.5,
        laps=None,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 90.0, "seconds": 540, "label": "< 150"},
            "zone_2_base": {"percentage": 10.0, "seconds": 60, "label": "150-160"},
            "zone_3_tempo": {"percentage": 0.0, "seconds": 0, "label": "> 160"},
        },
    )
    assert result.training_type == "recovery"


def test_confidence_scoring_range() -> None:
    """Confidence Score ist immer 0-100."""
    for dur in [10, 30, 50, 80, 120]:
        result = classify_training_type(
            duration_sec=dur * 60,
            hr_avg=155,
            hr_max=175,
            distance_km=dur / 6.0,
            laps=_make_laps(max(1, dur // 10), avg_hr=155, pace=6.0),
            hr_zone_distribution={
                "zone_1_recovery": {"percentage": 30.0, "seconds": 100, "label": "Zone 1"},
                "zone_2_base": {"percentage": 30.0, "seconds": 100, "label": "Zone 2"},
                "zone_3_tempo": {"percentage": 30.0, "seconds": 100, "label": "Zone 3"},
                "zone_4_threshold": {"percentage": 10.0, "seconds": 33, "label": "Zone 4"},
            },
        )
        assert 0 <= result.confidence <= 100


def test_custom_thresholds() -> None:
    """Benutzerdefinierte Schwellenwerte ueberschreiben Defaults."""
    custom = ClassifierThresholds(long_run_min_duration_min=60)  # 60 statt 75
    result = classify_training_type(
        duration_sec=65 * 60,  # 65 min - unter Default, ueber Custom
        hr_avg=140,
        hr_max=155,
        distance_km=11.0,
        laps=None,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 55.0, "seconds": 2145, "label": "Recovery"},
            "zone_2_base": {"percentage": 35.0, "seconds": 1365, "label": "Base"},
            "zone_3_tempo": {"percentage": 8.0, "seconds": 312, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 2.0, "seconds": 78, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 0.0, "seconds": 0, "label": "VO2max"},
        },
        thresholds=custom,
    )
    assert result.training_type == "long_run"


def test_classification_has_reasons() -> None:
    """Klassifizierung liefert immer Begruendungen."""
    result = classify_training_type(
        duration_sec=30 * 60,
        hr_avg=130,
        hr_max=145,
        distance_km=5.0,
        laps=None,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 85.0, "seconds": 1530, "label": "Zone 1"},
            "zone_2_base": {"percentage": 10.0, "seconds": 180, "label": "Zone 2"},
            "zone_3_tempo": {"percentage": 5.0, "seconds": 90, "label": "Zone 3"},
        },
    )
    assert len(result.reasons) > 0


# --- Integration Tests: Training Type API ---


RUNNING_CSV_3LAPS = """\
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
2025-02-25;1740467400;2025-02-25T08:10:00;600;140;162;1900;2,5;3;52,52;13,42;38
2025-02-25;1740467460;2025-02-25T08:11:00;660;135;160;2050;2,5;3;52,52;13,42;37
2025-02-25;1740467520;2025-02-25T08:12:00;720;130;158;2200;2,5;3;52,52;13,42;37
2025-02-25;1740467580;2025-02-25T08:13:00;780;128;155;2350;2,5;3;52,52;13,42;36
2025-02-25;1740467640;2025-02-25T08:14:00;840;125;152;2500;2,5;3;52,52;13,42;36
"""


def _make_csv_upload(csv_content: str) -> dict:
    """Erstellt Upload-Daten fuer den Test."""
    return {
        "csv_file": ("training.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }


@pytest.mark.anyio
async def test_upload_returns_training_type(client: AsyncClient) -> None:
    """Upload liefert auto-klassifizierten Training Type."""
    response = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV_3LAPS),
        data={
            "training_date": "2025-02-25",
            "training_type": "running",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"]
    assert data["metadata"]["training_type_auto"] is not None
    assert data["metadata"]["training_type_confidence"] is not None


@pytest.mark.anyio
async def test_session_response_includes_training_type(client: AsyncClient) -> None:
    """GET Session enthaelt training_type Info."""
    upload_resp = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV_3LAPS),
        data={
            "training_date": "2025-02-25",
            "training_type": "running",
        },
    )
    session_id = upload_resp.json()["session_id"]
    assert session_id is not None

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    session = response.json()
    assert session["training_type"] is not None
    assert session["training_type"]["auto"] is not None
    assert session["training_type"]["effective"] is not None
    assert session["training_type"]["override"] is None


@pytest.mark.anyio
async def test_training_type_override(client: AsyncClient) -> None:
    """PATCH setzt manuellen Training Type Override."""
    upload_resp = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV_3LAPS),
        data={
            "training_date": "2025-02-25",
            "training_type": "running",
        },
    )
    session_id = upload_resp.json()["session_id"]
    assert session_id is not None

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/training-type",
        json={"training_type": "tempo"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["training_type"]["override"] == "tempo"
    assert data["training_type"]["effective"] == "tempo"
    assert data["training_type"]["auto"] is not None


@pytest.mark.anyio
async def test_training_type_override_persists(client: AsyncClient) -> None:
    """Override bleibt nach erneutem GET erhalten."""
    upload_resp = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV_3LAPS),
        data={
            "training_date": "2025-02-25",
            "training_type": "running",
        },
    )
    session_id = upload_resp.json()["session_id"]
    assert session_id is not None

    await client.patch(
        f"/api/v1/sessions/{session_id}/training-type",
        json={"training_type": "intervals"},
    )

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.json()["training_type"]["override"] == "intervals"
    assert response.json()["training_type"]["effective"] == "intervals"


@pytest.mark.anyio
async def test_training_type_override_invalid_type(client: AsyncClient) -> None:
    """PATCH mit ungueltigem Typ gibt 400."""
    upload_resp = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV_3LAPS),
        data={
            "training_date": "2025-02-25",
            "training_type": "running",
        },
    )
    session_id = upload_resp.json()["session_id"]
    assert session_id is not None

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/training-type",
        json={"training_type": "invalid_type"},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_training_type_override_not_found(client: AsyncClient) -> None:
    """PATCH auf nicht-existierende Session gibt 404."""
    response = await client.patch(
        "/api/v1/sessions/99999/training-type",
        json={"training_type": "easy"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_sessions_includes_training_type(client: AsyncClient) -> None:
    """Session-Liste enthaelt training_type Info."""
    await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(RUNNING_CSV_3LAPS),
        data={
            "training_date": "2025-02-25",
            "training_type": "running",
        },
    )

    response = await client.get("/api/v1/sessions")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) >= 1
    assert sessions[0]["training_type"] is not None
    assert sessions[0]["training_type"]["effective"] is not None


@pytest.mark.anyio
async def test_strength_session_no_training_type(client: AsyncClient) -> None:
    """Kraft-Sessions bekommen keinen Training Type (nur Running)."""
    strength_csv = """\
date;timestamp;ISO8601;since_start;hr (count/min)
2025-02-25;1740466800;2025-02-25T08:00:00;0;80
2025-02-25;1740466810;2025-02-25T08:00:10;10;85
2025-02-25;1740466820;2025-02-25T08:00:20;20;95
2025-02-25;1740466830;2025-02-25T08:00:30;30;110
2025-02-25;1740466840;2025-02-25T08:00:40;40;125
"""
    upload_resp = await client.post(
        "/api/v1/sessions/upload/csv",
        files=_make_csv_upload(strength_csv),
        data={
            "training_date": "2025-02-25",
            "training_type": "strength",
        },
    )
    session_id = upload_resp.json()["session_id"]
    assert session_id is not None

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["training_type"] is None


# --- New Session Type Tests ---


def test_progression_decreasing_pace() -> None:
    """Progression: Pace nimmt ueber die Laps systematisch ab."""
    laps = [
        {"lap_number": 1, "avg_hr_bpm": 140, "duration_seconds": 600, "pace_min_per_km": 6.0, "suggested_type": "steady"},
        {"lap_number": 2, "avg_hr_bpm": 145, "duration_seconds": 600, "pace_min_per_km": 5.7, "suggested_type": "steady"},
        {"lap_number": 3, "avg_hr_bpm": 152, "duration_seconds": 600, "pace_min_per_km": 5.3, "suggested_type": "steady"},
        {"lap_number": 4, "avg_hr_bpm": 158, "duration_seconds": 600, "pace_min_per_km": 5.0, "suggested_type": "steady"},
        {"lap_number": 5, "avg_hr_bpm": 165, "duration_seconds": 600, "pace_min_per_km": 4.6, "suggested_type": "steady"},
        {"lap_number": 6, "avg_hr_bpm": 170, "duration_seconds": 600, "pace_min_per_km": 4.3, "suggested_type": "steady"},
    ]
    result = classify_training_type(
        duration_sec=60 * 60,
        hr_avg=155,
        hr_max=170,
        distance_km=12.0,
        laps=laps,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 15.0, "seconds": 540, "label": "Recovery"},
            "zone_2_base": {"percentage": 30.0, "seconds": 1080, "label": "Base"},
            "zone_3_tempo": {"percentage": 35.0, "seconds": 1260, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 20.0, "seconds": 720, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 0.0, "seconds": 0, "label": "VO2max"},
        },
    )
    assert result.training_type == "progression"
    assert result.confidence >= 65


def test_fartlek_mixed_pace() -> None:
    """Fartlek: Gemischte Pace mit moderater HR-Variabilitaet.

    Key constraints for triggering fartlek and not other types:
    - Pace CV ~0.12 (within 0.10-0.30 fartlek range)
    - HR below 160 to avoid interval checker's high-HR heuristic
    - HR CV ~0.06 (within 0.05-0.12 fartlek range)
    - Non-progressive pace pattern (both halves have similar avg)
    """
    laps = [
        {"lap_number": 1, "avg_hr_bpm": 135, "duration_seconds": 300, "pace_min_per_km": 5.5, "suggested_type": "steady"},
        {"lap_number": 2, "avg_hr_bpm": 158, "duration_seconds": 240, "pace_min_per_km": 4.3, "suggested_type": "steady"},
        {"lap_number": 3, "avg_hr_bpm": 145, "duration_seconds": 280, "pace_min_per_km": 4.8, "suggested_type": "steady"},
        {"lap_number": 4, "avg_hr_bpm": 138, "duration_seconds": 300, "pace_min_per_km": 5.6, "suggested_type": "steady"},
        {"lap_number": 5, "avg_hr_bpm": 157, "duration_seconds": 240, "pace_min_per_km": 4.1, "suggested_type": "steady"},
        {"lap_number": 6, "avg_hr_bpm": 142, "duration_seconds": 280, "pace_min_per_km": 5.2, "suggested_type": "steady"},
    ]
    result = classify_training_type(
        duration_sec=27 * 60,
        hr_avg=146,
        hr_max=158,
        distance_km=5.5,
        laps=laps,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 25.0, "seconds": 405, "label": "Recovery"},
            "zone_2_base": {"percentage": 35.0, "seconds": 567, "label": "Base"},
            "zone_3_tempo": {"percentage": 30.0, "seconds": 486, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 10.0, "seconds": 162, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 0.0, "seconds": 0, "label": "VO2max"},
        },
    )
    assert result.training_type == "fartlek"
    assert result.confidence >= 50


def test_repetitions_short_fast_laps() -> None:
    """Repetitions: Kurze, schnelle Wiederholungen mit hoher HR."""
    laps = [
        {"lap_number": 1, "avg_hr_bpm": 130, "duration_seconds": 600, "pace_min_per_km": 6.0, "suggested_type": "warmup"},
        {"lap_number": 2, "avg_hr_bpm": 175, "duration_seconds": 60, "pace_min_per_km": 3.2, "suggested_type": "work"},
        {"lap_number": 3, "avg_hr_bpm": 140, "duration_seconds": 90, "pace_min_per_km": 7.0, "suggested_type": "rest"},
        {"lap_number": 4, "avg_hr_bpm": 178, "duration_seconds": 55, "pace_min_per_km": 3.1, "suggested_type": "work"},
        {"lap_number": 5, "avg_hr_bpm": 138, "duration_seconds": 90, "pace_min_per_km": 7.0, "suggested_type": "rest"},
        {"lap_number": 6, "avg_hr_bpm": 180, "duration_seconds": 58, "pace_min_per_km": 3.0, "suggested_type": "work"},
        {"lap_number": 7, "avg_hr_bpm": 135, "duration_seconds": 90, "pace_min_per_km": 7.0, "suggested_type": "rest"},
        {"lap_number": 8, "avg_hr_bpm": 176, "duration_seconds": 62, "pace_min_per_km": 3.3, "suggested_type": "work"},
        {"lap_number": 9, "avg_hr_bpm": 130, "duration_seconds": 600, "pace_min_per_km": 6.5, "suggested_type": "cooldown"},
    ]
    result = classify_training_type(
        duration_sec=1705,
        hr_avg=155,
        hr_max=180,
        distance_km=4.0,
        laps=laps,
        hr_zone_distribution={
            "zone_1_recovery": {"percentage": 40.0, "seconds": 682, "label": "Recovery"},
            "zone_2_base": {"percentage": 15.0, "seconds": 256, "label": "Base"},
            "zone_3_tempo": {"percentage": 10.0, "seconds": 171, "label": "Tempo"},
            "zone_4_threshold": {"percentage": 25.0, "seconds": 426, "label": "Threshold"},
            "zone_5_vo2max": {"percentage": 10.0, "seconds": 171, "label": "VO2max"},
        },
    )
    assert result.training_type == "repetitions"
    assert result.confidence >= 60


# --- Helpers ---


def _make_laps(count: int, avg_hr: int = 150, pace: float = 5.5, duration: int = 600) -> list[dict]:
    """Erstellt einfache Lap-Daten fuer Tests."""
    return [
        {
            "lap_number": i + 1,
            "avg_hr_bpm": avg_hr,
            "duration_seconds": duration,
            "pace_min_per_km": pace,
            "distance_km": round(duration / 60 / pace, 2),
            "suggested_type": "steady",
        }
        for i in range(count)
    ]
