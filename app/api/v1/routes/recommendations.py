from __future__ import annotations

from fastapi import APIRouter

# from app.core.deps import RecommendationServiceDep
# from app.core.error_code import SuccessCode
# from app.core.responses import ApiResponse, success_response
# from app.core.route_helpers import map_runtime_error
# from app.schemas.recommendation import RecommendationRequest, RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# 참고용 입니다!!!!
# TODO: D102~D105 일정 준비/실행 항목 추천 API 구현
# @router.post(
#     "",
#     response_model=ApiResponse[RecommendationResponse],
#     summary="일정 준비/실행 항목 추천",
#     description=(
#         "parser → Neo4j 후보 조회 → Upstage LLM 정제 → recommender 후처리 "
#         "파이프라인으로 추천 항목을 생성합니다."
#     ),
# )
# async def create_recommendations(
#     body: RecommendationRequest,
#     service: RecommendationServiceDep,
# ) -> ApiResponse[RecommendationResponse]:
#     try:
#         result = await service.recommend(body)
#     except RuntimeError as exc:
#         raise map_runtime_error(exc) from exc
#     return success_response(result=result, success_code=SuccessCode.CREATED)
