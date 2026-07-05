from app.global_exception.error_code import ErrorCode


class BusinessException(Exception):
    def __init__(self, error_code: ErrorCode, message: str | None = None):
        self.error_code = error_code
        self.message = message or error_code.message
        super().__init__(self.message)
