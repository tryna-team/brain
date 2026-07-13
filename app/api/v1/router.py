from fastapi import APIRouter, Depends

from app.api.v1.routes import health
from app.core.internal_auth import verify_internal_api_key

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])

# 내부 API는 backend → brain 호출 전용. 헬스체크를 제외한 비즈니스 라우트는 여기에 등록한다.
protected_router = APIRouter(dependencies=[Depends(verify_internal_api_key)])
api_router.include_router(protected_router)
