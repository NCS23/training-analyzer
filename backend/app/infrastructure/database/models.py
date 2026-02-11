from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class WorkoutModel(Base):
    __tablename__ = "workouts"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    workout_type = Column(String, nullable=False, index=True)
    subtype = Column(String)
    
    duration_sec = Column(Integer)
    distance_km = Column(Float)
    pace = Column(String)
    hr_avg = Column(Integer)
    hr_max = Column(Integer)
    hr_min = Column(Integer)
    
    csv_data = Column(Text)
    ai_analysis = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
