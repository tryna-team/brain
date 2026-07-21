# Upstage API 멀티 키 Round-Robin 풀
#
# UPSTAGE_API_KEY, UPSTAGE_API_KEY_MULTI 두 환경변수(각 값은 콤마로 여러 키 나열 가능)를
# 모아 하나의 풀로 관리하고, 요청마다 acquire()로 다음 키를 순환 배분한다.
# 단일 키에 요청이 몰려 발생하는 Rate Limit(429) 병목을 완화하기 위한 용도.

from __future__ import annotations

import itertools
import threading

from app.core.config import settings


class UpstageKeyPool:
    def __init__(self, raw_keys: list[str | None]) -> None:
        keys: list[str] = []

        for raw in raw_keys:
            if not raw:
                continue

            for key in raw.split(","):
                key = key.strip()
                if key and key not in keys:
                    keys.append(key)

        self._keys = keys
        self._lock = threading.Lock()
        self._cycle = itertools.cycle(self._keys) if self._keys else None

    @property
    def keys(self) -> list[str]:
        return list(self._keys)

    @property
    def is_configured(self) -> bool:
        return bool(self._keys)

    def __len__(self) -> int:
        return len(self._keys)

    def acquire(self) -> str | None:
        """다음 키를 Round-Robin 방식으로 꺼낸다. 등록된 키가 없으면 None을 반환한다."""
        if self._cycle is None:
            return None

        with self._lock:
            return next(self._cycle)


upstage_key_pool = UpstageKeyPool([settings.upstage_api_key, settings.upstage_api_key_multi])
