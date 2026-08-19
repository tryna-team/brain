import logging

from app.schemas.recommendation.recommendation import RecommendationRequest
from app.services.recommendation.embedding_service import EmbeddingService
from app.core.exceptions import BusinessException
from app.schemas.recommendation.schedule_context import (
    DateCandidate,
    EmbeddingMeta,
    ScheduleContext,
    ScheduleContextResult,
    TimeCandidate,
)

logger = logging.getLogger(__name__)


class ScheduleContextService:

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service
    
    # 임베딩 모델 호출 전 정제
    def _build_semantic_input(
        self,
        request: RecommendationRequest,
    ) -> str:
        event_title = " ".join(request.event_title.split())
        embedding_words = " ".join(
            word.strip()
            for word in request.embedding_words
            if word.strip()
        )

        parts = [embedding_words or event_title]

        def append_if_not_duplicated(
            value: str,
            prefix: str = "",
        ) -> None:
            normalized_value = " ".join(value.split())

            if not normalized_value:
                return

            current_text = " ".join(parts).casefold()

            if normalized_value.casefold() in current_text:
                return

            parts.append(f"{prefix}{normalized_value}")

        if request.place_candidate:
            append_if_not_duplicated(
                request.place_candidate,
                prefix="장소: ",
            )

        if request.description:
            append_if_not_duplicated(
                request.description[:100],
            )

        return ". ".join(parts)
    
    def _build_schedule_context(
        self,
        request: RecommendationRequest,
    ) -> ScheduleContext:
        return ScheduleContext(
            startDateCandidate=DateCandidate(
                value=request.start_date_candidate,
                dateSource=request.start_date_source,
            ),
            startTimeCandidate=(
                TimeCandidate(value=request.start_time_candidate)
                if request.start_time_candidate is not None
                else None
            ),
            endDateCandidate=(
                DateCandidate(value=request.end_date_candidate)
                if request.end_date_candidate is not None
                else None
            ),
            endTimeCandidate=(
                TimeCandidate(value=request.end_time_candidate)
                if request.end_time_candidate is not None
                else None
            ),
            placeCandidate=request.place_candidate,
        )

    
    # 일정 맥락 구조화(D101 기능의 메인 함수)
    def structure_context(
        self,
        request: RecommendationRequest,
    ) -> ScheduleContextResult:
        semantic_input = self._build_semantic_input(request)
        schedule_context = self._build_schedule_context(request)

        try:
            query_embedding = self.embedding_service.embed(semantic_input)
        except BusinessException as exc:
            logger.warning(
                "D101 embedding failed: tempEventId=%s, errorCode=%s",
                request.temp_event_id,
                exc.error_code.name,
            )

            return ScheduleContextResult(
                tempEventId=request.temp_event_id,
                draftRevision=request.draft_revision,
                queryEmbedding=None,
                embeddingStatus="ERROR",
                semanticInputVersion="v2",
                scheduleContext=schedule_context,
                embeddingMeta=None,
                errorCode=exc.error_code.name,
                errors=[exc.message],
            )

        return ScheduleContextResult(
            tempEventId=request.temp_event_id,
            draftRevision=request.draft_revision,
            queryEmbedding=query_embedding,
            embeddingStatus="READY",
            semanticInputVersion="v2",
            scheduleContext=schedule_context,
            embeddingMeta=EmbeddingMeta(
                model=self.embedding_service.model,
                profile="QUERY",
                dimension=len(query_embedding),
            ),
        )
