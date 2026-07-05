from __future__ import annotations

from fastapi import APIRouter

# from app.core.deps import ScheduleContextServiceDep
# from app.core.error_code import SuccessCode
# from app.core.responses import ApiResponse, success_response
# from app.core.route_helpers import map_runtime_error
# from app.schemas.schedule import ScheduleContextRequest, ScheduleContextResponse

router = APIRouter(prefix="/schedules", tags=["schedules"])


# TODO: 일정 맥락 분석 API 구현 (Neo4j 기반 맥락 구조화)
# @router.post(
#     "/context",
#     response_model=ApiResponse[ScheduleContextResponse],
#     summary="일정 맥락 분석",
#     description="파싱된 일정 정보를 Neo4j 지식 그래프에서 조회해 맥락을 구조화합니다.",
# )
# async def analyze_schedule_context(
#     body: ScheduleContextRequest,
#     service: ScheduleContextServiceDep,
# ) -> ApiResponse[ScheduleContextResponse]:
#     try:
#         result = await service.analyze_context(body)
#     except RuntimeError as exc:
#         raise map_runtime_error(exc) from exc
#     return success_response(result=result, success_code=SuccessCode.OK)
