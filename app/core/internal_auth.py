from fastapi import Header

from app.core.config import settings
from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException

INTERNAL_API_KEY_HEADER = "X-Internal-Api-Key"


async def verify_internal_api_key(
    x_internal_api_key: str | None = Header(default=None, alias=INTERNAL_API_KEY_HEADER),
) -> None:
    if not settings.internal_api_key:
        return
    if x_internal_api_key != settings.internal_api_key:
        raise BusinessException(ErrorCode.COMMON_401)
