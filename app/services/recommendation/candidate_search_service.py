import logging
from dataclasses import asdict, replace

from app.graph.exceptions import RecommendationRepositoryError

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.error_code import ErrorCode
from app.graph.repositories.recommendation_repo import RecommendationRepo
from app.graph.models.recommendation_candidate import (
    RecommendationCandidateRecord,
    SemanticCandidateRecord,
)
from app.schemas.recommendation.candidates import CandidateSearchResult
from app.schemas.recommendation.schedule_context import ScheduleContextResult


class CandidateSearchService:
    def __init__(
        self,
        recommendation_repo: RecommendationRepo,
    ) -> None:
        self.recommendation_repo = recommendation_repo

    # 상위 후보 선택(이벤트 타입, 장소)
    def _select_top_candidate(
        self,
        candidates: list[SemanticCandidateRecord],
    ) -> str | None:
        if not candidates:
            return None

        return max(
            candidates,
            key=lambda candidate: candidate.score,
        ).code

    # 상위 후보 선택(맥락 - 여행 관련 별도의 규칙이 필요하여 분리)
    def _select_contexts(
        self,
        candidates: list[SemanticCandidateRecord],
    ) -> list[str]:
        travel_scope_codes = {
            "domestic_travel",
            "international_travel",
        }

        selected = [
            candidate.code
            for candidate in candidates
            if candidate.code not in travel_scope_codes
        ]

        travel_scope_candidates = [
            candidate
            for candidate in candidates
            if candidate.code in travel_scope_codes
        ]

        if travel_scope_candidates:
            strongest_travel_scope = max(
                travel_scope_candidates,
                key=lambda candidate: candidate.score,
            )
            selected.append(strongest_travel_scope.code)

        return selected
    
    # 예외 상황 시의 결과 생성 함수
    def _build_error_result(
        self,
        context: ScheduleContextResult,
        error_code: ErrorCode,
        message: str,
    ) -> CandidateSearchResult:
        return CandidateSearchResult(
            tempEventId=context.temp_event_id,
            draftRevision=context.draft_revision,
            mappingStatus="ERROR",
            lookupStatus="ERROR",
            recommendationCandidates=[],
            scheduleContext=context.schedule_context,
            errorCode=error_code.name,
            errors=[message],
        )
    
    # 관계 기반, 벡터 기반 조회 결과 병합
    def _merge_recommendation_candidates(
        self,
        relation_candidates: list[RecommendationCandidateRecord],
        vector_candidates: list[RecommendationCandidateRecord],
        limit: int = 8,
    ) -> list[RecommendationCandidateRecord]:
        candidates_by_code = {
            candidate.code: candidate
            for candidate in relation_candidates
        }

        relation_order = [
            candidate.code
            for candidate in relation_candidates
        ]
        vector_only_codes: list[str] = []

        for vector_candidate in vector_candidates:
            existing_candidate = candidates_by_code.get(
                vector_candidate.code
            )

            if existing_candidate is None:
                candidates_by_code[vector_candidate.code] = (
                    vector_candidate
                )
                vector_only_codes.append(vector_candidate.code)
                continue

            matched_by = list(existing_candidate.matched_by)
            matched_by_keys = {
                (
                    tuple(item.source_labels),
                    item.source_code,
                    item.suggestion_mode,
                    item.reason,
                )
                for item in matched_by
            }

            for item in vector_candidate.matched_by:
                key = (
                    tuple(item.source_labels),
                    item.source_code,
                    item.suggestion_mode,
                    item.reason,
                )

                if key not in matched_by_keys:
                    matched_by.append(item)
                    matched_by_keys.add(key)

            candidates_by_code[vector_candidate.code] = replace(
                existing_candidate,
                vector_score=vector_candidate.vector_score,
                matched_by=matched_by,
            )

        ordered_codes = [
            *relation_order,
            *vector_only_codes,
        ]

        return [
            candidates_by_code[code]
            for code in ordered_codes[:limit]
        ]

    # 벡터화된 사용자 입력값으로 neo4j에서 실행 항목 조회(D102 핵심 함수)
    def search(
        self,
        context: ScheduleContextResult,
    ) -> CandidateSearchResult:
        query_embedding = context.query_embedding

        if context.embedding_status != "READY" or query_embedding is None:
            raise ValueError(
                "D102 requires a ready D101 embedding."
            )

        actual_dimension = len(query_embedding)
        expected_dimension = settings.d102_embedding_dimension

        if actual_dimension != expected_dimension:
            raise ValueError(
                "D102 received an invalid embedding dimension: "
                f"expected={expected_dimension}, "
                f"actual={actual_dimension}"
            )

        try :
            event_type_records = (
                self.recommendation_repo.find_event_type_candidates(
                    query_embedding=query_embedding,
                    min_score=settings.d102_event_type_min_score,
                )
            )

            context_records = (
                self.recommendation_repo.find_context_candidates(
                    query_embedding=query_embedding,
                    min_score=settings.d102_context_min_score,
                )
            )

            place_type_records = (
                self.recommendation_repo.find_place_type_candidates(
                    query_embedding=query_embedding,
                    min_score=settings.d102_place_type_min_score,
                )
            )

            selected_event_type = self._select_top_candidate(
                event_type_records
            )

            detected_contexts = self._select_contexts(
                context_records
            )

            resolved_contexts = self.recommendation_repo.resolve_contexts(
                detected_contexts
            )

        except RecommendationRepositoryError:
            logger.exception(
                "D102 semantic mapping failed: tempEventId=%s",
                context.temp_event_id,
            )

            return self._build_error_result(
                context=context,
                error_code=ErrorCode.NEO4J_503,
                message="Neo4j 추천 후보 조회에 실패했습니다.",
            )
        
        selected_place_type = self._select_top_candidate(
            place_type_records
        )

        mapping_status = (
            "MATCHED"
            if selected_event_type is not None or resolved_contexts
            else "UNMATCHED"
        )

        recommendation_records = []
        error_code: str | None = None
        errors: list[str] = []

        if mapping_status == "MATCHED":
            try:
                relation_candidates = (
                    self.recommendation_repo.find_relation_candidates(
                        selected_event_type=selected_event_type,
                        resolved_contexts=resolved_contexts,
                        selected_place_type=selected_place_type,
                    )
                )
            except RecommendationRepositoryError:
                logger.exception(
                    "D102 relation candidate lookup failed: tempEventId=%s",
                    context.temp_event_id,
                )

                lookup_status = "ERROR"
                error_code = ErrorCode.NEO4J_503.name
                errors.append(
                    "Neo4j 추천 후보 조회에 실패했습니다."
                )
            else:
                try:
                    vector_candidates = (
                        self.recommendation_repo
                        .find_recommendation_vector_candidates(
                            query_embedding=query_embedding,
                            min_score=(
                                settings.d102_recommendation_min_score
                            ),
                            selected_event_type=selected_event_type,
                            resolved_contexts=resolved_contexts,
                            selected_place_type=selected_place_type,
                        )
                    )
                except RecommendationRepositoryError:
                    logger.exception(
                        "D102 recommendation vector lookup failed: "
                        "tempEventId=%s",
                        context.temp_event_id,
                    )

                    recommendation_records = relation_candidates
                    lookup_status = "PARTIAL_ERROR"
                    errors.append(
                        "Neo4j 벡터 기반 추천 후보 조회에 실패했습니다."
                    )
                else:
                    recommendation_records = (
                        self._merge_recommendation_candidates(
                            relation_candidates=relation_candidates,
                            vector_candidates=vector_candidates,
                        )
                    )

                    lookup_status = (
                        "SUCCESS"
                        if recommendation_records
                        else "NO_CANDIDATES"
                    )
        else:
            lookup_status = "NO_MAPPING"

        return CandidateSearchResult(
            tempEventId=context.temp_event_id,
            draftRevision=context.draft_revision,
            mappingStatus=mapping_status,
            eventTypeCandidates=[
                {
                    "code": candidate.code,
                    "score": candidate.score,
                }
                for candidate in event_type_records
            ],
            selectedEventType=selected_event_type,
            contextCandidates=[
                {
                    "code": candidate.code,
                    "score": candidate.score,
                }
                for candidate in context_records
            ],
            detectedContexts=detected_contexts,
            resolvedContexts=resolved_contexts,
            placeTypeCandidates=[
                {
                    "code": candidate.code,
                    "score": candidate.score,
                }
                for candidate in place_type_records
            ],
            selectedPlaceType=selected_place_type,
            lookupStatus=lookup_status,
            recommendationCandidates=[
                asdict(candidate)
                for candidate in recommendation_records
            ],
            scheduleContext=context.schedule_context,
            errorCode=error_code,
            errors=errors
        )
