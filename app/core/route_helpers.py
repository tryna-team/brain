from __future__ import annotations

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException


def map_runtime_error(exc: RuntimeError, *, detail: str | None = None) -> BusinessException:
    """RuntimeError 메시지를 도메인별 ErrorCode로 매핑해 BusinessException으로 변환한다."""
    message = detail or str(exc)
    upper = message.upper()

    if "NEO4J" in upper:
        return BusinessException(ErrorCode.NEO4J_503, message)
    if "UPSTAGE" in upper or "LLM" in upper:
        return BusinessException(ErrorCode.LLM_503, message)

    return BusinessException(ErrorCode.COMMON_500, message)
