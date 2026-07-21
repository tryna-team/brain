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
    event_title = request.event_title.strip()
    if not event_title:
        raise BusinessException(ErrorCode.COMMON_400)

    parsed_event = parse_event_text(event_title)
    warnings = _build_warnings(parsed_event)
    start_date = parsed_event.start_date or datetime.now(ASIA_SEOUL).date().isoformat()
    start_time = _format_time_with_seconds(parsed_event.start_time)

    return EventPreviewResponse(
        event_title=parsed_event.source_text,
        start_date=start_date,
        end_date=parsed_event.end_date,
        start_time=start_time,
        end_time=_format_time_with_seconds(parsed_event.end_time),
        place_candidate=parsed_event.place_candidate,
        to_embedding=parsed_event.to_embedding,
        is_all_day_candidate=start_time is None,
        needs_confirmation=bool(warnings),
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
