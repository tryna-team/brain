from fastapi import APIRouter

# TODO: import routes
from app.api.v1.routes import health

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
