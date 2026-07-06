from app.config import Settings, settings
from app.core.error_code import ErrorCode, SuccessCode
from app.core.exceptions import BusinessException

# TODO: app.core.codes 모듈로 통합 시 아래 import로 교체
# from app.core.codes import ErrorCode, SuccessCode

# TODO: app.core.config 모듈 생성 후 Settings를 core로 이동하고 아래 import로 교체
# from app.core.config import Settings, get_settings, settings

# TODO: get_settings() 팩토리 함수 구현 (FastAPI Depends용)
# def get_settings() -> Settings:
#     return settings


# TODO: Brain 서버는 Neo4j 기반.
#       DB 세션 대신 Neo4j 클라이언트 의존성은 app.core.deps 참고.
# from app.core.database import (
#     AsyncSessionLocal,
#     Base,
#     async_engine,
#     get_async_db_session,
# )


# TODO: 예외 계층 확장 시 아래 import 활성화
# from app.core.exceptions import (
#     CustomException,
#     DatabaseException,
#     FileException,
#     ValidationException,
#     create_http_exception,
# )

__all__ = [
    "ErrorCode",
    "SuccessCode",
    "Settings",
    "settings",
    "BusinessException",
    # "get_settings",
    # "Base",
    # "async_engine",
    # "AsyncSessionLocal",
    # "get_async_db_session",
    # "CustomException",
    # "ValidationException",
    # "DatabaseException",
    # "FileException",
    # "create_http_exception",
]
