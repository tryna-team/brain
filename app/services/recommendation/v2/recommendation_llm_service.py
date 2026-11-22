from dataclasses import dataclass
import json
import logging
from typing import Literal

import requests
from pydantic import ValidationError

from app.core.config import settings
from app.core.upstage_key_pool import UpstageKeyPool, upstage_key_pool
from app.schemas.recommendation.v2.llm_output import RawLLMRecommendationOutputV2
from app.schemas.recommendation.v2.request import RecommendationRequestV2
from app.services.recommendation.prompts.recommendation_v2_prompt import (
    PROMPT_VERSION,
    build_recommendation_messages,
)

logger = logging.getLogger(__name__)


def _validation_error_details(exc: ValidationError) -> list[dict]:
    # attributes 같은 자유 키에는 개인 정보가 들어갈 수 있으므로 경로에서도 숨긴다.
    schema = RawLLMRecommendationOutputV2.model_json_schema(by_alias=True)
    field_names = set(schema.get("properties", {}))
    for definition in schema.get("$defs", {}).values():
        field_names.update(definition.get("properties", {}))
    return [
        {
            "loc": [part if isinstance(part, int) or part in field_names else "<key>"
                    for part in error["loc"]],
            "type": error["type"],
        }
        for error in exc.errors(include_input=False, include_context=False, include_url=False)[:20]
    ]

LLMErrorCode = Literal[
    "NOT_CONFIGURED", "TIMEOUT", "REQUEST_FAILED", "INVALID_RESPONSE",
    "EMPTY_CONTENT", "INCOMPLETE_OUTPUT", "INVALID_OUTPUT",
]


class RecommendationLLMError(Exception):
    def __init__(self, code: LLMErrorCode, message: str, *, llm_attempt_count: int) -> None:
        super().__init__(message)
        self.code = code
        self.llm_attempt_count = llm_attempt_count


@dataclass(frozen=True)
class RecommendationLLMResult:
    output: RawLLMRecommendationOutputV2
    llm_attempt_count: int


class RecommendationLLMService:

    def __init__(self, *, key_pool: UpstageKeyPool | None = None) -> None:
        self.model = settings.upstage_chat_model
        self.timeout_seconds = settings.upstage_chat_timeout_seconds
        self.base_url = "https://api.upstage.ai/v1/chat/completions"
        self._key_pool = key_pool if key_pool is not None else upstage_key_pool

    def generate(self, request: RecommendationRequestV2) -> RecommendationLLMResult:
        api_key = self._key_pool.acquire()

        if api_key is None:
            raise RecommendationLLMError(
                "NOT_CONFIGURED", "Upstage API key is not configured.", llm_attempt_count=0,
            )

        messages = build_recommendation_messages(request)
        
        try:
            response = requests.post(
                self.base_url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise RecommendationLLMError(
                "TIMEOUT", "Upstage chat request timed out.", llm_attempt_count=1,
            ) from exc
        except requests.RequestException as exc:
            raise RecommendationLLMError(
                "REQUEST_FAILED", "Upstage chat request failed.", llm_attempt_count=1,
            ) from exc

        try:
            body = response.json()
            choice = body["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            raise RecommendationLLMError(
                "INVALID_RESPONSE", "Upstage returned an invalid response.", llm_attempt_count=1,
            ) from exc

        if finish_reason not in (None, "stop"):
            raise RecommendationLLMError(
                "INCOMPLETE_OUTPUT", "Upstage did not complete the requested output.", llm_attempt_count=1,
            )
        if not isinstance(content, str) or not content.strip():
            raise RecommendationLLMError(
                "EMPTY_CONTENT", "Upstage returned empty or non-text content.", llm_attempt_count=1,
            )

        try:
            output = RawLLMRecommendationOutputV2.model_validate_json(content)
        except ValidationError as exc:
            logger.warning(
                "Recommendation LLM output validation failed: %s",
                json.dumps({
                    "requestId": request.request_id,
                    "model": self.model,
                    "promptVersion": PROMPT_VERSION,
                    "errorCount": exc.error_count(),
                    "errors": _validation_error_details(exc),
                }, ensure_ascii=False),
            )
            raise RecommendationLLMError(
                "INVALID_OUTPUT", "LLM output does not match the expected JSON structure.", llm_attempt_count=1,
            ) from exc

        return RecommendationLLMResult(output=output, llm_attempt_count=1)
