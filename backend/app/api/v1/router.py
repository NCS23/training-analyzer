from fastapi import APIRouter

from app.api.v1 import (
    ai,
    athlete,
    exercise_library,
    goals,
    health,
    sessions,
    strength,
    training_balance,
    training_plans,
    trends,
    weekly_plan,
    workouts,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workouts.router, tags=["workouts"])
# strength MUST come before sessions — /sessions/strength must match before /{session_id}
api_router.include_router(strength.router, tags=["strength"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(athlete.router, tags=["athlete"])
api_router.include_router(goals.router, tags=["goals"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(trends.router, tags=["trends"])
api_router.include_router(exercise_library.router, tags=["exercises"])
api_router.include_router(training_plans.router, tags=["training-plans"])
api_router.include_router(weekly_plan.router, tags=["weekly-plan"])
api_router.include_router(training_balance.router, tags=["analytics"])
