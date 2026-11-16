from __future__ import annotations

import json
from datetime import date

import requests
from pydantic import ValidationError

from app.core.config import settings
from app.core.upstage_key_pool import upstage_key_pool
from app.core.upstage_retry import upstage_retry
from app.schemas.ocr_event import OcrEventExtraction


UPSTAGE_CHAT_URL = "https://api.upstage.ai/v1/chat/completions"


SYSTEM_PROMPT = """
너는 한국어 행사 포스터 및 공지사항에서 일정 정보를 추출하는 AI다.

입력으로 PaddleOCR이 추출한 텍스트가 주어진다.
텍스트에는 줄바꿈 오류, 인식 오류, 불필요한 정보가 포함될 수 있다.

다음 규칙을 반드시 따른다.

1. 하나의 주요 행사 또는 일정만 추출한다.
2. 행사 제목, 날짜, 시간, 장소, 설명을 추출한다.
3. 신청 기간, 접수 마감일, 발표일 등을 실제 행사 날짜와 구분한다.
4. 텍스트에 없는 정보를 임의로 생성하지 않는다.
5. 확인할 수 없는 값은 null로 반환한다.
6. 종료 시간이 명시되지 않았다면 end_time은 null이다.
7. 종료 날짜가 명시되지 않았다면 end_date는 null이다.
8. 연도가 없는 날짜는 명확한 근거가 있을 때만 연도를 결정한다.
9. 날짜는 YYYY-MM-DD 형식으로 반환한다.
10. 시간은 HH:MM:SS 형식으로 반환한다.
11. OCR 인식 오류는 문맥상 명확한 경우에만 보정한다.
12. 반드시 JSON 객체 하나만 반환한다.
13. JSON 외의 설명이나 Markdown 코드 블록은 출력하지 않는다.

반환 형식:

{
  "title": null,
  "start_date": null,
  "end_date": null,
  "start_time": null,
  "end_time": null,
  "location": null,
  "description": null
}
"""


@upstage_retry(upstage_key_pool)
def _request_llm(
    ocr_text: str,
    reference_date: date,
    *,
    api_key: str | None,
) -> dict:
    """Upstage Solar에 OCR 텍스트 분석을 요청한다."""

    if not api_key:
        raise RuntimeError("Upstage API 키가 설정되지 않았습니다.")

    response = requests.post(
        UPSTAGE_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.upstage_chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"기준 날짜: {reference_date.isoformat()}\n\n"
                        f"OCR 추출 텍스트:\n{ocr_text}"
                    ),
                },
            ],
            "temperature": 0,
        },
        timeout=30,
    )

    if not response.ok:
        print(f"[Upstage API Error] Status: {response.status_code}")
        print(f"[Upstage API Error] Response: {response.text}")

    response.raise_for_status()

    return response.json()


def extract_event_from_ocr(
    ocr_text: str,
    reference_date: date | None = None,
) -> OcrEventExtraction:
    """OCR 텍스트에서 일정 정보를 추출한다."""

    if not ocr_text or not ocr_text.strip():
        raise ValueError("OCR 텍스트가 비어 있습니다.")

    reference_date = reference_date or date.today()

    response = _request_llm(
        ocr_text=ocr_text,
        reference_date=reference_date,
    )

    try:
        content = response["choices"][0]["message"]["content"]

        if not isinstance(content, str):
            raise ValueError("LLM 응답이 문자열이 아닙니다.")

        # Markdown 코드 블록이 포함된 경우 제거
        content = content.strip()

        if content.startswith("```"):
            lines = content.splitlines()

            if len(lines) >= 3 and lines[-1].strip() == "```":
                content = "\n".join(lines[1:-1]).strip()

        parsed_json = json.loads(content)

        return OcrEventExtraction.model_validate(parsed_json)

    except (
        KeyError,
        IndexError,
        TypeError,
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise ValueError(
            "LLM 일정 정보 추출 결과를 검증하지 못했습니다."
        ) from exc