from fastapi import APIRouter

from app.core.deps import ScheduleContextServiceDep
from app.schemas.recommendation.recommendation import RecommendationRequest
from app.schemas.recommendation.schedule_context import ScheduleContextResult

router = APIRouter(tags=["Recommendation"])


@router.post("/recommendations", response_model=ScheduleContextResult)
def structure_schedule_context(
    request: RecommendationRequest,
    service: ScheduleContextServiceDep,
) -> ScheduleContextResult:
    return service.structure_context(request)