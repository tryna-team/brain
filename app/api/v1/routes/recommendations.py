from fastapi import APIRouter, Query

from app.core.config import settings
from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.core.deps import RecommendationServiceDep
from app.schemas.recommendation.pipeline import PipelineStep
from app.schemas.recommendation.recommendation import RecommendationRequest
from app.schemas.recommendation.schedule_context import ScheduleContextResult
from app.schemas.recommendation.candidates import CandidateSearchResult
from app.schemas.recommendation.refinement import RecommendationRefinementResult

router = APIRouter(tags=["Recommendation"])


@router.post(
    "/recommendations",
    response_model=(
        ScheduleContextResult
        | CandidateSearchResult
        | RecommendationRefinementResult
    ),
)
def get_recommendations(
    request: RecommendationRequest,
    service: RecommendationServiceDep,
    stop_after_step: PipelineStep | None = Query(
        default=None,
        description="개발용: 지정한 단계까지 실행하고 해당 결과를 반환합니다.",
    ),
) -> (
    ScheduleContextResult
    | CandidateSearchResult
    | RecommendationRefinementResult
):
    if (
        settings.app_env == "prod"
        and stop_after_step is not None
    ):
        raise BusinessException(
            ErrorCode.COMMON_403,
            "운영 환경에서는 중간 결과를 조회할 수 없습니다.",
        )

    return service.run_pipeline(
        request=request,
        stop_after_step=stop_after_step,
    )
