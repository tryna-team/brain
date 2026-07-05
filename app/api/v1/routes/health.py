from __future__ import annotations

from fastapi import APIRouter

from app.core.responses import ApiResponse, success_response
from app.core.error_code import SuccessCode
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthCheckResponse])
def health_check() -> ApiResponse[HealthCheckResponse]:
    return success_response(
        result=HealthCheckResponse(status="ok"),
        success_code=SuccessCode.OK,
        message="Tryna Brain server is running.",
    )
