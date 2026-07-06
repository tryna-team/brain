from typing import Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.error_code import SuccessCode

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    code: str
    message: str
    data: T | None = None

    @classmethod
    def ok(
        cls,
        data: T | None = None,
        code: str = "COMMON_200",
        message: str = "요청이 성공했습니다.",
    ) -> "ApiResponse[T]":
        return cls(success=True, code=code, message=message, data=data)

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        data: BaseModel | dict | None = None,
    ) -> "ApiResponse[BaseModel | dict]":
        return cls(success=False, code=code, message=message, data=data)


def success_response(
    result: T | None = None,
    success_code: SuccessCode = SuccessCode.OK,
    message: str | None = None,
) -> JSONResponse:
    body = ApiResponse.ok(
        data=result,
        code=success_code.name,
        message=message or success_code.message,
    )
    return JSONResponse(
        status_code=success_code.http_status.value,
        content=body.model_dump(mode="json"),
    )
