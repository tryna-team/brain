from app.schemas.recommendation.pipeline import PipelineStep
from app.schemas.recommendation.recommendation import RecommendationRequest
from app.schemas.recommendation.schedule_context import ScheduleContextResult
from app.schemas.recommendation.candidates import CandidateSearchResult
from app.services.recommendation.schedule_context_service import (
    ScheduleContextService,
)
from app.services.recommendation.candidate_search_service import CandidateSearchService



class RecommendationService:
    def __init__(
        self,
        schedule_context_service: ScheduleContextService,
        candidate_search_service: CandidateSearchService
    ):
        self.schedule_context_service = schedule_context_service
        self.candidate_search_service = candidate_search_service

    def run_pipeline(
        self,
        request: RecommendationRequest,
        stop_after_step: PipelineStep | None = None,
    ) -> ScheduleContextResult | CandidateSearchResult:
        # D101: 일정 맥락 구조화
        context = self.schedule_context_service.structure_context(request)

        if stop_after_step == PipelineStep.CONTEXT:
            return context

        # D102: Neo4j 추천 후보 조회
        candidate = self.candidate_search_service.search(context)

        if stop_after_step == PipelineStep.CANDIDATES:
            return candidate

        if stop_after_step is not None:
            raise NotImplementedError(
                f"{stop_after_step.value} 단계는 아직 구현되지 않았습니다."
            )

        # TODO: D102~D105 파이프라인 연결
        return candidate