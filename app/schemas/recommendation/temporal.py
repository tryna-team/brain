from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recommendation.schedule_context import ScheduleContext


TemporalStatus = Literal[
    "SUCCESS",
    "NO_ITEMS",
    "ERROR",
]

ItemType = Literal[
    "TIMED_ACTION",
    "UNTIMED_PREP",
]


class TemporalRecommendationItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    source_code: str = Field(alias="sourceCode", min_length=1)
    display_text: str = Field(alias="displayText", min_length=1)
    item_type: ItemType = Field(alias="itemType")
    offset_days: int | None = Field(default=None, alias="offsetDays")
    display_date: date | None = Field(default=None, alias="displayDate")
    display_time: time | None = Field(default=None, alias="displayTime")
    action_type: str = Field(alias="actionType")
    target_type: str = Field(alias="targetType")
    suggestion_level: str = Field(alias="suggestionLevel")
    default_timing: str = Field(alias="defaultTiming")
    selection_rank: int = Field(alias="selectionRank", ge=1, le=3)


class TemporalValidationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    temp_event_id: str = Field(alias="tempEventId")
    draft_revision: int = Field(alias="draftRevision")
    temporal_status: TemporalStatus = Field(alias="temporalStatus")
    items: list[TemporalRecommendationItem] = Field(default_factory=list)
    schedule_context: ScheduleContext = Field(alias="scheduleContext")
    errors: list[str] = Field(default_factory=list)
