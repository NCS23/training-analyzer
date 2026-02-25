from fastapi import APIRouter

from app.api.v1 import ai, health, sessions, workouts

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workouts.router, tags=["workouts"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(ai.router, tags=["ai"])
