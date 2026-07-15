from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.schemas.event_preview import (
    EventPreviewRequest,
    EventPreviewResponse,
    EventPreviewWarning,
)
from app.services.parser_service import ParsedEvent, parse_event_text


def preview_event(request: EventPreviewRequest) -> EventPreviewResponse:
    source_text = request.sourceText.strip()
    if not source_text:
        raise BusinessException(ErrorCode.COMMON_400)

    parsed_event = parse_event_text(source_text)
    warnings = _build_warnings(parsed_event)

    return EventPreviewResponse(
        sourceText=parsed_event.source_text,
        dateCandidate=parsed_event.date_candidate,
        timeCandidate=parsed_event.time_candidate,
        placeCandidate=parsed_event.place_candidate,
        toEmbedding=parsed_event.to_embedding,
        isAllDayCandidate=parsed_event.time_candidate is None,
        needsConfirmation=bool(warnings),
        warnings=warnings,
    )


def _build_warnings(parsed_event: ParsedEvent) -> list[EventPreviewWarning]:
    warnings = []

    if parsed_event.date_candidate is None:
        warnings.append(
            EventPreviewWarning(
                code="DATE_MISSING",
                message="날짜 입력이 필요합니다.",
            )
        )

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
