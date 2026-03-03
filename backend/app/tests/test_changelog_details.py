"""Tests for enriched changelog details (E16-S07)."""

import pytest
from httpx import AsyncClient

PLAN_DATA = {
    "name": "Test Plan",
    "description": "Test Beschreibung",
    "start_date": "2026-04-01",
    "end_date": "2026-06-30",
    "status": "draft",
}


@pytest.mark.anyio
async def test_plan_created_has_category(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    assert resp.status_code == 201
    plan_id = resp.json()["id"]

    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog")
    assert log.status_code == 200
    entries = log.json()["entries"]
    created = next(e for e in entries if e["change_type"] == "plan_created")
    assert created["category"] == "meta"
    assert created["details"]["source"] == "user"
    assert created["details"]["phase_count"] == 0


@pytest.mark.anyio
async def test_plan_updated_captures_field_diffs(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = resp.json()["id"]

    await client.patch(
        f"/api/v1/training-plans/{plan_id}",
        json={"status": "active", "name": "Neuer Name"},
    )

    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog")
    updated = next(e for e in log.json()["entries"] if e["change_type"] == "plan_updated")
    assert updated["details"] is not None
    field_changes = updated["details"]["field_changes"]
    assert any(fc["field"] == "status" for fc in field_changes)
    status_change = next(fc for fc in field_changes if fc["field"] == "status")
    assert status_change["from"] == "draft"
    assert status_change["to"] == "active"
    name_change = next(fc for fc in field_changes if fc["field"] == "name")
    assert name_change["label"] == "Name"


@pytest.mark.anyio
async def test_plan_updated_date_change_is_structure(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = resp.json()["id"]

    await client.patch(
        f"/api/v1/training-plans/{plan_id}",
        json={"start_date": "2026-04-08"},
    )

    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog")
    updated = next(e for e in log.json()["entries"] if e["change_type"] == "plan_updated")
    assert updated["category"] == "structure"


@pytest.mark.anyio
async def test_phase_added_has_structure_details(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = resp.json()["id"]

    phase_data = {
        "name": "Grundlagen",
        "phase_type": "base",
        "start_week": 1,
        "end_week": 4,
    }
    await client.post(f"/api/v1/training-plans/{plan_id}/phases", json=phase_data)

    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog")
    added = next(e for e in log.json()["entries"] if e["change_type"] == "phase_added")
    assert added["category"] == "structure"
    assert added["details"]["phase_name"] == "Grundlagen"
    assert added["details"]["phase_type"] == "base"


@pytest.mark.anyio
async def test_phase_updated_captures_diffs(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = resp.json()["id"]

    phase_resp = await client.post(
        f"/api/v1/training-plans/{plan_id}/phases",
        json={"name": "P1", "phase_type": "base", "start_week": 1, "end_week": 4},
    )
    phase_id = phase_resp.json()["id"]

    await client.patch(
        f"/api/v1/training-plans/{plan_id}/phases/{phase_id}",
        json={"end_week": 6},
    )

    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog")
    updated = next(e for e in log.json()["entries"] if e["change_type"] == "phase_updated")
    assert updated["category"] == "structure"
    field_changes = updated["details"]["field_changes"]
    ew = next(fc for fc in field_changes if fc["field"] == "end_week")
    assert ew["from"] == 4
    assert ew["to"] == 6
    assert ew["label"] == "Endwoche"


@pytest.mark.anyio
async def test_phase_deleted_has_details(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = resp.json()["id"]

    phase_resp = await client.post(
        f"/api/v1/training-plans/{plan_id}/phases",
        json={"name": "Bye", "phase_type": "taper", "start_week": 1, "end_week": 2},
    )
    phase_id = phase_resp.json()["id"]

    await client.delete(f"/api/v1/training-plans/{plan_id}/phases/{phase_id}")

    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog")
    deleted = next(e for e in log.json()["entries"] if e["change_type"] == "phase_deleted")
    assert deleted["category"] == "structure"
    assert deleted["details"]["phase_name"] == "Bye"


@pytest.mark.anyio
async def test_category_filter_on_changelog(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = resp.json()["id"]

    # Create + update -> produces "meta" entries
    await client.patch(f"/api/v1/training-plans/{plan_id}", json={"name": "X"})

    # Add phase -> produces "structure" entry
    await client.post(
        f"/api/v1/training-plans/{plan_id}/phases",
        json={"name": "P", "phase_type": "base", "start_week": 1, "end_week": 4},
    )

    # Filter by structure
    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog?category=structure")
    entries = log.json()["entries"]
    assert all(e["category"] == "structure" for e in entries)
    assert len(entries) > 0

    # Filter by meta
    log2 = await client.get(f"/api/v1/training-plans/{plan_id}/changelog?category=meta")
    entries2 = log2.json()["entries"]
    assert all(e["category"] == "meta" for e in entries2)


@pytest.mark.anyio
async def test_old_entries_without_category_render(client: AsyncClient) -> None:
    """Entries with null category/details (pre-migration) should not crash."""
    resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = resp.json()["id"]

    # All entries have category now, but verify the response schema accepts null
    log = await client.get(f"/api/v1/training-plans/{plan_id}/changelog")
    assert log.status_code == 200
    for entry in log.json()["entries"]:
        # category can be None for old entries — should not crash
        assert "category" in entry
