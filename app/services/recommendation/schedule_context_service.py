import json
import math
from app.schemas.recommendation.recommendation import RecommendationRequest
from app.core.config import settings
from app.core.valkey_client import valkey_client
from app.services.recommendation.embedding_service import EmbeddingService
from app.core.exceptions import BusinessException
from app.schemas.recommendation.schedule_context import (
    DateCandidate,
    EmbeddingMeta,
    ScheduleContext,
    ScheduleContextResult,
    TimeCandidate,
)
from app.services.recommendation.schedule_context_candidates import (
    CONTEXT_CANDIDATES,
    EVENT_TYPE_CANDIDATES,
    PLACE_TYPE_CANDIDATES,
)


class ScheduleContextService:

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service
    
    # # 임베딩 모델 호출 전 정제
    # def _build_embedding_text(self, request: RecommendationRequest) -> str | None:
    #     cleaned_words = (word.strip() for word in request.embedding_words)
    #     unique_words = list(dict.fromkeys(word for word in cleaned_words if word))

    #     if not unique_words:
    #         return None

    #     return " ".join(unique_words)
    
    # 임베딩 모델 호출 전 정제
    def _build_semantic_input(
        self,
        request: RecommendationRequest,
    ) -> str:
        semantic_words: list[str] = []

        for word in request.embedding_words:
            normalized_word = word.strip()

            if not normalized_word:
                continue

            if normalized_word not in semantic_words:
                semantic_words.append(normalized_word)

        if semantic_words:
            parts = [" ".join(semantic_words)]
        else:
            parts = [request.event_title.strip()]

        if request.place_candidate:
            place = request.place_candidate.strip()

            if place:
                parts.append(f"장소: {place}")

        if request.description:
            description = request.description.strip()[:100]

            if description:
                parts.append(description)

        return ". ".join(parts)
    
    def _build_schedule_context(
        self,
        request: RecommendationRequest,
    ) -> ScheduleContext:
        return ScheduleContext(
            dateCandidate=DateCandidate(
                value=request.start_date_candidate
            ),
            timeCandidate=(
                TimeCandidate(value=request.start_time_candidate)
                if request.start_time_candidate is not None
                else None
            ),
            placeCandidate=request.place_candidate,
        )
    
    # 캐시 key 생성
    def _candidate_cache_key(self, group: str, key: str) -> str:
        return f"{settings.valkey_key_prefix}:d101:v1:candidate_vector:{group}:{key}"
    
    # 후보 벡터 Valkey에서 읽기
    def _get_cached_vector(self, group: str, key: str) -> list[float] | None:
        if valkey_client is None:
            return None

        try:
            cached = valkey_client.get(self._candidate_cache_key(group, key))
        except Exception:
            return None

        if cached is None:
            return None

        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            return None
    
    # 후보 벡터 Valkey에 저장
    def _set_cached_vector(self, group: str, key: str, vector: list[float]) -> None:
        if valkey_client is None:
            return

        try:
            valkey_client.set(
                self._candidate_cache_key(group, key),
                json.dumps(vector),
                ex=settings.valkey_candidate_vector_ttl_seconds,
            )
        except Exception:
            return
    
    # 임베딩 전 캐시 확인
    def _get_candidate_vector(self, group: str, candidate: dict) -> list[float]:
        cached_vector = self._get_cached_vector(group, candidate["key"])
        if cached_vector is not None:
            return cached_vector

        candidate_text = self._build_candidate_text(candidate)
        vector = self.embedding_service.embed(candidate_text)
        self._set_cached_vector(group, candidate["key"], vector)

        return vector
    
    # candidate 하나를 임베딩할 문자열로 변환
    def _build_candidate_text(self, candidate: dict) -> str:
        return (
            f"{candidate['name']}. "
            f"{candidate['description']} "
            f"예시: {', '.join(candidate['examples'])}"
        )
    
    # 후보 찾기
    def _find_best_candidate(
        self,
        group: str,
        input_vector: list[float],
        candidates: list[dict],
        threshold: float,
    ) -> tuple[str | None, float]:
        best_key = None
        best_score = 0.0

        for candidate in candidates:
            candidate_vector = self._get_candidate_vector(group, candidate)
            score = self._cosine_similarity(input_vector, candidate_vector)

            if score > best_score:
                best_key = candidate["key"]
                best_score = score

        if best_score < threshold:
            return None, best_score
        
        return best_key, best_score
    
    # context 후보 목록 찾기
    def _find_context_candidates(
        self,
        input_vector: list[float],
        threshold: float = 0.47,
    ) -> list[str]:
        results: list[str] = []

        for candidate in CONTEXT_CANDIDATES:
            candidate_vector = self._get_candidate_vector("context", candidate)
            score = self._cosine_similarity(input_vector, candidate_vector)

            if score >= threshold:
                results.append(candidate["key"])

        return results
    
    # confidence 계산
    def _calculate_confidence(self, score: float) -> str:
        if score >= 0.60:
            return "high"
        if score >= 0.53:
            return "medium"
        if score >= 0.48:
            return "low"

        return "unknown"

    # 코사인 유사도 함수
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)
    
    # 일정 맥락 구조화(D101 기능의 메인 함수)
    def structure_context(
        self,
        request: RecommendationRequest,
    ) -> ScheduleContextResult:
        semantic_input = self._build_semantic_input(request)
        schedule_context = self._build_schedule_context(request)

        try:
            query_embedding = self.embedding_service.embed(semantic_input)
        except BusinessException:
            return ScheduleContextResult(
                tempEventId=request.temp_event_id,
                draftRevision=request.draft_revision,
                queryEmbedding=None,
                embeddingStatus="error",
                semanticInputVersion="v1",
                scheduleContext=schedule_context,
                embeddingMeta=None,
            )

        return ScheduleContextResult(
            tempEventId=request.temp_event_id,
            draftRevision=request.draft_revision,
            queryEmbedding=query_embedding,
            embeddingStatus="ready",
            semanticInputVersion="v1",
            scheduleContext=schedule_context,
            embeddingMeta=EmbeddingMeta(
                model=self.embedding_service.model,
                profile="query",
                dimension=len(query_embedding),
            ),
        )
