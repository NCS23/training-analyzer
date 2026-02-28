"""Tests fuer Exercise Library API."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExerciseModel


class TestExerciseLibraryUnit:
    """Unit tests for exercise library model."""

    async def test_exercise_model_creation(self, db_session: AsyncSession) -> None:
        """ExerciseModel can be created and persisted."""
        exercise = ExerciseModel(
            name="Test Exercise",
            category="push",
            is_custom=True,
            is_favorite=False,
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)

        assert exercise.id is not None
        assert exercise.name == "Test Exercise"
        assert exercise.category == "push"
        assert exercise.is_custom is True
        assert exercise.is_favorite is False
        assert exercise.usage_count == 0


class TestExerciseLibraryAPI:
    """Integration tests for exercise library endpoints."""

    async def test_list_exercises_seeds_defaults(self, client: AsyncClient) -> None:
        """First GET /exercises seeds default exercises."""
        response = await client.get("/api/v1/exercises")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 20  # We have 30+ default exercises
        assert len(data["exercises"]) == data["total"]

    async def test_list_exercises_filter_category(self, client: AsyncClient) -> None:
        """Category filter works."""
        response = await client.get("/api/v1/exercises?category=push")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for ex in data["exercises"]:
            assert ex["category"] == "push"

    async def test_list_exercises_search(self, client: AsyncClient) -> None:
        """Search filter works (case-insensitive, partial match)."""
        response = await client.get("/api/v1/exercises?search=bank")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2  # Bankdruecken, Schraegbankdruecken, etc.
        for ex in data["exercises"]:
            assert "bank" in ex["name"].lower()

    async def test_list_exercises_favorites_only(self, client: AsyncClient) -> None:
        """Favorites filter returns empty initially."""
        response = await client.get("/api/v1/exercises?favorites_only=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_create_exercise(self, client: AsyncClient) -> None:
        """POST /exercises creates a custom exercise."""
        response = await client.post(
            "/api/v1/exercises",
            json={"name": "Turkish Get-Up", "category": "core"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Turkish Get-Up"
        assert data["category"] == "core"
        assert data["is_custom"] is True
        assert data["is_favorite"] is False

    async def test_create_exercise_duplicate(self, client: AsyncClient) -> None:
        """Creating a duplicate exercise (case-insensitive) returns 409."""
        await client.post(
            "/api/v1/exercises",
            json={"name": "My Exercise", "category": "push"},
        )
        response = await client.post(
            "/api/v1/exercises",
            json={"name": "my exercise", "category": "push"},
        )
        assert response.status_code == 409

    async def test_create_exercise_invalid_category(self, client: AsyncClient) -> None:
        """Invalid category returns 400."""
        response = await client.post(
            "/api/v1/exercises",
            json={"name": "Some Exercise", "category": "invalid"},
        )
        assert response.status_code == 400

    async def test_update_exercise(self, client: AsyncClient) -> None:
        """PATCH /exercises/{id} updates exercise fields."""
        create_response = await client.post(
            "/api/v1/exercises",
            json={"name": "Old Name", "category": "push"},
        )
        exercise_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/exercises/{exercise_id}",
            json={"name": "New Name", "category": "pull"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["category"] == "pull"

    async def test_toggle_favorite(self, client: AsyncClient) -> None:
        """PATCH /exercises/{id}/favorite toggles favorite status."""
        # Seed first
        await client.get("/api/v1/exercises")
        # Get first exercise
        list_response = await client.get("/api/v1/exercises")
        first_id = list_response.json()["exercises"][0]["id"]

        # Toggle on
        response = await client.patch(f"/api/v1/exercises/{first_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is True

        # Toggle off
        response = await client.patch(f"/api/v1/exercises/{first_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is False

    async def test_favorites_sorted_first(self, client: AsyncClient) -> None:
        """Favorited exercises appear first in the list."""
        # Seed
        await client.get("/api/v1/exercises")
        list_response = await client.get("/api/v1/exercises")
        exercises = list_response.json()["exercises"]
        # Favorite the last exercise
        last_id = exercises[-1]["id"]
        last_name = exercises[-1]["name"]
        await client.patch(f"/api/v1/exercises/{last_id}/favorite")

        # Re-fetch — favorited should be first
        response = await client.get("/api/v1/exercises")
        data = response.json()
        assert data["exercises"][0]["name"] == last_name
        assert data["exercises"][0]["is_favorite"] is True

    async def test_delete_custom_exercise(self, client: AsyncClient) -> None:
        """DELETE /exercises/{id} deletes a custom exercise."""
        create_response = await client.post(
            "/api/v1/exercises",
            json={"name": "To Delete", "category": "core"},
        )
        exercise_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/exercises/{exercise_id}")
        assert response.status_code == 204

        # Verify deleted
        list_response = await client.get("/api/v1/exercises?search=To Delete")
        assert list_response.json()["total"] == 0

    async def test_delete_default_exercise_fails(self, client: AsyncClient) -> None:
        """Deleting a default (non-custom) exercise returns 400."""
        # Seed
        await client.get("/api/v1/exercises")
        list_response = await client.get("/api/v1/exercises")
        default_ex = next(ex for ex in list_response.json()["exercises"] if not ex["is_custom"])

        response = await client.delete(f"/api/v1/exercises/{default_ex['id']}")
        assert response.status_code == 400

    async def test_exercise_not_found(self, client: AsyncClient) -> None:
        """Operations on non-existent exercise return 404."""
        response = await client.patch(
            "/api/v1/exercises/99999",
            json={"name": "Updated"},
        )
        assert response.status_code == 404

        response = await client.patch("/api/v1/exercises/99999/favorite")
        assert response.status_code == 404

        response = await client.delete("/api/v1/exercises/99999")
        assert response.status_code == 404


class TestExerciseSync:
    """Tests for exercise sync during strength session creation."""

    @pytest.fixture
    async def _seed_exercises(self, client: AsyncClient) -> None:
        """Seed default exercises."""
        await client.get("/api/v1/exercises")

    @pytest.mark.usefixtures("_seed_exercises")
    async def test_creating_strength_session_syncs_exercises(self, client: AsyncClient) -> None:
        """Creating a strength session updates exercise usage counts."""
        import json

        exercises = [
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [{"reps": 10, "weight_kg": 60, "status": "completed"}],
            },
            {
                "name": "Brand New Exercise",
                "category": "legs",
                "sets": [{"reps": 8, "weight_kg": 40, "status": "completed"}],
            },
        ]

        form_data = {
            "exercises_json": json.dumps(exercises),
            "training_date": "2026-02-28",
            "duration_minutes": "45",
        }

        response = await client.post(
            "/api/v1/sessions/strength",
            data=form_data,
        )
        assert response.status_code == 201

        # Check Bankdruecken usage_count incremented
        list_response = await client.get("/api/v1/exercises?search=Bankdruecken")
        data = list_response.json()
        bank = next((e for e in data["exercises"] if e["name"] == "Bankdruecken"), None)
        assert bank is not None
        assert bank["usage_count"] >= 1

        # Check new exercise was auto-created
        list_response = await client.get("/api/v1/exercises?search=Brand New Exercise")
        data = list_response.json()
        assert data["total"] == 1
        assert data["exercises"][0]["name"] == "Brand New Exercise"
        assert data["exercises"][0]["is_custom"] is True
        assert data["exercises"][0]["usage_count"] == 1
