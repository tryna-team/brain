from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.event_preview import EventPreviewRequest
from app.services.event_preview_service import preview_event


def test_preview_event_returns_start_date_and_start_time_with_seconds():
    result = preview_event(EventPreviewRequest(eventTitle="금요일 3시 팀플 회의"))

    assert result.event_title == "금요일 3시 팀플 회의"
    assert result.start_date is not None
    assert result.end_date is None
    assert result.start_time == "15:00:00"
    assert result.end_time is None
    assert result.place_candidate is None
    assert result.to_embedding == ["팀플", "회의"]
    assert result.is_all_day_candidate is False


def test_preview_event_keeps_ambiguous_time_out_of_start_time():
    result = preview_event(EventPreviewRequest(eventTitle="내일 오후에 팀플 회의"))

    assert result.start_date is not None
    assert result.start_time is None
    assert result.is_all_day_candidate is True
    assert result.needs_confirmation is True
    assert any(warning.code == "TIME_AMBIGUOUS" for warning in result.warnings)


def test_preview_event_defaults_missing_date_to_today():
    result = preview_event(EventPreviewRequest(eventTitle="팀플 회의"))

    assert result.start_date == datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    assert result.needs_confirmation is False
    assert all(warning.code != "DATE_MISSING" for warning in result.warnings)


def test_preview_event_response_keeps_camel_case_json_contract():
    result = preview_event(EventPreviewRequest(eventTitle="금요일 3시 팀플 회의"))
    payload = result.model_dump(by_alias=True)

    assert payload["eventTitle"] == "금요일 3시 팀플 회의"
    assert payload["startDate"] is not None
    assert payload["startTime"] == "15:00:00"
    assert payload["placeCandidate"] is None
    assert payload["toEmbedding"] == ["팀플", "회의"]
    assert payload["isAllDayCandidate"] is False
    assert payload["needsConfirmation"] is False
