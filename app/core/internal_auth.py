import secrets

from fastapi import Header

from app.core.config import settings
from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException

INTERNAL_API_KEY_HEADER = "X-Internal-Api-Key"


async def verify_internal_api_key(
    x_internal_api_key: str | None = Header(default=None, alias=INTERNAL_API_KEY_HEADER),
) -> None:
    if not settings.internal_api_key:
        raise BusinessException(ErrorCode.INTERNAL_AUTH_500)
    if not settings.internal_api_key.isascii():
        raise BusinessException(
            ErrorCode.INTERNAL_AUTH_500,
            "내부 API 인증 키는 ASCII 문자로 설정해야 합니다.",
        )

    if not x_internal_api_key or not x_internal_api_key.isascii() or not secrets.compare_digest(
        x_internal_api_key,
        settings.internal_api_key,
    ):
        raise BusinessException(ErrorCode.INTERNAL_AUTH_401)
