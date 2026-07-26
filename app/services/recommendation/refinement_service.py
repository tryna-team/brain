import logging
from pydantic import ValidationError
from app.schemas.recommendation.candidates import CandidateSearchResult
from app.schemas.recommendation.recommendation import RecommendationRequest
from app.services.recommendation.prompts.refinement_prompt import (
    FEW_SHOT_VERSION,
    PROMPT_VERSION,
    build_refinement_messages
)
from app.schemas.recommendation.refinement import (
    LLMRefinementResponse,
    RecommendationRefinementResult,
    RefinedRecommendationItem
)
from app.services.recommendation.refinement_llm_service import (
    RefinementLLMError,
    RefinementLLMService,
)

logger = logging.getLogger(__name__)


class RecommendationRefinementService:
    def __init__(
        self,
        llm_service: RefinementLLMService,
    ) -> None:
        self.llm_service = llm_service

    # D102에서 조회된 후보가 없을 때
    def _build_no_candidates_result(
        self,
        request: RecommendationRequest,
        candidate_result: CandidateSearchResult,
    ) -> RecommendationRefinementResult:
        return RecommendationRefinementResult(
            tempEventId=request.temp_event_id,
            draftRevision=request.draft_revision,
            refinementStatus="no_candidates",
            promptVersion=PROMPT_VERSION,
            fewShotVersion=FEW_SHOT_VERSION,
            modelMeta={
                "provider": "upstage",
                "model": self.llm_service.model,
            },
            refinedItems=[],
            scheduleContext=candidate_result.schedule_context,
            errors=[]
        )
    
    # Upstage 반환 문자열 파싱
    def _parse_llm_response(
        self,
        content: str,
    ) -> LLMRefinementResponse:
        return LLMRefinementResponse.model_validate_json(content)
    
    # sourceCode 검증, 최종 결과 생성
    def _build_success_result(
        self,
        request: RecommendationRequest,
        candidate_result: CandidateSearchResult,
        llm_response: LLMRefinementResponse,
    ) -> RecommendationRefinementResult:
        candidates_by_code = {
            candidate.code: candidate
            for candidate in candidate_result.recommendation_candidates
        }

        refined_items: list[RefinedRecommendationItem] = []
        errors: list[str] = []
        selected_codes: set[str] = set()

        if len(llm_response.refined_items) > 3:
            errors.append(
                "Upstage returned more than 3 refined items."
            )

        for llm_item in llm_response.refined_items[:3]:
            candidate = candidates_by_code.get(
                llm_item.source_code
            )

            if candidate is None:
                errors.append(
                    "Upstage returned an unauthorized sourceCode: "
                    f"{llm_item.source_code}"
                )
                continue

            if candidate.code in selected_codes:
                errors.append(
                    "Upstage returned a duplicate sourceCode: "
                    f"{candidate.code}"
                )
                continue

            selected_codes.add(candidate.code)

            refined_items.append(
                RefinedRecommendationItem(
                    sourceCode=candidate.code,
                    displayText=llm_item.display_text,
                    actionType=candidate.action_type,
                    targetType=candidate.target_type,
                    suggestionLevel=candidate.suggestion_level,
                    defaultTiming=candidate.default_timing,
                    offsetDays=candidate.offset_days,
                    selectionRank=len(refined_items) + 1,
                )
            )

        return RecommendationRefinementResult(
            tempEventId=request.temp_event_id,
            draftRevision=request.draft_revision,
            refinementStatus="success",
            promptVersion=PROMPT_VERSION,
            fewShotVersion=FEW_SHOT_VERSION,
            modelMeta={
                "provider": "upstage",
                "model": self.llm_service.model,
            },
            refinedItems=refined_items,
            scheduleContext=candidate_result.schedule_context,
            errors=errors,
        )

    # fallback 결과 생성(Upstage 호출 실패·시간 초과 시 fallback 결과 응답)
    def _build_fallback_result(
        self,
        request: RecommendationRequest,
        candidate_result: CandidateSearchResult,
        message: str,
    ) -> RecommendationRefinementResult:
        safe_candidates = [
            candidate
            for candidate in candidate_result.recommendation_candidates
            if candidate.suggestion_level == "safe"
        ][:3]

        refined_items = [
            RefinedRecommendationItem(
                sourceCode=candidate.code,
                displayText=candidate.name,
                actionType=candidate.action_type,
                targetType=candidate.target_type,
                suggestionLevel=candidate.suggestion_level,
                defaultTiming=candidate.default_timing,
                offsetDays=candidate.offset_days,
                selectionRank=index,
            )
            for index, candidate in enumerate(
                safe_candidates,
                start=1,
            )
        ]

        return RecommendationRefinementResult(
            tempEventId=request.temp_event_id,
            draftRevision=request.draft_revision,
            refinementStatus="fallback",
            promptVersion=PROMPT_VERSION,
            fewShotVersion=FEW_SHOT_VERSION,
            modelMeta={
                "provider": "upstage",
                "model": self.llm_service.model,
            },
            refinedItems=refined_items,
            scheduleContext=candidate_result.schedule_context,
            errors=[message],
        )
    
    def _build_error_result(
        self,
        request: RecommendationRequest,
        candidate_result: CandidateSearchResult,
        message: str,
    ) -> RecommendationRefinementResult:
        return RecommendationRefinementResult(
            tempEventId=request.temp_event_id,
            draftRevision=request.draft_revision,
            refinementStatus="error",
            promptVersion=PROMPT_VERSION,
            fewShotVersion=FEW_SHOT_VERSION,
            modelMeta={
                "provider": "upstage",
                "model": self.llm_service.model,
            },
            refinedItems=[],
            scheduleContext=candidate_result.schedule_context,
            errors=[message],
        )

    # D103 Upstage를 통한 추천 항목 정제 핵심 메서드
    def refine(
        self,
        request: RecommendationRequest,
        candidate_result: CandidateSearchResult,
    ) -> RecommendationRefinementResult:
        
        if (
            request.temp_event_id
            != candidate_result.temp_event_id
            or request.draft_revision
            != candidate_result.draft_revision
        ):
            return self._build_error_result(
                request=request,
                candidate_result=candidate_result,
                message="Stale or mismatched D102 result.",
            )
        
        if candidate_result.lookup_status == "error":
            return self._build_error_result(
                request=request,
                candidate_result=candidate_result,
                message="D102 candidate lookup failed.",
            )
        
        if (
            candidate_result.lookup_status
            in {"no_mapping", "no_candidates"}
            or not candidate_result.recommendation_candidates
        ):
            return self._build_no_candidates_result(
                request=request,
                candidate_result=candidate_result,
            )

        messages = build_refinement_messages(
            event_title=request.event_title,
            candidate_result=candidate_result,
        )

        try:
            content = self.llm_service.complete(messages)
            llm_response = self._parse_llm_response(content)
        except RefinementLLMError:
            logger.exception("D103 Upstage 호출 실패")

            return self._build_fallback_result(
                request=request,
                candidate_result=candidate_result,
                message="D103 Upstage refinement failed.",
            )
        except ValidationError:
            logger.exception("D103 Upstage JSON 응답 검증 실패")

            return self._build_fallback_result(
                request=request,
                candidate_result=candidate_result,
                message="D103 Upstage returned invalid JSON.",
            )

        return self._build_success_result(
            request=request,
            candidate_result=candidate_result,
            llm_response=llm_response,
        )