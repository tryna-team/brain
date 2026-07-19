# Upstage API 429/503 재시도 + 키 로테이션 데코레이터
#
# 데코레이션 대상 함수는 api_key를 키워드 인자로 받아야 한다:
#     def call(self, text: str, *, api_key: str): ...
#
# 요청이 429(Too Many Requests)/503(Service Unavailable)으로 실패하면
# UpstageKeyPool에서 다음 키를 꺼내 교체한 뒤 지수 백오프와 함께 재시도한다.

from __future__ import annotations

import functools
import time
from typing import Callable, TypeVar

import requests

from app.core.upstage_key_pool import UpstageKeyPool

T = TypeVar("T")

RETRYABLE_STATUS_CODES = {429, 503}


def upstage_retry(
    key_pool: UpstageKeyPool,
    *,
    max_retries: int = 2,
    backoff_seconds: float = 0.5,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc: requests.HTTPError | None = None

            for attempt in range(max_retries + 1):
                api_key = key_pool.acquire()

                try:
                    return func(*args, api_key=api_key, **kwargs)
                except requests.HTTPError as exc:
                    status = exc.response.status_code if exc.response is not None else None

                    if status not in RETRYABLE_STATUS_CODES or attempt == max_retries:
                        raise

                    last_exc = exc
                    time.sleep(backoff_seconds * (attempt + 1))

            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
