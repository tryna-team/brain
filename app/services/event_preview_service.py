from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.schemas.event_preview import (
    EventPreviewRequest,
    EventPreviewResponse,
    EventPreviewWarning,
)
from app.services.parser_service import ParsedEvent, parse_event_text


ASIA_SEOUL = ZoneInfo("Asia/Seoul")
TIME_PART_COUNT = 2
TIME_WITH_SECONDS_PART_COUNT = 3


def preview_event(request: EventPreviewRequest) -> EventPreviewResponse:
    source_text = request.sourceText.strip()
    if not source_text:
        raise BusinessException(ErrorCode.COMMON_400)

    parsed_event = parse_event_text(source_text)
    warnings = _build_warnings(parsed_event)
    start_date = parsed_event.date_candidate or datetime.now(ASIA_SEOUL).date().isoformat()
    start_time = _format_time_with_seconds(parsed_event.time_candidate)

    return EventPreviewResponse(
        sourceText=parsed_event.source_text,
        startDate=start_date,
        endDate=None,
        startTime=start_time,
        endTime=None,
        placeCandidate=parsed_event.place_candidate,
        toEmbedding=parsed_event.to_embedding,
        isAllDayCandidate=start_time is None,
        needsConfirmation=bool(warnings),
        warnings=warnings,
    )


def _build_warnings(parsed_event: ParsedEvent) -> list[EventPreviewWarning]:
    warnings = []


    if parsed_event.is_past_date:
        warnings.append(
            EventPreviewWarning(
                code="PAST_DATE",
                message="과거 날짜로 해석되었습니다. 저장 전 확인이 필요합니다.",
            )
        )

    if parsed_event.is_time_ambiguous:
        warnings.append(
            EventPreviewWarning(
                code="TIME_AMBIGUOUS",
                message="정확한 시간 확인이 필요합니다.",
            )
        )

    return warnings


def _format_time_with_seconds(time_candidate: str | None) -> str | None:
    if time_candidate is None:
        return None

    time_parts = time_candidate.split(":")
    if not all(part.isdigit() for part in time_parts):
        return None

    if len(time_parts) == TIME_PART_COUNT:
        hour, minute = time_parts
        return f"{hour.zfill(2)}:{minute.zfill(2)}:00"

    if len(time_parts) == TIME_WITH_SECONDS_PART_COUNT:
        hour, minute, second = time_parts
        return f"{hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}"

    return None
