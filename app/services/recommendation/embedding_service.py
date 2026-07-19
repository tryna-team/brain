# D101 임베딩 모델을 통한 일정 맥락 구조화

import requests

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.error_code import ErrorCode
from app.core.upstage_key_pool import upstage_key_pool
from app.core.upstage_retry import upstage_retry


class EmbeddingService:
    def __init__(self) -> None:
        self.model = settings.upstage_embedding_model
        self.base_url = "https://api.upstage.ai/v1/embeddings"
        self._key_pool = upstage_key_pool

    def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise BusinessException(ErrorCode.EMBEDDING_400)

        if not self._key_pool.is_configured:
            raise BusinessException(ErrorCode.EMBEDDING_503)

        try:
            body = self._request_embedding(text.strip())
        except requests.RequestException as exc:
            raise BusinessException(ErrorCode.EMBEDDING_503) from exc

        try:
            embedding = body["data"][0]["embedding"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise BusinessException(ErrorCode.EMBEDDING_503) from exc

        return embedding

    @upstage_retry(upstage_key_pool)
    def _request_embedding(self, text: str, *, api_key: str) -> dict:
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": text,
            },
            timeout=10,
        )
        response.raise_for_status()

        return response.json()
