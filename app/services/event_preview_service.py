from datetime import date, timedelta

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.schemas.event_preview import (
    EventPreviewRequest,
    EventPreviewResponse,
    EventPreviewWarning,
)


def preview_event(request: EventPreviewRequest) -> EventPreviewResponse:
    source_text = request.sourceText.strip()
    if not source_text:
        raise BusinessException(ErrorCode.COMMON_400)

    date_candidate = _extract_date(source_text)
    time_candidate = _extract_time(source_text)
    title_candidate = _extract_title(source_text)
    event_type_candidate = _extract_event_type(source_text)
    warnings = _build_warnings(date_candidate)

    return EventPreviewResponse(
        sourceText=source_text,
        titleCandidate=title_candidate,
        dateCandidate=date_candidate,
        timeCandidate=time_candidate,
        placeCandidate=None,
        eventTypeCandidate=event_type_candidate,
        isAllDayCandidate=time_candidate is None,
        needsConfirmation=bool(warnings),
        warnings=warnings,
    )


def _extract_title(source_text: str) -> str:
    if "팀플" in source_text and "회의" in source_text:
        return "팀플 회의"
    return source_text


def _extract_event_type(source_text: str) -> str | None:
    if "회의" in source_text or "미팅" in source_text:
        return "meeting"
    if "생일" in source_text:
        return "birthday"
    return None


def _extract_date(source_text: str) -> str | None:
    today = date.today()
    if "오늘" in source_text:
        return today.isoformat()
    if "내일" in source_text:
        return (today + timedelta(days=1)).isoformat()
    if "금요일" in source_text:
        return _next_weekday(today, 4).isoformat()
    return None


def _extract_time(source_text: str) -> str | None:
    if "오전 10시" in source_text or "10시" in source_text:
        return "10:00"
    if "오후 3시" in source_text or "3시" in source_text:
        return "15:00"
    if "저녁 7시" in source_text or "오후 7시" in source_text or "7시" in source_text:
        return "19:00"
    return None


def _next_weekday(base_date: date, weekday: int) -> date:
    days_until = (weekday - base_date.weekday()) % 7
    return base_date + timedelta(days=days_until)


def _build_warnings(date_candidate: str | None) -> list[EventPreviewWarning]:
    if date_candidate is not None:
        return []
    return [
        EventPreviewWarning(
            code="DATE_MISSING",
            message="날짜 후보를 찾지 못했습니다.",
        )
    ]

