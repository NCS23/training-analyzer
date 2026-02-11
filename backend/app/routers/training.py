"""Training API Endpoints"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from datetime import date

from app.models.training import (
    TrainingType,
    TrainingSubType,
    TrainingUploadResponse,
)
from app.services.csv_parser import TrainingCSVParser

router = APIRouter(prefix="/training", tags=["training"])

# Parser Instanz
csv_parser = TrainingCSVParser()

@router.post("/upload", response_model=TrainingUploadResponse)
async def upload_training(
    csv_file: UploadFile = File(..., description="Apple Watch CSV Export"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),
    training_type: TrainingType = Form(..., description="Trainingstyp (running/strength)"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Spezifischer Trainingstyp"),
    notes: Optional[str] = Form(None, description="Notizen zum Training"),
):
    """
    Upload und Parse Training CSV von Apple Watch
    
    - **csv_file**: Apple Watch CSV Export (;-delimited)
    - **training_date**: Datum des Trainings
    - **training_type**: running oder strength
    - **training_subtype**: Optional, z.B. interval, longrun, knee_dominant
    - **notes**: Optionale Notizen
    
    Returns:
        Geparste Trainingsdaten mit Laps, Summary, HF-Zonen
    """
    try:
        # Validiere CSV Datei
        if not csv_file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="File must be a CSV file"
            )
        
        # Lese CSV
        content = await csv_file.read()
        
        # Parse CSV
        result = csv_parser.parse(content, training_type)
        
        if not result['success']:
            return TrainingUploadResponse(
                success=False,
                errors=result.get('errors', ['Unknown parsing error'])
            )
        
        # TODO: Später in DB speichern
        # training_id = await save_to_database(result, training_date, training_subtype, notes)
        
        return TrainingUploadResponse(
            success=True,
            training_id=None,  # TODO: Nach DB-Implementierung
            data=result.get('data'),
            metadata={
                **result.get('metadata', {}),
                'training_date': training_date.isoformat(),
                'training_subtype': training_subtype.value if training_subtype else None,
                'notes': notes,
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing training upload: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "training"}