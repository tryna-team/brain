from fastapi import APIRouter

from app.api.v1.routes import health, parse, recommendations, schedules

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(parse.router)
api_router.include_router(schedules.router)
api_router.include_router(recommendations.router)
