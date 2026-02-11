from fastapi import APIRouter
from app.api.v1 import health, workouts, ai

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workouts.router, tags=["workouts"])
api_router.include_router(ai.router, tags=["ai"])
