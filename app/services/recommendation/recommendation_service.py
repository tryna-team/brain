from app.schemas.recommendation.pipeline import PipelineStep
from app.schemas.recommendation.recommendation import RecommendationRequest
from app.schemas.recommendation.schedule_context import ScheduleContextResult
from app.services.recommendation.schedule_context_service import (
    ScheduleContextService,
)


class RecommendationService:
    def __init__(
        self,
        schedule_context_service: ScheduleContextService,
    ):
        self.schedule_context_service = schedule_context_service

    def run_pipeline(
        self,
        request: RecommendationRequest,
        stop_after_step: PipelineStep | None = None,
    ) -> ScheduleContextResult:
        context = self.schedule_context_service.structure_context(request)

        if stop_after_step == PipelineStep.CONTEXT:
            return context

        if stop_after_step is not None:
            raise NotImplementedError(
                f"{stop_after_step.value} 단계는 아직 구현되지 않았습니다."
            )

        # TODO: D102~D105 파이프라인 연결
        return context