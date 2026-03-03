"""Exercise Library API Endpoints."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExerciseModel
from app.infrastructure.database.session import get_db
from app.models.exercise_library import (
    EnrichRequest,
    ExerciseCreate,
    ExerciseDbEntry,
    ExerciseDbSearchResponse,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseUpdate,
)
from app.services.exercise_enrichment import (
    enrich_exercise_model,
    enrich_exercise_model_by_id,
    get_all_german_names,
    load_exercise_db,
    translate_search_query,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])

# Valid exercise categories (matching strength.ExerciseCategory)
VALID_CATEGORIES = {"push", "pull", "legs", "core", "cardio", "drills"}

# Default exercises (seeded on first access)
DEFAULT_EXERCISES: list[dict[str, str]] = [
    # Push
    {"name": "Bankdrücken", "category": "push"},
    {"name": "Schrägbankdrücken", "category": "push"},
    {"name": "Kurzhantel-Bankdrücken", "category": "push"},
    {"name": "Schulterdrücken", "category": "push"},
    {"name": "Dips", "category": "push"},
    {"name": "Seitheben", "category": "push"},
    {"name": "Trizeps-Pushdown", "category": "push"},
    {"name": "Liegestütze", "category": "push"},
    # Pull
    {"name": "Klimmzüge", "category": "pull"},
    {"name": "Langhantelrudern", "category": "pull"},
    {"name": "Kurzhantelrudern", "category": "pull"},
    {"name": "Latzug", "category": "pull"},
    {"name": "Face Pulls", "category": "pull"},
    {"name": "Bizeps-Curls", "category": "pull"},
    {"name": "Hammer Curls", "category": "pull"},
    # Legs
    {"name": "Kniebeugen", "category": "legs"},
    {"name": "Kreuzheben", "category": "legs"},
    {"name": "Rumänisches Kreuzheben", "category": "legs"},
    {"name": "Beinpresse", "category": "legs"},
    {"name": "Ausfallschritte", "category": "legs"},
    {"name": "Beinbeuger", "category": "legs"},
    {"name": "Beinstrecker", "category": "legs"},
    {"name": "Wadenheben", "category": "legs"},
    {"name": "Hip Thrusts", "category": "legs"},
    # Core
    {"name": "Plank", "category": "core"},
    {"name": "Crunches", "category": "core"},
    {"name": "Russian Twist", "category": "core"},
    {"name": "Hanging Leg Raises", "category": "core"},
    {"name": "Cable Crunches", "category": "core"},
    # Cardio
    {"name": "Rudern Ergometer", "category": "cardio"},
    {"name": "Seilspringen", "category": "cardio"},
    # Drills (Lauf-ABC)
    {"name": "Kniehebelauf", "category": "drills"},
    {"name": "Anfersen", "category": "drills"},
    {"name": "Skippings", "category": "drills"},
    {"name": "Seitgalopp", "category": "drills"},
    {"name": "Hopserlauf", "category": "drills"},
]


# ASCII → Umlaut name migration for exercises seeded before umlaut fix
_NAME_MIGRATION: dict[str, str] = {
    "Bankdruecken": "Bankdrücken",
    "Schraegbankdruecken": "Schrägbankdrücken",
    "Kurzhantel-Bankdruecken": "Kurzhantel-Bankdrücken",
    "Schulterdruecken": "Schulterdrücken",
    "Liegestuetze": "Liegestütze",
    "Klimmzuege": "Klimmzüge",
    "Bizeps-Curls": "Bizeps-Curls",
    "Rumaenisches Kreuzheben": "Rumänisches Kreuzheben",
    "Ausfallschritte": "Ausfallschritte",
    "Trizeps-Pushdown": "Trizeps-Pushdown",
}


async def _ensure_seed_data(db: AsyncSession) -> None:
    """Seed default exercises if table is empty, enrich existing un-enriched ones."""
    count_result = await db.execute(select(ExerciseModel.id).limit(1))
    if count_result.scalar_one_or_none() is None:
        # Fresh seed with enrichment
        for ex in DEFAULT_EXERCISES:
            enrichment = enrich_exercise_model(ex["name"])
            model = ExerciseModel(
                name=ex["name"],
                category=ex["category"],
                is_custom=False,
                is_favorite=False,
            )
            if enrichment:
                _apply_enrichment(model, enrichment)
            db.add(model)
        await db.commit()
        return

    changed = False

    # Migrate ASCII names → proper umlauts
    result_all = await db.execute(select(ExerciseModel).where(ExerciseModel.is_custom.is_(False)))
    for exercise in result_all.scalars().all():
        new_name = _NAME_MIGRATION.get(str(exercise.name))
        if new_name:
            exercise.name = new_name  # type: ignore[assignment]
            changed = True

    if changed:
        await db.flush()

    # Enrich existing exercises that lack enrichment data
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.exercise_db_id.is_(None)))
    un_enriched = result.scalars().all()

    for exercise in un_enriched:
        enrichment = enrich_exercise_model(str(exercise.name))
        if enrichment:
            _apply_enrichment(exercise, enrichment)
            changed = True

    # Re-enrich all non-custom exercises to pick up updated translations
    result2 = await db.execute(
        select(ExerciseModel).where(
            ExerciseModel.is_custom.is_(False),
            ExerciseModel.exercise_db_id.isnot(None),
        )
    )
    for exercise in result2.scalars().all():
        enrichment = enrich_exercise_model(str(exercise.name))
        if enrichment:
            _apply_enrichment(exercise, enrichment)
            changed = True

    if changed:
        await db.commit()


def _apply_enrichment(model: ExerciseModel, enrichment: dict[str, Optional[str]]) -> None:
    """Apply enrichment data to an ExerciseModel."""
    model.instructions_json = enrichment.get("instructions_json")  # type: ignore[assignment]
    model.primary_muscles_json = enrichment.get("primary_muscles_json")  # type: ignore[assignment]
    model.secondary_muscles_json = enrichment.get("secondary_muscles_json")  # type: ignore[assignment]
    model.image_urls_json = enrichment.get("image_urls_json")  # type: ignore[assignment]
    model.equipment = enrichment.get("equipment")  # type: ignore[assignment]
    model.level = enrichment.get("level")  # type: ignore[assignment]
    model.force = enrichment.get("force")  # type: ignore[assignment]
    model.mechanic = enrichment.get("mechanic")  # type: ignore[assignment]
    model.exercise_db_id = enrichment.get("exercise_db_id")  # type: ignore[assignment]


@router.get("", response_model=ExerciseListResponse)
async def list_exercises(
    category: Optional[str] = Query(None, description="Filter nach Kategorie"),
    search: Optional[str] = Query(None, description="Suche nach Name"),
    favorites_only: bool = Query(False, description="Nur Favoriten"),
    db: AsyncSession = Depends(get_db),
) -> ExerciseListResponse:
    """Liste aller Übungen mit Filtern."""
    await _ensure_seed_data(db)

    query = select(ExerciseModel)

    if category and category in VALID_CATEGORIES:
        query = query.where(ExerciseModel.category == category)
    if search and search.strip():
        query = query.where(ExerciseModel.name.ilike(f"%{search.strip()}%"))
    if favorites_only:
        query = query.where(ExerciseModel.is_favorite.is_(True))

    # Sort: favorites first, then by usage_count desc, then name
    query = query.order_by(
        ExerciseModel.is_favorite.desc(),
        ExerciseModel.usage_count.desc(),
        ExerciseModel.name.asc(),
    )

    result = await db.execute(query)
    exercises = result.scalars().all()

    return ExerciseListResponse(
        exercises=[ExerciseResponse.from_db(e) for e in exercises],
        total=len(exercises),
    )


@router.get("/exercise-db/search", response_model=ExerciseDbSearchResponse)
async def search_exercise_db(
    q: Optional[str] = Query(None, description="Suche nach Name"),
    muscle: Optional[str] = Query(None, description="Filter nach primärem Muskel"),
    equipment: Optional[str] = Query(None, description="Filter nach Equipment"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ExerciseDbSearchResponse:
    """Durchsucht die free-exercise-db (873 Übungen).

    Unterstützt deutsche Suchbegriffe: 'Brust' findet Chest-Übungen,
    'Langhantel' findet Barbell-Übungen, 'Bankdrücken' findet
    'Barbell Bench Press' etc.
    """
    db = load_exercise_db()
    german_names = get_all_german_names()
    results: list[dict] = list(db.values())

    if q and q.strip():
        q_lower = q.strip().lower()

        # 1. Englische Suchbegriffe aus deutschem Query ableiten
        translated_terms = translate_search_query(q_lower)

        def matches(ex: dict) -> bool:
            name_lower = ex["name"].lower()
            # Direkter Match auf englischen Namen
            if q_lower in name_lower:
                return True
            # Match auf deutschen Alias-Namen
            de_name = german_names.get(ex["id"], "").lower()
            if de_name and q_lower in de_name:
                return True
            # Match über übersetzte Begriffe
            return any(term in name_lower for term in translated_terms)

        results = [e for e in results if matches(e)]

    if muscle:
        results = [e for e in results if muscle in e.get("primaryMuscles", [])]

    if equipment:
        results = [e for e in results if e.get("equipment") == equipment]

    results.sort(key=lambda e: e["name"])

    total = len(results)
    results = results[offset : offset + limit]

    return ExerciseDbSearchResponse(
        exercises=[
            ExerciseDbEntry(
                id=e["id"],
                name=e["name"],
                name_de=german_names.get(e["id"]),
                category=e.get("category"),
                equipment=e.get("equipment"),
                primary_muscles=e.get("primaryMuscles", []),
                level=e.get("level"),
                force=e.get("force"),
            )
            for e in results
        ],
        total=total,
    )


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Einzelne Übung mit allen Details."""
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Übung nicht gefunden.")
    return ExerciseResponse.from_db(exercise)


@router.post("", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    body: ExerciseCreate,
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Erstellt eine neue benutzerdefinierte Übung."""
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültige Kategorie. Erlaubt: {', '.join(sorted(VALID_CATEGORIES))}",
        )

    # Check for duplicates (case-insensitive)
    existing = await db.execute(select(ExerciseModel).where(ExerciseModel.name.ilike(body.name)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Übung existiert bereits.")

    exercise = ExerciseModel(
        name=body.name,
        category=body.category,
        is_custom=True,
        is_favorite=False,
    )

    # Try to enrich from free-exercise-db
    enrichment = enrich_exercise_model(body.name)
    if enrichment:
        _apply_enrichment(exercise, enrichment)

    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.from_db(exercise)


@router.patch("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: int,
    body: ExerciseUpdate,
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Aktualisiert eine Übung (Name, Kategorie, Favorit, Anleitung, Muskeln)."""
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Übung nicht gefunden.")

    if body.name is not None:
        # Check for name conflict
        existing = await db.execute(
            select(ExerciseModel).where(
                ExerciseModel.name.ilike(body.name),
                ExerciseModel.id != exercise_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Übung mit diesem Namen existiert bereits.",
            )
        exercise.name = body.name  # type: ignore[assignment]

    if body.category is not None:
        if body.category not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Ungültige Kategorie. Erlaubt: {', '.join(sorted(VALID_CATEGORIES))}",
            )
        exercise.category = body.category  # type: ignore[assignment]

    if body.is_favorite is not None:
        exercise.is_favorite = body.is_favorite  # type: ignore[assignment]

    if body.instructions is not None:
        exercise.instructions_json = json.dumps(body.instructions)  # type: ignore[assignment]

    if body.primary_muscles is not None:
        exercise.primary_muscles_json = json.dumps(body.primary_muscles)  # type: ignore[assignment]

    if body.secondary_muscles is not None:
        exercise.secondary_muscles_json = json.dumps(body.secondary_muscles)  # type: ignore[assignment]

    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.from_db(exercise)


@router.patch("/{exercise_id}/favorite", response_model=ExerciseResponse)
async def toggle_favorite(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Togglet den Favoriten-Status einer Übung."""
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Übung nicht gefunden.")

    exercise.is_favorite = not exercise.is_favorite  # type: ignore[assignment]
    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.from_db(exercise)


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Löscht eine benutzerdefinierte Übung."""
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Übung nicht gefunden.")

    if not exercise.is_custom:
        raise HTTPException(
            status_code=400,
            detail="Standard-Übungen können nicht gelöscht werden.",
        )

    await db.delete(exercise)
    await db.commit()


@router.post("/{exercise_id}/enrich", response_model=ExerciseResponse)
async def enrich_exercise(
    exercise_id: int,
    body: Optional[EnrichRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Reichert eine Übung mit free-exercise-db Daten an.

    Mit exercise_db_id im Body: direkte Zuordnung.
    Ohne Body: Name-basiertes Matching (abwärtskompatibel).
    """
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Übung nicht gefunden.")

    if body and body.exercise_db_id:
        enrichment = enrich_exercise_model_by_id(body.exercise_db_id)
    else:
        enrichment = enrich_exercise_model(str(exercise.name))

    if not enrichment:
        raise HTTPException(
            status_code=404,
            detail="Keine Daten in der Übungsdatenbank gefunden.",
        )

    _apply_enrichment(exercise, enrichment)

    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.from_db(exercise)
