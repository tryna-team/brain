from datetime import date

from app.services.ocr.event_extraction_service import (
    extract_event_from_ocr,
)


OCR_TEXT = """
2026 AI 개발자 컨퍼런스

행사 일시
2026년 11월 15일 14:00~17:00

장소
코엑스 컨퍼런스룸

사전 등록 기간
10월 20일~11월 10일

참가비 무료
"""


def main():
    result = extract_event_from_ocr(
        ocr_text=OCR_TEXT,
        reference_date=date(2026, 10, 26),
    )

    print(
        result.model_dump_json(
            indent=2,
            exclude_none=False,
        )
    )


if __name__ == "__main__":
    main()