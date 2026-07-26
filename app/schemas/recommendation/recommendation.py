from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from app.schemas.types import SourceType, DateSource
from app.schemas.recommendation.temporal import ItemType


SuggestionStatus = Literal["ready", "empty", "error"]

# /api/v1/recommendations requestDTO
class RecommendationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    temp_event_id: str = Field(alias= "tempEventId")
    draft_revision: int = Field(alias= "draftRevision")
    event_title: str = Field(alias= "eventTitle", min_length=1)
    source_type: SourceType = Field(alias= "sourceType")
    start_date_candidate: date = Field(alias= "startDateCandidate")
    start_time_candidate: time | None = Field(default= None, alias= "startTimeCandidate")
    end_date_candidate: date | None = Field(default= None, alias= "endDateCandidate")
    end_time_candidate: time | None = Field(default= None, alias= "endTimeCandidate")
    start_date_source: DateSource | None = Field(default=None, alias="startDateSource")
    place_candidate: str | None = Field(default= None, alias= "placeCandidate")
    description: str | None = None
    embedding_words: list[str] = Field(default_factory=list, alias="embeddingWords")


class SuggestionItem(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    source_code: str = Field(alias="sourceCode")
    display_text: str = Field(alias="displayText")
    item_type: ItemType = Field(alias="itemType")
    offset_days: int | None = Field(default=None, alias="offsetDays")
    display_date: date | None = Field(default=None, alias="displayDate")
    action_type: str = Field(alias="actionType")
    target_type: str = Field(alias="targetType")
    default_timing: str = Field(alias="defaultTiming")
    selection_rank: int = Field(alias="selectionRank", ge=1, le=3)
    parent_temp_event_id: str = Field(alias="parentTempEventId")


# /api/v1/recommendations responseDTO
class RecommendationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    temp_event_id: str = Field(alias="tempEventId")
    draft_revision: int = Field(alias="draftRevision")
    suggestion_status: SuggestionStatus = Field(alias="suggestionStatus")
    suggestions: list[SuggestionItem] = Field(default_factory=list, max_length=3)
    errors: list[str] = Field(default_factory=list)

