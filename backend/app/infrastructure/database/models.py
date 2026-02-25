from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class WorkoutModel(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    workout_type = Column(String(20), nullable=False, index=True)
    subtype = Column(String(30))

    # Running
    duration_sec = Column(Integer)
    distance_km = Column(Float)
    pace = Column(String(10))
    hr_avg = Column(Integer)
    hr_max = Column(Integer)
    hr_min = Column(Integer)
    cadence_avg = Column(Integer)

    # Stored data
    csv_data = Column(Text)
    laps_json = Column(Text)
    hr_zones_json = Column(Text)
    notes = Column(Text)

    # AI
    ai_analysis = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
