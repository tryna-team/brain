# D101 임베딩 모델을 통한 일정 맥락 구조화

import requests

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.error_code import ErrorCode


class EmbeddingService:
    def __init__(self) -> None:
        self.api_key = settings.upstage_api_key
        self.model = settings.upstage_embedding_model
        self.base_url = "https://api.upstage.ai/v1/embeddings"

    def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise BusinessException(ErrorCode.EMBEDDING_400)

        if not self.api_key:
            raise BusinessException(ErrorCode.EMBEDDING_503)
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": text.strip(),
                },
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise BusinessException(ErrorCode.EMBEDDING_503) from exc

        try:
            body = response.json()
            embedding = body["data"][0]["embedding"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise BusinessException(ErrorCode.EMBEDDING_503) from exc

        return embedding