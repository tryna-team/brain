from __future__ import annotations

from fastapi import APIRouter

# from app.core.deps import ParserServiceDep
# from app.core.error_code import SuccessCode
# from app.core.responses import ApiResponse, success_response
# from app.core.route_helpers import map_runtime_error
# from app.schemas.parse import ParseScheduleRequest, ParseScheduleResponse

router = APIRouter(prefix="/parse", tags=["parse"])


# 참고용 입니다!!!!
# TODO: C101/C102 자연어 일정 1차 파싱 API 구현
# @router.post(
#     "",
#     response_model=ApiResponse[ParseScheduleResponse],
#     summary="자연어 일정 1차 파싱",
#     description="사용자 입력 문장에서 날짜/시간/제목/장소/일정 유형 후보를 추출합니다.",
# )
# async def parse_schedule(
#     body: ParseScheduleRequest,
#     service: ParserServiceDep,
# ) -> ApiResponse[ParseScheduleResponse]:
#     try:
#         result = await service.parse(body.source_text)
#     except RuntimeError as exc:
#         raise map_runtime_error(exc) from exc
#     return success_response(result=result, success_code=SuccessCode.OK)
