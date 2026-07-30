from unittest.mock import Mock, patch

import pytest
import requests

from app.core.upstage_key_pool import UpstageKeyPool
from app.core.upstage_retry import upstage_retry
from app.services.recommendation.refinement_llm_service import (
    RefinementLLMError,
    RefinementLLMService,
)

SAMPLE_MESSAGES = [{"role": "user", "content": "refine these candidates"}]
SUCCESS_BODY = {
    "choices": [
        {
            "message": {
                "content": '{"refined_items": []}',
            },
        },
    ],
}


def _http_error(status_code: int) -> requests.HTTPError:
    response = Mock()
    response.status_code = status_code
    return requests.HTTPError(response=response)


def _success_response(content: str = '{"refined_items": []}') -> Mock:
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": content}}],
    }
    return response


def _error_response(status_code: int) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.raise_for_status.side_effect = _http_error(status_code)
    return response


def _build_service(
    keys: list[str | None],
    *,
    max_retries: int = 2,
) -> RefinementLLMService:
    pool = UpstageKeyPool(keys)
    service = RefinementLLMService()
    service._key_pool = pool

    original = RefinementLLMService._request_completion.__wrapped__

    @upstage_retry(pool, max_retries=max_retries, backoff_seconds=0)
    def _request_completion(
        messages: list[dict[str, str]],
        *,
        api_key: str,
    ) -> dict:
        return original(service, messages, api_key=api_key)

    service._request_completion = _request_completion
    return service


def test_complete_returns_stripped_content_on_success():
    service = _build_service(["key-a", "key-b"])

    with patch(
        "app.services.recommendation.refinement_llm_service.requests.post",
        return_value=_success_response('  {"refined_items": []}  '),
    ) as mock_post:
        result = service.complete(SAMPLE_MESSAGES)

    assert result == '{"refined_items": []}'
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer key-a"


def test_complete_rotates_key_and_succeeds_after_429():
    service = _build_service(["key-a", "key-b"])
    seen_keys: list[str] = []

    def fake_post(*_args, headers=None, **_kwargs):
        key = headers["Authorization"].removeprefix("Bearer ")
        seen_keys.append(key)

        if len(seen_keys) == 1:
            return _error_response(429)

        return _success_response()

    with patch(
        "app.services.recommendation.refinement_llm_service.requests.post",
        side_effect=fake_post,
    ):
        result = service.complete(SAMPLE_MESSAGES)

    assert result == '{"refined_items": []}'
    assert seen_keys == ["key-a", "key-b"]


def test_complete_raises_refinement_llm_error_when_retries_exhausted_on_503():
    service = _build_service(["key-a", "key-b"], max_retries=1)
    seen_keys: list[str] = []

    def fake_post(*_args, headers=None, **_kwargs):
        seen_keys.append(headers["Authorization"].removeprefix("Bearer "))
        return _error_response(503)

    with patch(
        "app.services.recommendation.refinement_llm_service.requests.post",
        side_effect=fake_post,
    ):
        with pytest.raises(RefinementLLMError, match="Upstage chat request failed."):
            service.complete(SAMPLE_MESSAGES)

    assert seen_keys == ["key-a", "key-b"]


def test_complete_does_not_retry_non_retryable_status():
    service = _build_service(["key-a", "key-b"])
    call_count = 0

    def fake_post(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        return _error_response(400)

    with patch(
        "app.services.recommendation.refinement_llm_service.requests.post",
        side_effect=fake_post,
    ):
        with pytest.raises(RefinementLLMError, match="Upstage chat request failed."):
            service.complete(SAMPLE_MESSAGES)

    assert call_count == 1


def test_complete_raises_refinement_llm_error_when_messages_empty():
    service = _build_service(["key-a"])

    with pytest.raises(RefinementLLMError, match="Chat messages must not be empty."):
        service.complete([])


def test_complete_raises_refinement_llm_error_when_api_key_not_configured():
    service = _build_service([None, ""])

    with pytest.raises(RefinementLLMError, match="Upstage API key is not configured."):
        service.complete(SAMPLE_MESSAGES)


def test_complete_raises_refinement_llm_error_on_invalid_response_shape():
    service = _build_service(["key-a"])

    with patch(
        "app.services.recommendation.refinement_llm_service.requests.post",
        return_value=_success_response(content="not used"),
    ) as mock_post:
        mock_post.return_value.json.return_value = {"unexpected": "shape"}

        with pytest.raises(RefinementLLMError, match="Upstage returned an invalid response."):
            service.complete(SAMPLE_MESSAGES)


def test_complete_raises_refinement_llm_error_on_empty_content():
    service = _build_service(["key-a"])

    with patch(
        "app.services.recommendation.refinement_llm_service.requests.post",
        return_value=_success_response(content="   "),
    ):
        with pytest.raises(RefinementLLMError, match="Upstage returned empty content."):
            service.complete(SAMPLE_MESSAGES)
