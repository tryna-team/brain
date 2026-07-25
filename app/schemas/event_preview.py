from pydantic import BaseModel, ConfigDict, Field

from app.schemas.types import DateSource


class EventPreviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_title: str = Field(alias="eventTitle")


class EventPreviewWarning(BaseModel):
    code: str
    message: str


class EventPreviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_title: str = Field(alias="eventTitle")
    start_date: str | None = Field(default=None, alias="startDate")
    date_source: DateSource | None = Field(default=None, alias="dateSource")
    end_date: str | None = Field(default=None, alias="endDate")
    start_time: str | None = Field(default=None, alias="startTime")
    end_time: str | None = Field(default=None, alias="endTime")
    place_candidate: str | None = Field(default=None, alias="placeCandidate")
    to_embedding: list[str] = Field(alias="toEmbedding")
    is_all_day_candidate: bool = Field(alias="isAllDayCandidate")
    needs_confirmation: bool = Field(alias="needsConfirmation")
    warnings: list[EventPreviewWarning] = Field(default_factory=list)
