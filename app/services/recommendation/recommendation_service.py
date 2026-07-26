from app.schemas.recommendation.pipeline import PipelineStep
from app.schemas.recommendation.recommendation import RecommendationRequest
from app.schemas.recommendation.schedule_context import ScheduleContextResult
from app.schemas.recommendation.candidates import CandidateSearchResult
from app.services.recommendation.schedule_context_service import ScheduleContextService
from app.services.recommendation.candidate_search_service import CandidateSearchService
from app.services.recommendation.refinement_service import RecommendationRefinementService
from app.schemas.recommendation.refinement import RecommendationRefinementResult
from app.schemas.recommendation.temporal import TemporalValidationResult
from app.services.recommendation.temporal_validation_service import TemporalValidationService


class RecommendationService:
    def __init__(
        self,
        schedule_context_service: ScheduleContextService,
        candidate_search_service: CandidateSearchService,
        refinement_service: RecommendationRefinementService,
        temporal_validation_service: TemporalValidationService,
    ) -> None:
        self.schedule_context_service = schedule_context_service
        self.candidate_search_service = candidate_search_service
        self.refinement_service = refinement_service
        self.temporal_validation_service = temporal_validation_service

    def run_pipeline(
        self,
        request: RecommendationRequest,
        stop_after_step: PipelineStep | None = None,
    ) -> (
        ScheduleContextResult
        | CandidateSearchResult
        | RecommendationRefinementResult
        | TemporalValidationResult
    ):
        # D101: 일정 맥락 구조화
        context = self.schedule_context_service.structure_context(request)

        if stop_after_step == PipelineStep.CONTEXT:
            return context

        # D102: Neo4j 추천 후보 조회
        candidate = self.candidate_search_service.search(context)

        if stop_after_step == PipelineStep.CANDIDATES:
            return candidate
        

        # D103: Upstage 추천 항목 정제
        refined_result = self.refinement_service.refine(
            request=request,
            candidate_result=candidate,
        )

        if stop_after_step == PipelineStep.REFINED_ITEMS:
            return refined_result

        # D104: 시간 맥락 검증 및 항목 유형 확정
        temporal_result = self.temporal_validation_service.temporal_validate(
            refinement_result=refined_result,
        )

        if stop_after_step == PipelineStep.VALIDATED_ITEMS:
            return temporal_result

        if stop_after_step is not None:
            raise NotImplementedError(
                f"{stop_after_step.value} 단계는 아직 구현되지 않았습니다."
            )

        # D105 구현 전까지 최종 결과로 D104 반환
        return temporal_result