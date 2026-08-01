import logging
from time import perf_counter

from app.schemas.recommendation.pipeline import PipelineStep
from app.schemas.recommendation.recommendation import RecommendationRequest, RecommendationResponse
from app.schemas.recommendation.schedule_context import ScheduleContextResult
from app.schemas.recommendation.candidates import CandidateSearchResult
from app.services.recommendation.schedule_context_service import ScheduleContextService
from app.services.recommendation.candidate_search_service import CandidateSearchService
from app.services.recommendation.refinement_service import RecommendationRefinementService
from app.schemas.recommendation.refinement import RecommendationRefinementResult
from app.schemas.recommendation.temporal import TemporalValidationResult
from app.services.recommendation.temporal_validation_service import TemporalValidationService
from app.services.recommendation.suggestion_compose_service import SuggestionCompositionService


logger = logging.getLogger("uvicorn.error")


class RecommendationService:
    def __init__(
        self,
        schedule_context_service: ScheduleContextService,
        candidate_search_service: CandidateSearchService,
        refinement_service: RecommendationRefinementService,
        temporal_validation_service: TemporalValidationService,
        suggestion_compose_service: SuggestionCompositionService
    ) -> None:
        self.schedule_context_service = schedule_context_service
        self.candidate_search_service = candidate_search_service
        self.refinement_service = refinement_service
        self.temporal_validation_service = temporal_validation_service
        self.suggestion_compose_service = suggestion_compose_service

    def run_pipeline(
        self,
        request: RecommendationRequest,
        stop_after_step: PipelineStep | None = None,
    ) -> (
        ScheduleContextResult
        | CandidateSearchResult
        | RecommendationRefinementResult
        | TemporalValidationResult
        | RecommendationResponse
    ):
        started_at = perf_counter()

        try:
            return self._run_pipeline(
                request=request,
                stop_after_step=stop_after_step,
            )
        finally:
            elapsed_seconds = perf_counter() - started_at
            target_step = (
                stop_after_step.value
                if stop_after_step is not None
                else "final"
            )
            logger.info(
                "Recommendation pipeline completed: "
                "tempEventId=%s, step=%s, elapsed=%.3fs",
                request.temp_event_id,
                target_step,
                elapsed_seconds,
            )

    def _run_pipeline(
        self,
        request: RecommendationRequest,
        stop_after_step: PipelineStep | None = None,
    ) -> (
        ScheduleContextResult
        | CandidateSearchResult
        | RecommendationRefinementResult
        | TemporalValidationResult
        | RecommendationResponse
    ):
        # D101: 일정 맥락 구조화
        context = self.schedule_context_service.structure_context(request)

        if stop_after_step == PipelineStep.CONTEXT:
            return context

        # D101 실패 시 추천 파이프라인 조기 종료
        if context.embedding_status == "ERROR":
            return RecommendationResponse(
                tempEventId=context.temp_event_id,
                draftRevision=context.draft_revision,
                suggestionStatus="ERROR",
                suggestions=[],
                errorCode=context.error_code,
                errors=context.errors,
            )


        # D102: Neo4j 추천 후보 조회
        candidate = self.candidate_search_service.search(context)

        if stop_after_step == PipelineStep.CANDIDATES:
            return candidate

        # D102 전체 실패 시 추천 파이프라인 조기 종료
        if (
            candidate.mapping_status == "ERROR"
            or candidate.lookup_status == "ERROR"
        ):
            return RecommendationResponse(
                tempEventId=candidate.temp_event_id,
                draftRevision=candidate.draft_revision,
                suggestionStatus="ERROR",
                suggestions=[],
                errorCode=candidate.error_code,
                errors=candidate.errors,
            )


        # D103: Upstage 추천 항목 정제
        refined_result = self.refinement_service.refine(
            request=request,
            candidate_result=candidate,
        )

        if stop_after_step == PipelineStep.REFINED_ITEMS:
            return refined_result

        # D103 전체 실패 시 추천 파이프라인 조기 종료
        if refined_result.refinement_status == "ERROR":
            return RecommendationResponse(
                tempEventId=refined_result.temp_event_id,
                draftRevision=refined_result.draft_revision,
                suggestionStatus="ERROR",
                suggestions=[],
                errorCode=refined_result.error_code,
                errors=refined_result.errors,
            )


        # D104: 시간 맥락 검증 및 항목 유형 확정
        # D104는 오류 상태를 반환하지 않음
        # 예상하지 못한 예외는 전역 핸들러로 전파되며 D105는 실행되지 않음
        temporal_result = self.temporal_validation_service.temporal_validate(
            refinement_result=refined_result,
        )

        if stop_after_step == PipelineStep.VALIDATED_ITEMS:
            return temporal_result

        # D105: 최종 추천 응답 조합
        # 내부 계약 오류는 전역 핸들러에서 처리
        recommendation_result = self.suggestion_compose_service.compose(
            temporal_result=temporal_result
        )

        if stop_after_step is not None:
            raise NotImplementedError(
                f"{stop_after_step.value} 단계는 아직 구현되지 않았습니다."
            )

        return recommendation_result
