from datetime import date, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator

from app.schemas.event_preview import EventPreviewResponse
from app.schemas.recommendation.v2.base import ResponseModelV2


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("timezone must be a valid IANA timezone.") from exc
    return value


class EventInputV2(ResponseModelV2):

    title: str = Field(min_length=1)
    start_date: date | None = Field(default=None, alias="startDate")
    start_time: time | None = Field(default=None, alias="startTime")
    end_date: date | None = Field(default=None, alias="endDate")
    end_time: time | None = Field(default=None, alias="endTime")
    is_all_day: bool = Field(alias="isAllDay")
    timezone: str = Field(min_length=1)
    place: str | None = None
    description: str | None = None

    _validate_timezone = field_validator("timezone")(validate_timezone)


class RecommendationRequestV2(ResponseModelV2):
    request_id: str = Field(alias="requestId", min_length=1)
    owner_id: str = Field(alias="ownerId", min_length=1)
    temp_event_id: str | None = Field(default=None, alias="tempEventId", min_length=1)
    event_id: str | None = Field(default=None, alias="eventId", min_length=1)
    draft_revision: int = Field(alias="draftRevision", ge=0)
    original_text: str | None = Field(default=None, alias="originalText")
    event: EventInputV2
    parsing_result: EventPreviewResponse = Field(alias="parsingResult")

    @model_validator(mode="after")
    def validate_event_identity(self):
        if (self.temp_event_id is None) == (self.event_id is None):
            raise ValueError("Exactly one of tempEventId and eventId is required.")
        return self
