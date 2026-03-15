from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkoutModel(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    workout_type: Mapped[str] = mapped_column(String(20), index=True)
    subtype: Mapped[str | None] = mapped_column(String(30), default=None)

    # Running
    duration_sec: Mapped[int | None] = mapped_column(default=None)
    distance_km: Mapped[float | None] = mapped_column(Float, default=None)
    pace: Mapped[str | None] = mapped_column(String(10), default=None)
    hr_avg: Mapped[int | None] = mapped_column(default=None)
    hr_max: Mapped[int | None] = mapped_column(default=None)
    hr_min: Mapped[int | None] = mapped_column(default=None)
    cadence_avg: Mapped[int | None] = mapped_column(default=None)

    # Stored data
    csv_data: Mapped[str | None] = mapped_column(Text, default=None)
    laps_json: Mapped[str | None] = mapped_column(Text, default=None)
    hr_zones_json: Mapped[str | None] = mapped_column(Text, default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    rpe: Mapped[int | None] = mapped_column(default=None)  # 1-10 Rate of Perceived Exertion

    # Strength training
    exercises_json: Mapped[str | None] = mapped_column(Text, default=None)

    # HR Timeseries (per-second HR data, e.g. from FIT files without GPS)
    hr_timeseries_json: Mapped[str | None] = mapped_column(Text, default=None)

    # GPS
    gps_track_json: Mapped[str | None] = mapped_column(Text, default=None)
    has_gps: Mapped[bool] = mapped_column(default=False, server_default="false")

    # Athlete settings snapshot (at time of upload)
    athlete_resting_hr: Mapped[int | None] = mapped_column(default=None)
    athlete_max_hr: Mapped[int | None] = mapped_column(default=None)

    # Training Type Klassifizierung
    training_type_auto: Mapped[str | None] = mapped_column(String(30), default=None)
    training_type_confidence: Mapped[int | None] = mapped_column(default=None)
    training_type_override: Mapped[str | None] = mapped_column(String(30), default=None)

    # AI
    ai_analysis: Mapped[str | None] = mapped_column(Text, default=None)

    # Soll/Ist-Link (S10)
    planned_entry_id: Mapped[int | None] = mapped_column(default=None)  # FK to planned_sessions

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AthleteModel(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resting_hr: Mapped[int | None] = mapped_column(default=None)
    max_hr: Mapped[int | None] = mapped_column(default=None)

    # Elevation correction factors (sec/km per 100m)
    elevation_gain_factor: Mapped[float | None] = mapped_column(Float, server_default="10.0")
    elevation_loss_factor: Mapped[float | None] = mapped_column(Float, server_default="5.0")

    # Verschlüsselte API Keys (User-konfiguriert via UI)
    encrypted_claude_api_key: Mapped[str | None] = mapped_column(Text, default=None)
    encrypted_openai_api_key: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ExerciseModel(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(20))
    is_favorite: Mapped[bool] = mapped_column(default=False, server_default="false")
    is_custom: Mapped[bool] = mapped_column(default=True, server_default="true")
    usage_count: Mapped[int] = mapped_column(default=0, server_default="0")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # Enrichment data (from free-exercise-db or Claude API)
    instructions_json: Mapped[str | None] = mapped_column(Text, default=None)
    primary_muscles_json: Mapped[str | None] = mapped_column(Text, default=None)
    secondary_muscles_json: Mapped[str | None] = mapped_column(Text, default=None)
    image_urls_json: Mapped[str | None] = mapped_column(Text, default=None)
    equipment: Mapped[str | None] = mapped_column(String(50), default=None)
    level: Mapped[str | None] = mapped_column(String(20), default=None)
    force: Mapped[str | None] = mapped_column(String(20), default=None)
    mechanic: Mapped[str | None] = mapped_column(String(20), default=None)
    exercise_db_id: Mapped[str | None] = mapped_column(String(100), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SessionTemplateModel(Base):
    __tablename__ = "session_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    session_type: Mapped[str] = mapped_column(String(30), server_default="strength")
    exercises_json: Mapped[str | None] = mapped_column(Text, default=None)  # JSON array
    run_details_json: Mapped[str | None] = mapped_column(Text, default=None)  # JSON for running
    is_template: Mapped[bool] = mapped_column(default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RaceGoalModel(Base):
    __tablename__ = "race_goals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    race_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    distance_km: Mapped[float] = mapped_column(Float)
    target_time_seconds: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    training_plan_id: Mapped[int | None] = mapped_column(default=None)  # FK to training_plans

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TrainingPlanModel(Base):
    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    goal_id: Mapped[int | None] = mapped_column(default=None)  # FK to race_goals
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    target_event_date: Mapped[date | None] = mapped_column(Date, default=None)
    weekly_structure_json: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(20), server_default="draft")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TrainingPhaseModel(Base):
    __tablename__ = "training_phases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    training_plan_id: Mapped[int] = mapped_column(Integer)  # FK to training_plans
    name: Mapped[str] = mapped_column(String(200))
    phase_type: Mapped[str] = mapped_column(String(30))  # base|build|peak|taper|transition
    start_week: Mapped[int] = mapped_column(Integer)
    end_week: Mapped[int] = mapped_column(Integer)
    focus_json: Mapped[str | None] = mapped_column(Text, default=None)
    target_metrics_json: Mapped[str | None] = mapped_column(Text, default=None)
    weekly_template_json: Mapped[str | None] = mapped_column(Text, default=None)
    weekly_templates_json: Mapped[str | None] = mapped_column(Text, default=None)  # Per-week
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WeeklyPlanDayModel(Base):
    __tablename__ = "weekly_plan_days"
    __table_args__ = (UniqueConstraint("week_start", "day_of_week", name="uq_day_week_day"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int | None] = mapped_column(default=None, index=True)  # FK to training_plans
    week_start: Mapped[date] = mapped_column(Date, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Mon, 6=Sun
    is_rest_day: Mapped[bool] = mapped_column(default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    edited: Mapped[bool] = mapped_column(default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class PlannedSessionModel(Base):
    __tablename__ = "planned_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    day_id: Mapped[int] = mapped_column(Integer, index=True)  # FK to weekly_plan_days
    position: Mapped[int] = mapped_column(Integer, server_default="0")
    training_type: Mapped[str] = mapped_column(String(30))  # 'strength', 'running'
    template_id: Mapped[int | None] = mapped_column(default=None)  # FK to session_templates
    run_details_json: Mapped[str | None] = mapped_column(Text, default=None)
    exercises_json: Mapped[str | None] = mapped_column(Text, default=None)  # JSON array
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(20), server_default="active")  # 'active'|'skipped'

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AIAnalysisLogModel(Base):
    __tablename__ = "ai_analysis_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workout_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workouts.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    provider: Mapped[str] = mapped_column(String(100))
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt: Mapped[str] = mapped_column(Text)
    raw_response: Mapped[str] = mapped_column(Text)
    parsed_ok: Mapped[bool] = mapped_column(Boolean, server_default="true")
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None)


class PlanChangeLogModel(Base):
    __tablename__ = "plan_changelog"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True)  # FK to training_plans
    change_type: Mapped[str] = mapped_column(String(30))
    category: Mapped[str | None] = mapped_column(String(20), default=None)
    summary: Mapped[str] = mapped_column(String(500))
    details_json: Mapped[str | None] = mapped_column(Text, default=None)
    reason: Mapped[str | None] = mapped_column(Text, default=None)
    created_by: Mapped[str | None] = mapped_column(String(50), default=None)  # future: user auth
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
