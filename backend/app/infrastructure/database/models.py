from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
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
    rpe = Column(Integer)  # 1-10 Rate of Perceived Exertion

    # Strength training
    exercises_json = Column(Text)

    # GPS
    gps_track_json = Column(Text)
    has_gps = Column(Boolean, default=False, nullable=False, server_default="false")

    # Athlete settings snapshot (at time of upload)
    athlete_resting_hr = Column(Integer)
    athlete_max_hr = Column(Integer)

    # Training Type Klassifizierung
    training_type_auto = Column(String(30))
    training_type_confidence = Column(Integer)
    training_type_override = Column(String(30))

    # AI
    ai_analysis = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AthleteModel(Base):
    __tablename__ = "athletes"

    id = Column(Integer, primary_key=True, index=True)
    resting_hr = Column(Integer)
    max_hr = Column(Integer)

    # Elevation correction factors (sec/km per 100m)
    elevation_gain_factor = Column(Float, server_default="10.0")
    elevation_loss_factor = Column(Float, server_default="5.0")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ExerciseModel(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(20), nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False, server_default="false")
    is_custom = Column(Boolean, default=True, nullable=False, server_default="true")
    usage_count = Column(Integer, default=0, nullable=False, server_default="0")
    last_used_at = Column(DateTime, nullable=True)

    # Enrichment data (from free-exercise-db or Claude API)
    instructions_json = Column(Text)
    primary_muscles_json = Column(Text)
    secondary_muscles_json = Column(Text)
    image_urls_json = Column(Text)
    equipment = Column(String(50))
    level = Column(String(20))
    force = Column(String(20))
    mechanic = Column(String(20))
    exercise_db_id = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RaceGoalModel(Base):
    __tablename__ = "race_goals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    race_date = Column(DateTime, nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    target_time_seconds = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, server_default="true")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
