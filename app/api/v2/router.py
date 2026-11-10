from fastapi import APIRouter, Depends

from app.api.v2.routes import recommendations
from app.core.internal_auth import verify_internal_api_key


api_router = APIRouter(dependencies=[Depends(verify_internal_api_key)])
api_router.include_router(recommendations.router)
