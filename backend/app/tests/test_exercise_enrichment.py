"""Tests für Exercise Enrichment Service."""

import json
from unittest.mock import patch

from httpx import AsyncClient

from app.services.exercise_enrichment import (
    EXERCISE_DB_MAPPING,
    enrich_exercise_model,
    find_exercise_db_match,
    get_enrichment_data,
    load_exercise_db,
)


class TestExerciseEnrichmentUnit:
    """Unit tests for enrichment functions."""

    def test_load_exercise_db(self) -> None:
        """Exercise DB loads and contains entries."""
        db = load_exercise_db()
        assert len(db) > 800
        # Check a known entry
        assert "Pushups" in db
        assert db["Pushups"]["name"] == "Pushups"

    def test_all_mappings_exist_in_db(self) -> None:
        """Every German mapping points to a valid exercise_db entry."""
        db = load_exercise_db()
        for german_name, db_id in EXERCISE_DB_MAPPING.items():
            assert db_id in db, f"Mapping '{german_name}' -> '{db_id}' not found in DB"

    def test_get_enrichment_data_known_exercise(self) -> None:
        """Known exercise returns full enrichment data."""
        data = get_enrichment_data("Bankdrücken")
        assert data is not None
        assert data["exercise_db_id"] == "Barbell_Bench_Press_-_Medium_Grip"
        assert isinstance(data["instructions"], list)
        assert len(data["instructions"]) > 0
        assert isinstance(data["primary_muscles"], list)
        assert "chest" in data["primary_muscles"]
        assert isinstance(data["image_urls"], list)
        assert len(data["image_urls"]) == 2
        assert data["equipment"] is not None

    def test_get_enrichment_data_unknown_exercise(self) -> None:
        """Unknown exercise returns None."""
        data = get_enrichment_data("Nonexistent Exercise 12345")
        assert data is None

    def test_enrich_exercise_model_returns_db_ready_values(self) -> None:
        """enrich_exercise_model returns JSON-serialized column values."""
        result = enrich_exercise_model("Kniebeugen")
        assert result is not None
        assert result["exercise_db_id"] == "Barbell_Squat"

        # Verify JSON fields are valid JSON strings
        instructions_raw = result["instructions_json"]
        assert instructions_raw is not None
        instructions = json.loads(instructions_raw)
        assert isinstance(instructions, list)
        assert len(instructions) > 0

        primary_raw = result["primary_muscles_json"]
        assert primary_raw is not None
        primary = json.loads(primary_raw)
        assert isinstance(primary, list)
        assert "quadriceps" in primary

    def test_find_exercise_db_match_explicit_mapping(self) -> None:
        """Explicit mapping is found first."""
        match = find_exercise_db_match("Liegestütze")
        assert match == "Pushups"

    def test_find_exercise_db_match_exact_english_name(self) -> None:
        """Exact English name match works."""
        match = find_exercise_db_match("Pushups")
        assert match == "Pushups"

    def test_find_exercise_db_match_partial(self) -> None:
        """Partial name match works as fallback."""
        match = find_exercise_db_match("Bench Press")
        assert match is not None
        assert "Bench_Press" in match

    def test_find_exercise_db_match_no_match(self) -> None:
        """Completely unknown name returns None."""
        match = find_exercise_db_match("Xyz Nonexistent 12345")
        assert match is None

    def test_all_31_exercises_have_instructions(self) -> None:
        """All 31 default exercises have instructions from the DB."""
        for german_name in EXERCISE_DB_MAPPING:
            data = get_enrichment_data(german_name)
            assert data is not None, f"No enrichment for {german_name}"
            assert len(data["instructions"]) > 0, f"No instructions for {german_name}"

    def test_instructions_are_in_german(self) -> None:
        """Instructions should be in German, not English."""
        data = get_enrichment_data("Bankdrücken")
        assert data is not None
        first_instruction = data["instructions"][0]
        # German text should contain typical German words/characters
        assert "Lege" in first_instruction or "dich" in first_instruction
        # Should NOT contain English
        assert "Lie back" not in first_instruction

    def test_all_31_exercises_have_muscles(self) -> None:
        """All 31 default exercises have at least primary muscles."""
        for german_name in EXERCISE_DB_MAPPING:
            data = get_enrichment_data(german_name)
            assert data is not None, f"No enrichment for {german_name}"
            assert len(data["primary_muscles"]) > 0, f"No muscles for {german_name}"

    def test_all_31_exercises_have_images(self) -> None:
        """All 31 default exercises have 2 images downloaded."""
        for german_name in EXERCISE_DB_MAPPING:
            data = get_enrichment_data(german_name)
            assert data is not None, f"No enrichment for {german_name}"
            assert len(data["image_urls"]) == 2, f"Missing images for {german_name}"


class TestExerciseEnrichmentAPI:
    """Integration tests for enrichment in API."""

    async def test_seeded_exercises_have_enrichment(self, client: AsyncClient) -> None:
        """Default exercises are seeded with enrichment data."""
        response = await client.get("/api/v1/exercises?search=Bankdrücken")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        ex = data["exercises"][0]
        assert ex["instructions"] is not None
        assert len(ex["instructions"]) > 0
        assert ex["primary_muscles"] is not None
        assert "chest" in ex["primary_muscles"]
        assert ex["image_urls"] is not None
        assert len(ex["image_urls"]) == 2
        assert ex["equipment"] is not None
        assert ex["exercise_db_id"] == "Barbell_Bench_Press_-_Medium_Grip"

    async def test_get_single_exercise_detail(self, client: AsyncClient) -> None:
        """GET /exercises/{id} returns full enrichment data."""
        # Seed
        await client.get("/api/v1/exercises")
        list_response = await client.get("/api/v1/exercises?search=Kniebeugen")
        exercise_id = list_response.json()["exercises"][0]["id"]

        response = await client.get(f"/api/v1/exercises/{exercise_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Kniebeugen"
        assert data["primary_muscles"] is not None
        assert "quadriceps" in data["primary_muscles"]
        assert data["instructions"] is not None
        assert data["image_urls"] is not None

    async def test_get_nonexistent_exercise_returns_404(self, client: AsyncClient) -> None:
        """GET /exercises/{id} returns 404 for nonexistent."""
        response = await client.get("/api/v1/exercises/99999")
        assert response.status_code == 404

    async def test_update_exercise_instructions(self, client: AsyncClient) -> None:
        """PATCH /exercises/{id} can update instructions and muscles."""
        create_response = await client.post(
            "/api/v1/exercises",
            json={"name": "Custom Ex", "category": "push"},
        )
        exercise_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/exercises/{exercise_id}",
            json={
                "instructions": ["Step 1", "Step 2"],
                "primary_muscles": ["chest", "triceps"],
                "secondary_muscles": ["shoulders"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["instructions"] == ["Step 1", "Step 2"]
        assert data["primary_muscles"] == ["chest", "triceps"]
        assert data["secondary_muscles"] == ["shoulders"]

    async def test_enrich_endpoint(self, client: AsyncClient) -> None:
        """POST /exercises/{id}/enrich enriches a known exercise."""
        # Seed
        await client.get("/api/v1/exercises")
        list_response = await client.get("/api/v1/exercises?search=Plank")
        exercise_id = list_response.json()["exercises"][0]["id"]

        response = await client.post(f"/api/v1/exercises/{exercise_id}/enrich")
        assert response.status_code == 200
        data = response.json()
        assert data["instructions"] is not None
        assert data["primary_muscles"] is not None

    async def test_enrich_endpoint_unknown_exercise_no_api_key(self, client: AsyncClient) -> None:
        """POST /exercises/{id}/enrich returns 404 when no DB match and no API key."""
        create_response = await client.post(
            "/api/v1/exercises",
            json={"name": "ZZZ Unknown Custom", "category": "core"},
        )
        exercise_id = create_response.json()["id"]

        with patch("app.services.exercise_ai_enrichment.settings") as mock_settings:
            mock_settings.claude_api_key = ""
            response = await client.post(f"/api/v1/exercises/{exercise_id}/enrich")
        assert response.status_code == 404

    async def test_enrich_endpoint_claude_fallback(self, client: AsyncClient) -> None:
        """POST /exercises/{id}/enrich uses Claude API when no DB match."""
        create_response = await client.post(
            "/api/v1/exercises",
            json={"name": "Spezialübung XYZ", "category": "core"},
        )
        exercise_id = create_response.json()["id"]

        mock_enrichment = {
            "instructions_json": json.dumps(["Schritt 1", "Schritt 2"]),
            "primary_muscles_json": json.dumps(["abdominals"]),
            "secondary_muscles_json": json.dumps([]),
            "image_urls_json": json.dumps([]),
            "equipment": "body_only",
            "level": "intermediate",
            "force": "static",
            "mechanic": "isolation",
            "exercise_db_id": None,
        }

        with patch(
            "app.services.exercise_ai_enrichment.generate_exercise_enrichment",
            return_value=mock_enrichment,
        ):
            response = await client.post(f"/api/v1/exercises/{exercise_id}/enrich")

        assert response.status_code == 200
        data = response.json()
        assert data["instructions"] == ["Schritt 1", "Schritt 2"]
        assert data["primary_muscles"] == ["abdominals"]
        assert data["equipment"] == "body_only"
        assert data["exercise_db_id"] is None

    async def test_create_exercise_claude_fallback(self, client: AsyncClient) -> None:
        """POST /exercises uses Claude fallback for unknown exercises."""
        mock_enrichment = {
            "instructions_json": json.dumps(["Ausführung 1"]),
            "primary_muscles_json": json.dumps(["quadriceps"]),
            "secondary_muscles_json": json.dumps(["glutes"]),
            "image_urls_json": json.dumps([]),
            "equipment": "body_only",
            "level": "beginner",
            "force": "push",
            "mechanic": "compound",
            "exercise_db_id": None,
        }

        with patch(
            "app.services.exercise_ai_enrichment.generate_exercise_enrichment",
            return_value=mock_enrichment,
        ):
            response = await client.post(
                "/api/v1/exercises",
                json={"name": "Einzigartige Übung 123", "category": "legs"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["instructions"] == ["Ausführung 1"]
        assert data["primary_muscles"] == ["quadriceps"]
        assert data["equipment"] == "body_only"
