import requests

from app.core.config import settings
from app.core.upstage_key_pool import upstage_key_pool
from app.core.upstage_retry import upstage_retry


class RefinementLLMError(Exception):
    """Upstage 추천 정제 호출 또는 응답 처리 실패."""


class RefinementLLMService:
    def __init__(self) -> None:
        self.model = settings.upstage_chat_model
        self.timeout_seconds = settings.upstage_chat_timeout_seconds
        self.base_url = "https://api.upstage.ai/v1/chat/completions"
        self._key_pool = upstage_key_pool

    def complete(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        if not messages:
            raise RefinementLLMError(
                "Chat messages must not be empty."
            )

        if not self._key_pool.is_configured:
            raise RefinementLLMError(
                "Upstage API key is not configured."
            )

        try:
            body = self._request_completion(messages)
        except requests.RequestException as exc:
            raise RefinementLLMError(
                "Upstage chat request failed."
            ) from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RefinementLLMError(
                "Upstage returned an invalid response."
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise RefinementLLMError(
                "Upstage returned empty content."
            )

        return content.strip()

    @upstage_retry(upstage_key_pool)
    def _request_completion(
        self,
        messages: list[dict[str, str]],
        *,
        api_key: str,
    ) -> dict:
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        return response.json()
