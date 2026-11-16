from time import perf_counter
from uuid import uuid4

from app.schemas.recommendation.v2.candidate import (
    CandidateActionV2,
    RecommendationCandidateV2,
)
from app.schemas.recommendation.v2.context import RecommendationContextV2
from app.schemas.recommendation.v2.request import RecommendationRequestV2
from app.schemas.recommendation.v2.response import (
    RecommendationIssueV2,
    RecommendationProcessingV2,
    RecommendationResponseV2,
)

## 임시 응답
def recommend(request: RecommendationRequestV2) -> RecommendationResponseV2:
    started_at = perf_counter()

    candidate = RecommendationCandidateV2(
        candidate_id=uuid4(),
        display_text="일정에 필요한 준비 사항 확인하기",
        reason="서버 간 연동 확인을 위한 예시 추천입니다.",
        rank=1,
        action=CandidateActionV2(
            resolution="NEW",
            name="준비 사항 확인",
            description="일정 전에 필요한 준비 사항을 확인하는 행동",
        ),
    )

    return RecommendationResponseV2(
        request_id=request.request_id,
        temp_event_id=request.temp_event_id,
        event_id=request.event_id,
        draft_revision=request.draft_revision,
        status="PARTIAL",
        event=request.event.model_copy(deep=True),
        context=RecommendationContextV2(),
        candidates=[candidate],
        warnings=[
            RecommendationIssueV2(
                code="STUB_RESPONSE",
                stage="PIPELINE",
                message="This is a stub response; LLM analysis and knowledge lookup were not performed.",
            )
        ],
        processing=RecommendationProcessingV2(
            duration_ms=int((perf_counter() - started_at) * 1000),
            llm_attempt_count=0,
        ),
    )
