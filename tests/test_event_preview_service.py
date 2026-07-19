from app.schemas.event_preview import EventPreviewRequest
from app.services.event_preview_service import preview_event


def test_preview_event_returns_start_date_and_start_time_with_seconds():
    result = preview_event(EventPreviewRequest(sourceText="금요일 3시 팀플 회의"))

    assert result.sourceText == "금요일 3시 팀플 회의"
    assert result.startDate is not None
    assert result.endDate is None
    assert result.startTime == "15:00:00"
    assert result.endTime is None
    assert result.placeCandidate is None
    assert result.toEmbedding == ["팀플", "회의"]
    assert result.isAllDayCandidate is False


def test_preview_event_keeps_ambiguous_time_out_of_start_time():
    result = preview_event(EventPreviewRequest(sourceText="내일 오후에 팀플 회의"))

    assert result.startDate is not None
    assert result.startTime is None
    assert result.isAllDayCandidate is True
    assert result.needsConfirmation is True
    assert any(warning.code == "TIME_AMBIGUOUS" for warning in result.warnings)
