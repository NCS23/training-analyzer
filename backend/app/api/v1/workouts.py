"""
Workout API Endpoints

Handles workout upload, analysis, and retrieval.
"""

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.database.session import get_db

router = APIRouter()


@router.post("/workouts/upload")
async def upload_workout(csv_file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Upload and analyze workout from CSV file

    **Process:**
    1. Parse CSV file (Apple Watch format)
    2. Extract lap data
    3. Analyze with AI
    4. Save to database

    **Returns:**
    Workout data with AI analysis
    """
    try:
        # Read CSV file
        content = await csv_file.read()
        csv_text = content.decode("utf-8")

        # Parse CSV (simplified - improve this based on actual Apple Watch format)
        workout_data = await parse_apple_watch_csv(csv_text)

        # Analyze with AI
        try:
            ai_analysis = await ai_service.analyze_workout(workout_data)
        except Exception as e:
            ai_analysis = f"AI analysis failed: {str(e)}"

        # Save to database
        workout = WorkoutModel(
            date=workout_data.get("date", datetime.now()),
            workout_type=workout_data.get("workout_type", "running"),
            subtype=workout_data.get("subtype"),
            duration_sec=workout_data.get("duration_sec"),
            distance_km=workout_data.get("distance_km"),
            pace=workout_data.get("pace"),
            hr_avg=workout_data.get("hr_avg"),
            hr_max=workout_data.get("hr_max"),
            hr_min=workout_data.get("hr_min"),
            csv_data=csv_text,
            ai_analysis=ai_analysis,
        )

        db.add(workout)
        await db.commit()
        await db.refresh(workout)

        return {
            "success": True,
            "workout_id": workout.id,
            "analysis": ai_analysis,
            "data": {
                "date": workout.date.isoformat(),
                "type": workout.workout_type,
                "duration_min": workout.duration_sec // 60 if workout.duration_sec else None,
                "distance_km": workout.distance_km,
                "pace": workout.pace,
                "hr_avg": workout.hr_avg,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}") from e


@router.get("/workouts")
async def get_workouts(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Get list of workouts"""
    from sqlalchemy import select

    query = select(WorkoutModel).order_by(WorkoutModel.date.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    workouts = result.scalars().all()

    return {
        "workouts": [
            {
                "id": w.id,
                "date": w.date.isoformat(),
                "type": w.workout_type,
                "subtype": w.subtype,
                "duration_min": w.duration_sec // 60 if w.duration_sec else None,
                "distance_km": w.distance_km,
                "pace": w.pace,
                "hr_avg": w.hr_avg,
            }
            for w in workouts
        ],
        "total": len(workouts),
    }


@router.get("/workouts/{workout_id}")
async def get_workout(workout_id: int, db: AsyncSession = Depends(get_db)):
    """Get single workout with AI analysis"""
    from sqlalchemy import select

    query = select(WorkoutModel).where(WorkoutModel.id == workout_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    return {
        "id": workout.id,
        "date": workout.date.isoformat(),
        "type": workout.workout_type,
        "subtype": workout.subtype,
        "duration_min": workout.duration_sec // 60 if workout.duration_sec else None,
        "distance_km": workout.distance_km,
        "pace": workout.pace,
        "hr_avg": workout.hr_avg,
        "hr_max": workout.hr_max,
        "hr_min": workout.hr_min,
        "ai_analysis": workout.ai_analysis,
    }


async def parse_apple_watch_csv(csv_text: str) -> dict:
    """
    Parse Apple Watch CSV file

    TODO: Implement proper parsing based on actual CSV format
    This is a placeholder - improve based on your CSV structure
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    # Placeholder parsing - adapt to actual format
    if not rows:
        raise ValueError("Empty CSV file")

    # Example: Extract from first row (adapt to your needs)
    rows[0]

    return {
        "date": datetime.now(),  # TODO: Parse from CSV
        "workout_type": "running",
        "duration_sec": 3000,  # TODO: Parse from CSV
        "distance_km": 5.0,  # TODO: Parse from CSV
        "pace": "6:00",  # TODO: Calculate from CSV
        "hr_avg": 150,  # TODO: Parse from CSV
        "hr_max": 170,  # TODO: Parse from CSV
        "hr_min": 120,  # TODO: Parse from CSV
    }
