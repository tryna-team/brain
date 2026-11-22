from time import perf_counter

from app.schemas.recommendation.v2.request import RecommendationRequestV2
from app.schemas.recommendation.v2.response import RecommendationResponseV2
from app.services.recommendation.v2.recommendation_llm_service import (
    RecommendationLLMError,
    RecommendationLLMService,
)
from app.services.recommendation.v2.recommendation_result_service import (
    build_error_response,
    build_recommendation_response,
)


def recommend(request: RecommendationRequestV2) -> RecommendationResponseV2:
    started_at = perf_counter()
    service = RecommendationLLMService()

    try:
        result = service.generate(request)
    except RecommendationLLMError as error:
        response = build_error_response(request, error, duration_ms=0)
    else:
        response = build_recommendation_response(request, result, duration_ms=0)

    response.processing.duration_ms = int((perf_counter() - started_at) * 1000)
    return response
