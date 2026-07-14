from enum import Enum
from http import HTTPStatus


class ErrorCode(Enum):
    # 공통 에러 코드
    COMMON_400 = (HTTPStatus.BAD_REQUEST, "잘못된 요청입니다.")
    INTERNAL_AUTH_401 = (HTTPStatus.UNAUTHORIZED, "서버 간 인증에 실패했습니다.")
    COMMON_404 = (HTTPStatus.NOT_FOUND, "요청한 리소스를 찾을 수 없습니다.")
    COMMON_422 = (HTTPStatus.UNPROCESSABLE_ENTITY, "요청값 검증에 실패했습니다.")
    COMMON_500 = (HTTPStatus.INTERNAL_SERVER_ERROR, "서버 내부 오류가 발생했습니다.")


    # recommendation 에러 코드
    # D101 관련 에러코드
    EMBEDDING_400 = (HTTPStatus.BAD_REQUEST, "임베딩할 텍스트가 비어 있습니다.")
    EMBEDDING_503 = (HTTPStatus.SERVICE_UNAVAILABLE, "임베딩 모델 연동을 사용할 수 없습니다.")

    NEO4J_503 = (HTTPStatus.SERVICE_UNAVAILABLE, "Neo4j 연결을 사용할 수 없습니다.")
    LLM_503 = (HTTPStatus.SERVICE_UNAVAILABLE, "LLM 연동을 사용할 수 없습니다.")


    

    def __init__(self, status: HTTPStatus, message: str):
        self.status = status
        self.message = message

    @property
    def http_status(self) -> HTTPStatus:
        return self.status


class SuccessCode(Enum):
    OK = (HTTPStatus.OK, "요청이 성공했습니다.")
    CREATED = (HTTPStatus.CREATED, "요청이 성공했습니다.")

    def __init__(self, status: HTTPStatus, message: str):
        self.status = status
        self.message = message

    @property
    def http_status(self) -> HTTPStatus:
        return self.status
