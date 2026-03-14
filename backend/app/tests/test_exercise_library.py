"""Tests fuer Exercise Library API."""

import io

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


def _make_jpeg(size: int = 100) -> bytes:
    """Erzeugt minimale gültige JPEG-Bytes."""
    # JPEG SOI marker + JFIF header + padding
    header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    return header + b"\x00" * max(0, size - len(header)) + b"\xff\xd9"


def _make_png(size: int = 100) -> bytes:
    """Erzeugt minimale gültige PNG-Bytes."""
    header = b"\x89PNG\r\n\x1a\n"
    return header + b"\x00" * max(0, size - len(header))


class TestExerciseImageUpload:
    """Tests für den Bild-Upload bei Custom-Übungen."""

    async def _create_custom_exercise(self, client: AsyncClient) -> int:
        """Erstellt eine Custom-Übung und gibt die ID zurück."""
        response = await client.post(
            "/api/v1/exercises",
            json={"name": "Upload Test Übung", "category": "push"},
        )
        assert response.status_code == 201
        return response.json()["id"]

    async def test_upload_one_image(self, client: AsyncClient) -> None:
        """Upload eines einzelnen Bildes setzt image_urls."""
        exercise_id = await self._create_custom_exercise(client)
        jpeg_data = _make_jpeg()

        response = await client.post(
            f"/api/v1/exercises/{exercise_id}/images",
            files={"image_0": ("start.jpg", io.BytesIO(jpeg_data), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["image_urls"]) == 1
        assert "/static/uploads/exercises/" in data["image_urls"][0]

    async def test_upload_two_images(self, client: AsyncClient) -> None:
        """Upload von zwei Bildern setzt beide image_urls."""
        exercise_id = await self._create_custom_exercise(client)
        jpeg_data = _make_jpeg()
        png_data = _make_png()

        response = await client.post(
            f"/api/v1/exercises/{exercise_id}/images",
            files={
                "image_0": ("start.jpg", io.BytesIO(jpeg_data), "image/jpeg"),
                "image_1": ("end.png", io.BytesIO(png_data), "image/png"),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["image_urls"]) == 2

    async def test_upload_rejects_non_custom(self, client: AsyncClient) -> None:
        """Upload für Standard-Übungen wird abgelehnt."""
        # Seed defaults
        await client.get("/api/v1/exercises")
        list_resp = await client.get("/api/v1/exercises")
        default_ex = next(ex for ex in list_resp.json()["exercises"] if not ex["is_custom"])

        response = await client.post(
            f"/api/v1/exercises/{default_ex['id']}/images",
            files={"image_0": ("test.jpg", io.BytesIO(_make_jpeg()), "image/jpeg")},
        )
        assert response.status_code == 400

    async def test_upload_rejects_invalid_type(self, client: AsyncClient) -> None:
        """Upload mit ungültigem Dateityp wird abgelehnt."""
        exercise_id = await self._create_custom_exercise(client)

        response = await client.post(
            f"/api/v1/exercises/{exercise_id}/images",
            files={"image_0": ("test.gif", io.BytesIO(b"GIF89a"), "image/gif")},
        )
        assert response.status_code == 400

    async def test_upload_rejects_oversized(self, client: AsyncClient) -> None:
        """Upload > 5 MB wird abgelehnt."""
        exercise_id = await self._create_custom_exercise(client)
        big_data = _make_jpeg(6 * 1024 * 1024)

        response = await client.post(
            f"/api/v1/exercises/{exercise_id}/images",
            files={"image_0": ("big.jpg", io.BytesIO(big_data), "image/jpeg")},
        )
        assert response.status_code == 400

    async def test_reupload_replaces_images(self, client: AsyncClient) -> None:
        """Re-Upload ersetzt bestehende Bilder."""
        exercise_id = await self._create_custom_exercise(client)
        jpeg_data = _make_jpeg()

        # Erster Upload: 2 Bilder
        await client.post(
            f"/api/v1/exercises/{exercise_id}/images",
            files={
                "image_0": ("s.jpg", io.BytesIO(jpeg_data), "image/jpeg"),
                "image_1": ("e.jpg", io.BytesIO(jpeg_data), "image/jpeg"),
            },
        )

        # Re-Upload: nur 1 Bild
        response = await client.post(
            f"/api/v1/exercises/{exercise_id}/images",
            files={"image_0": ("new.jpg", io.BytesIO(jpeg_data), "image/jpeg")},
        )
        assert response.status_code == 200
        assert len(response.json()["image_urls"]) == 1

    async def test_delete_images(self, client: AsyncClient) -> None:
        """DELETE löscht Bilder und setzt image_urls auf null."""
        exercise_id = await self._create_custom_exercise(client)

        # Upload
        await client.post(
            f"/api/v1/exercises/{exercise_id}/images",
            files={"image_0": ("s.jpg", io.BytesIO(_make_jpeg()), "image/jpeg")},
        )

        # Delete
        response = await client.delete(f"/api/v1/exercises/{exercise_id}/images")
        assert response.status_code == 204

        # Verify
        get_resp = await client.get(f"/api/v1/exercises/{exercise_id}")
        assert get_resp.json()["image_urls"] is None

    async def test_delete_rejects_non_custom(self, client: AsyncClient) -> None:
        """Delete für Standard-Übungen wird abgelehnt."""
        await client.get("/api/v1/exercises")
        list_resp = await client.get("/api/v1/exercises")
        default_ex = next(ex for ex in list_resp.json()["exercises"] if not ex["is_custom"])

        response = await client.delete(f"/api/v1/exercises/{default_ex['id']}/images")
        assert response.status_code == 400

    async def test_upload_not_found(self, client: AsyncClient) -> None:
        """Upload auf nicht-existente Übung gibt 404."""
        response = await client.post(
            "/api/v1/exercises/99999/images",
            files={"image_0": ("s.jpg", io.BytesIO(_make_jpeg()), "image/jpeg")},
        )
        assert response.status_code == 404

    async def test_delete_not_found(self, client: AsyncClient) -> None:
        """Delete auf nicht-existente Übung gibt 404."""
        response = await client.delete("/api/v1/exercises/99999/images")
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
