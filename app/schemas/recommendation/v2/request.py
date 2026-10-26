from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from app.schemas.types import DateSource

SourceType = Literal["USER_NATURAL_LANGUAGE", "USER_MANUAL_EDIT"]

# /api/v2/recommendations requestDTO
class RecommendationRequestV2(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    temp_event_id: str = Field(alias= "tempEventId", min_length=1)
    draft_revision: int = Field(alias= "draftRevision", ge=0)
    event_title: str = Field(alias= "eventTitle", min_length=1)
    source_type: SourceType = Field(alias= "sourceType")
    original_text: str | None = Field(default=None, alias="originalText")
    start_date_candidate: date = Field(alias= "startDateCandidate")
    start_time_candidate: time | None = Field(default= None, alias= "startTimeCandidate")
    end_date_candidate: date | None = Field(default= None, alias= "endDateCandidate")
    end_time_candidate: time | None = Field(default= None, alias= "endTimeCandidate")
    start_date_source: DateSource | None = Field(default=None, alias="startDateSource")
    place_candidate: str | None = Field(default= None, alias= "placeCandidate")
    description: str | None = None
    embedding_words: list[str] = Field(default_factory=list, alias="embeddingWords")