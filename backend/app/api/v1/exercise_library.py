"""Exercise Library API Endpoints."""

import json
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
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
    {"name": "Fußgelenksarbeit", "category": "drills"},
    {"name": "Prellhopser", "category": "drills"},
    {"name": "Sprunglauf", "category": "drills"},
    {"name": "Steigerungslauf", "category": "drills"},
    {"name": "Seitwärts überkreuzen", "category": "drills"},
    {"name": "Seitsprünge", "category": "drills"},
    {"name": "Rückwärtslaufen", "category": "drills"},
    {"name": "B-Skip", "category": "drills"},
    {"name": "High Kicks", "category": "drills"},
    {"name": "Wechselsprünge", "category": "drills"},
    {"name": "Vorderfußsprünge", "category": "drills"},
]

# Inline enrichment for drills (not in free-exercise-db)
_DRILL_ENRICHMENT: dict[str, dict[str, Optional[str]]] = {
    "Kniehebelauf": {
        "instructions_json": json.dumps(
            [
                "Laufe auf der Stelle oder in langsamer Vorwärtsbewegung und ziehe die Knie abwechselnd aktiv bis auf Hüfthöhe hoch.",
                "Der Fußaufsatz erfolgt auf dem Vorderfuß, der Oberkörper bleibt aufrecht.",
                "Achte auf eine aktive Armarbeit gegengleich zu den Beinen.",
                "Beginne langsam und steigere die Frequenz nach Gefühl.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Hüftbeuger", "Quadrizeps"]),
        "secondary_muscles_json": json.dumps(["Waden", "Rumpf"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Anfersen": {
        "instructions_json": json.dumps(
            [
                "Laufe locker vorwärts und ziehe die Fersen abwechselnd aktiv zum Gesäß.",
                "Der Oberkörper bleibt aufrecht, die Hüfte leicht nach vorne geschoben.",
                "Die Knie bleiben unter dem Körper — die Bewegung kommt aus der Beinrückseite.",
                "Halte eine gleichmäßige Frequenz und achte auf lockere Schultern.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Hamstrings", "Waden"]),
        "secondary_muscles_json": json.dumps(["Gesäß", "Hüftbeuger"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Skippings": {
        "instructions_json": json.dumps(
            [
                "Führe schnelle, kurze Kniehebeläufe mit maximaler Frequenz aus.",
                "Die Kontaktzeit am Boden soll minimal sein — Vorderfuß-Aufsatz.",
                "Die Arme arbeiten aktiv und gegengleich im Rhythmus mit.",
                "Halte den Rumpf stabil und den Blick nach vorne gerichtet.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Waden", "Hüftbeuger"]),
        "secondary_muscles_json": json.dumps(["Quadrizeps", "Schienbeinmuskel"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Seitgalopp": {
        "instructions_json": json.dumps(
            [
                "Bewege dich seitlich in Galoppschritten — ein Bein führt, das andere schließt an.",
                "Bleibe auf den Fußballen und federe leicht bei jedem Schritt.",
                "Der Oberkörper bleibt aufrecht, die Arme schwingen locker mit.",
                "Wechsle nach der Hälfte der Strecke die Seite.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Adduktoren", "Abduktoren"]),
        "secondary_muscles_json": json.dumps(["Waden", "Quadrizeps"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Hopserlauf": {
        "instructions_json": json.dumps(
            [
                "Springe bei jedem Schritt aktiv nach oben ab, indem du das Schwungbein-Knie hochziehst.",
                "Drücke dich kräftig über den Vorderfuß ab und nutze den Armschwung für Höhe.",
                "Lande weich auf dem Vorderfuß und gehe direkt in den nächsten Sprung.",
                "Achte auf eine aufrechte Haltung und schaue geradeaus.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Waden", "Quadrizeps", "Gesäß"]),
        "secondary_muscles_json": json.dumps(["Hüftbeuger", "Rumpf"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Fußgelenksarbeit": {
        "instructions_json": json.dumps(
            [
                "Laufe in kleinen, schnellen Schritten vorwärts — der Fuß setzt nur mit dem Ballen auf.",
                "Die Fußgelenke federn bei jedem Schritt aktiv ab, die Knie bleiben fast gestreckt.",
                "Halte den Bodenkontakt so kurz wie möglich.",
                "Arme locker angewinkelt mitschwingen, Oberkörper aufrecht.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Waden", "Fußgelenke"]),
        "secondary_muscles_json": json.dumps(["Schienbeinmuskel", "Quadrizeps"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Prellhopser": {
        "instructions_json": json.dumps(
            [
                "Springe beidbeinig oder einbeinig aus dem Fußgelenk ab — möglichst steif, ohne die Knie stark zu beugen.",
                "Der Abdruck kommt primär aus der Wade und dem Fußgelenk.",
                "Halte die Bodenkontaktzeit kurz und reaktiv.",
                "Arme können seitlich oder angewinkelt unterstützen.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Waden", "Fußgelenke"]),
        "secondary_muscles_json": json.dumps(["Quadrizeps", "Schienbeinmuskel"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Sprunglauf": {
        "instructions_json": json.dumps(
            [
                "Laufe mit übertrieben langen, federnden Schritten — wie in Zeitlupe durch die Luft.",
                "Drücke dich kräftig vom Vorderfuß ab und bringe das Schwungbein-Knie weit nach oben.",
                "Ziel ist maximale Flugphase bei jedem Schritt.",
                "Lande weich und kontrolliert, der Oberkörper bleibt stabil und aufrecht.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Gesäß", "Quadrizeps", "Waden"]),
        "secondary_muscles_json": json.dumps(["Hüftbeuger", "Hamstrings", "Rumpf"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Steigerungslauf": {
        "instructions_json": json.dumps(
            [
                "Beginne im lockeren Trab und steigere das Tempo gleichmäßig über 80-100 Meter bis zum Sprinttempo.",
                "Fokussiere dich auf eine saubere Lauftechnik: hohe Knie, aktiver Armschwung, Vorderfuß-Aufsatz.",
                "Am Ende der Strecke solltest du bei etwa 95% deiner Maximalgeschwindigkeit sein.",
                "Laufe locker aus — kein abruptes Stoppen.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Quadrizeps", "Hamstrings", "Waden"]),
        "secondary_muscles_json": json.dumps(["Gesäß", "Hüftbeuger", "Rumpf"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Seitwärts überkreuzen": {
        "instructions_json": json.dumps(
            [
                "Bewege dich seitlich und kreuze das hintere Bein abwechselnd vor und hinter dem Standbein.",
                "Die Hüfte rotiert dabei aktiv mit — der Oberkörper bleibt möglichst stabil nach vorne gerichtet.",
                "Bleibe auf den Fußballen und halte einen gleichmäßigen Rhythmus.",
                "Wechsle nach der Hälfte der Strecke die Laufrichtung.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Hüftrotatoren", "Adduktoren", "Abduktoren"]),
        "secondary_muscles_json": json.dumps(["Waden", "Rumpf", "Obliques"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Seitsprünge": {
        "instructions_json": json.dumps(
            [
                "Springe beidbeinig von einer Seite zur anderen, etwa schulterbreit.",
                "Lande weich auf den Fußballen mit leicht gebeugten Knien.",
                "Die Bewegung kommt aus Fußgelenk und Knie — Oberkörper bleibt stabil.",
                "Halte einen gleichmäßigen Rhythmus und achte auf eine aktive Stabilisierung.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Adduktoren", "Abduktoren", "Waden"]),
        "secondary_muscles_json": json.dumps(["Quadrizeps", "Gesäß", "Rumpf"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Rückwärtslaufen": {
        "instructions_json": json.dumps(
            [
                "Laufe in moderatem Tempo rückwärts — Aufsatz über den Vorderfuß, dann Ferse absenken.",
                "Halte den Rumpf aufrecht und schaue über die Schulter oder drehe den Kopf regelmäßig.",
                "Die Schritte sind kürzer als beim Vorwärtslaufen.",
                "Diese Übung stärkt die vordere Oberschenkel- und Schienbeinmuskulatur.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Quadrizeps", "Schienbeinmuskel"]),
        "secondary_muscles_json": json.dumps(["Waden", "Gesäß", "Rumpf"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "B-Skip": {
        "instructions_json": json.dumps(
            [
                "Ziehe das Knie wie beim Kniehebelauf hoch und strecke den Unterschenkel dann aktiv nach vorne aus.",
                "Ziehe den Fuß anschließend kratzig unter den Körper zurück — wie eine Scharrbewegung am Boden.",
                "Die Arme arbeiten kräftig und gegengleich mit.",
                "Achte auf einen aufrechten Oberkörper und aktiven Fußaufsatz unter dem Schwerpunkt.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Hamstrings", "Hüftbeuger", "Gesäß"]),
        "secondary_muscles_json": json.dumps(["Waden", "Quadrizeps", "Rumpf"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "High Kicks": {
        "instructions_json": json.dumps(
            [
                "Schwinge im Gehen oder leichtem Lauf das gestreckte Bein nach vorne oben.",
                "Versuche mit der Hand die Fußspitze auf Hüfthöhe oder höher zu berühren.",
                "Die Bewegung soll kontrolliert und fließend sein — nicht ruckartig.",
                "Halte den Rumpf aufrecht und vermeide ein Zurücklehnen.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Hamstrings", "Hüftbeuger"]),
        "secondary_muscles_json": json.dumps(["Quadrizeps", "Waden", "Rumpf"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Wechselsprünge": {
        "instructions_json": json.dumps(
            [
                "Springe aus einer leichten Schrittstellung explosiv nach oben und wechsle die Beine in der Luft.",
                "Lande weich in der entgegengesetzten Schrittstellung und springe sofort wieder ab.",
                "Die Arme arbeiten aktiv gegengleich mit — wie beim Sprint.",
                "Achte auf eine aufrechte Haltung und aktiven Vorderfuß-Aufsatz.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Quadrizeps", "Gesäß", "Waden"]),
        "secondary_muscles_json": json.dumps(["Hamstrings", "Hüftbeuger", "Rumpf"]),
        "level": "intermediate",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
    "Vorderfußsprünge": {
        "instructions_json": json.dumps(
            [
                "Springe beidbeinig vorwärts ab — ausschließlich über die Vorderfüße, die Fersen berühren den Boden nicht.",
                "Halte die Knie leicht gebeugt und den Rumpf stabil.",
                "Die Sprünge sind kurz und schnell — Fokus auf reaktive Fußarbeit.",
                "Halte die Arme angewinkelt und nutze sie für Schwung und Balance.",
            ]
        ),
        "primary_muscles_json": json.dumps(["Waden", "Fußgelenke"]),
        "secondary_muscles_json": json.dumps(["Quadrizeps", "Schienbeinmuskel", "Rumpf"]),
        "level": "beginner",
        "equipment": "body_only",
        "image_urls_json": None,
        "force": None,
        "mechanic": None,
        "exercise_db_id": None,
    },
}


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


UPLOAD_DIR = Path(__file__).parent.parent.parent / "static" / "uploads" / "exercises"
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


async def _validate_image_file(file: UploadFile) -> tuple[bytes, str]:
    """Validiert und liest eine Bild-Datei. Gibt (content, extension) zurück."""
    if not file.content_type or file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Nur JPG/PNG-Bilder werden akzeptiert.",
        )
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Bild-Datei ist leer.")
    if len(content) > _MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Bild darf maximal 5 MB groß sein.")
    ext = ".png" if file.content_type == "image/png" else ".jpg"
    return content, ext


async def _ensure_seed_data(db: AsyncSession) -> None:  # noqa: PLR0912  # TODO: E16 Refactoring
    """Seed default exercises if table is empty, enrich existing un-enriched ones."""
    count_result = await db.execute(select(ExerciseModel.id).limit(1))
    if count_result.scalar_one_or_none() is None:
        # Fresh seed with enrichment
        for ex in DEFAULT_EXERCISES:
            enrichment = enrich_exercise_model(ex["name"]) or _DRILL_ENRICHMENT.get(ex["name"])
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

    # Seed missing default exercises (e.g. drills added in #140)
    existing_names_result = await db.execute(select(ExerciseModel.name))
    existing_names = {str(n) for n in existing_names_result.scalars().all()}
    for ex in DEFAULT_EXERCISES:
        if ex["name"] not in existing_names:
            enrichment = enrich_exercise_model(ex["name"]) or _DRILL_ENRICHMENT.get(ex["name"])
            model = ExerciseModel(
                name=ex["name"],
                category=ex["category"],
                is_custom=False,
                is_favorite=False,
            )
            if enrichment:
                _apply_enrichment(model, enrichment)
            db.add(model)
            changed = True

    # Migrate ASCII names → proper umlauts
    result_all = await db.execute(select(ExerciseModel).where(ExerciseModel.is_custom.is_(False)))
    for exercise in result_all.scalars().all():
        new_name = _NAME_MIGRATION.get(str(exercise.name))
        if new_name:
            exercise.name = new_name
            changed = True

    if changed:
        await db.flush()

    # Enrich existing exercises that lack enrichment data
    result = await db.execute(
        select(ExerciseModel).where(
            ExerciseModel.exercise_db_id.is_(None),
            ExerciseModel.instructions_json.is_(None),
        )
    )
    un_enriched = result.scalars().all()

    for exercise in un_enriched:
        enrichment = enrich_exercise_model(str(exercise.name)) or _DRILL_ENRICHMENT.get(
            str(exercise.name)
        )
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
    model.instructions_json = enrichment.get("instructions_json")
    model.primary_muscles_json = enrichment.get("primary_muscles_json")
    model.secondary_muscles_json = enrichment.get("secondary_muscles_json")
    model.image_urls_json = enrichment.get("image_urls_json")
    model.equipment = enrichment.get("equipment")
    model.level = enrichment.get("level")
    model.force = enrichment.get("force")
    model.mechanic = enrichment.get("mechanic")
    model.exercise_db_id = enrichment.get("exercise_db_id")


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

    # Try to enrich from free-exercise-db, then Claude API fallback
    enrichment = enrich_exercise_model(body.name)
    if not enrichment:
        from app.core.api_key_resolver import resolve_claude_api_key
        from app.services.exercise_ai_enrichment import generate_exercise_enrichment

        api_key = await resolve_claude_api_key(db)
        enrichment = await generate_exercise_enrichment(body.name, body.category, api_key)
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
        exercise.name = body.name

    if body.category is not None:
        if body.category not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Ungültige Kategorie. Erlaubt: {', '.join(sorted(VALID_CATEGORIES))}",
            )
        exercise.category = body.category

    if body.is_favorite is not None:
        exercise.is_favorite = body.is_favorite

    if body.instructions is not None:
        exercise.instructions_json = json.dumps(body.instructions)

    if body.primary_muscles is not None:
        exercise.primary_muscles_json = json.dumps(body.primary_muscles)

    if body.secondary_muscles is not None:
        exercise.secondary_muscles_json = json.dumps(body.secondary_muscles)

    if body.level is not None:
        exercise.level = body.level

    if body.equipment is not None:
        exercise.equipment = body.equipment

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

    exercise.is_favorite = not exercise.is_favorite
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
        # Fallback: Claude API für Anreicherung nutzen
        from app.core.api_key_resolver import resolve_claude_api_key
        from app.services.exercise_ai_enrichment import generate_exercise_enrichment

        api_key = await resolve_claude_api_key(db)
        enrichment = await generate_exercise_enrichment(
            str(exercise.name),
            str(exercise.category),
            api_key,
        )

    if not enrichment:
        raise HTTPException(
            status_code=404,
            detail="Keine Daten in der Übungsdatenbank gefunden.",
        )

    _apply_enrichment(exercise, enrichment)

    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.from_db(exercise)


@router.post("/{exercise_id}/images", response_model=ExerciseResponse)
async def upload_exercise_images(
    exercise_id: int,
    image_0: UploadFile = File(..., description="Startposition (Pflicht)"),
    image_1: UploadFile | None = File(None, description="Endposition (Optional)"),
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Lädt Bilder für eine Custom-Übung hoch (Start- und optional Endposition)."""
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Übung nicht gefunden.")
    if not exercise.is_custom:
        raise HTTPException(
            status_code=400,
            detail="Bilder können nur für Custom-Übungen hochgeladen werden.",
        )

    # Validate files
    content_0, ext_0 = await _validate_image_file(image_0)
    files_to_write: list[tuple[bytes, str, int]] = [(content_0, ext_0, 0)]

    if image_1 is not None:
        content_1, ext_1 = await _validate_image_file(image_1)
        files_to_write.append((content_1, ext_1, 1))

    # Write files — remove old directory first to clean stale images
    upload_dir = UPLOAD_DIR / str(exercise_id)
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    image_urls: list[str] = []
    for content, ext, idx in files_to_write:
        file_path = upload_dir / f"{idx}{ext}"
        file_path.write_bytes(content)
        image_urls.append(f"/static/uploads/exercises/{exercise_id}/{idx}{ext}")

    exercise.image_urls_json = json.dumps(image_urls)
    await db.commit()
    await db.refresh(exercise)

    return ExerciseResponse.from_db(exercise)


@router.delete("/{exercise_id}/images", status_code=204)
async def delete_exercise_images(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Löscht alle hochgeladenen Bilder einer Custom-Übung."""
    result = await db.execute(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Übung nicht gefunden.")
    if not exercise.is_custom:
        raise HTTPException(
            status_code=400,
            detail="Bilder können nur für Custom-Übungen gelöscht werden.",
        )

    # Remove files
    upload_dir = UPLOAD_DIR / str(exercise_id)
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    exercise.image_urls_json = None
    await db.commit()
