from fastapi import APIRouter

from app.schemas.recommendation.v2.request import RecommendationRequestV2
from app.schemas.recommendation.v2.response import RecommendationResponseV2
from app.services.recommendation.v2.recommendation_service import recommend


router = APIRouter(tags=["Recommendation V2"])


@router.post("/recommendations", response_model=RecommendationResponseV2)
def get_recommendations(request: RecommendationRequestV2) -> RecommendationResponseV2:
    return recommend(request)
