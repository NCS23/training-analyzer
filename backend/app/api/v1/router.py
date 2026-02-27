from fastapi import APIRouter

from app.api.v1 import ai, athlete, goals, health, sessions, trends, workouts

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workouts.router, tags=["workouts"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(athlete.router, tags=["athlete"])
api_router.include_router(goals.router, tags=["goals"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(trends.router, tags=["trends"])
