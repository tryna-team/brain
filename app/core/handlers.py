import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.core.responses import ApiResponse

logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def business_exception_handler(
        request: Request,
        exc: BusinessException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.error_code.status.value,
            content=ApiResponse.error(
                code=exc.error_code.name,
                message=exc.message,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=ErrorCode.COMMON_422.status.value,
            content=ApiResponse.error(
                code=ErrorCode.COMMON_422.name,
                message=ErrorCode.COMMON_422.message,
                data={"errors": exc.errors()},
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(
            "Unhandled server error: method=%s, path=%s",
            request.method,
            request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )

        return JSONResponse(
            status_code=ErrorCode.COMMON_500.status.value,
            content=ApiResponse.error(
                code=ErrorCode.COMMON_500.name,
                message=ErrorCode.COMMON_500.message,
            ).model_dump(),
        )
