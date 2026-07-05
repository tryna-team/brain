from typing import Generic, TypeVar

from pydantic import BaseModel

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
