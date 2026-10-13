import requests

from app.core.config import settings


class ImageOcrService:
    def __init__(self):
        self.base_url = "https://api.upstage.ai/v1/document-digitization"

    def extract_text(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        if not settings.upstage_api_key:
            raise RuntimeError("Upstage API 키가 설정되지 않았습니다.")

        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {settings.upstage_api_key}"
            },
            files={
                "document": (
                    filename,
                    image_bytes,
                    content_type,
                )
            },
            data={
                "model": "ocr"
            },
            timeout=60,
        )

        if not response.ok:
            print("UPSTAGE STATUS:", response.status_code)
            print("UPSTAGE ERROR:", response.text[:2000])

        response.raise_for_status()

        result = response.json()

        return result.get("text", "")


image_ocr_service = ImageOcrService()