from fastapi import APIRouter

from app.global_response.response import ApiResponse
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthCheckResponse])
def health_check() -> ApiResponse[HealthCheckResponse]:
    return ApiResponse.ok(
        data=HealthCheckResponse(status="ok"),
        message="Tryna Brain server is running.",
    )
