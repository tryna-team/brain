from unittest.mock import Mock

import pytest
import requests

from app.core.upstage_key_pool import UpstageKeyPool
from app.core.upstage_retry import upstage_retry


def test_acquire_round_robins_through_registered_keys():
    pool = UpstageKeyPool(["key-a", "key-b"])

    assert [pool.acquire() for _ in range(4)] == ["key-a", "key-b", "key-a", "key-b"]


def test_dedupes_keys_split_across_comma_separated_env_values():
    pool = UpstageKeyPool(["key-a,key-b", "key-b,key-c"])

    assert pool.keys == ["key-a", "key-b", "key-c"]


def test_ignores_missing_or_blank_env_values():
    pool = UpstageKeyPool([None, "", "  "])

    assert pool.is_configured is False
    assert len(pool) == 0
    assert pool.acquire() is None


def test_single_key_still_round_robins_to_itself():
    pool = UpstageKeyPool(["key-a", None])

    assert pool.is_configured is True
    assert [pool.acquire() for _ in range(3)] == ["key-a", "key-a", "key-a"]


def _http_error(status_code: int) -> requests.HTTPError:
    response = Mock()
    response.status_code = status_code
    return requests.HTTPError(response=response)


def test_upstage_retry_rotates_key_and_succeeds_after_429():
    pool = UpstageKeyPool(["key-a", "key-b"])
    seen_keys = []

    @upstage_retry(pool, max_retries=2, backoff_seconds=0)
    def call(*, api_key: str) -> str:
        seen_keys.append(api_key)
        if len(seen_keys) == 1:
            raise _http_error(429)
        return api_key

    result = call()

    assert result == "key-b"
    assert seen_keys == ["key-a", "key-b"]


def test_upstage_retry_raises_after_exhausting_retries_on_503():
    pool = UpstageKeyPool(["key-a", "key-b"])

    @upstage_retry(pool, max_retries=1, backoff_seconds=0)
    def call(*, api_key: str) -> str:
        raise _http_error(503)

    with pytest.raises(requests.HTTPError):
        call()


def test_upstage_retry_does_not_retry_non_retryable_status():
    pool = UpstageKeyPool(["key-a", "key-b"])
    call_count = 0

    @upstage_retry(pool, max_retries=2, backoff_seconds=0)
    def call(*, api_key: str) -> str:
        nonlocal call_count
        call_count += 1
        raise _http_error(400)

    with pytest.raises(requests.HTTPError):
        call()

    assert call_count == 1
