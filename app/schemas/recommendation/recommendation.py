from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.types import SourceType, DateSource

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

# /api/v1/recommendations responseDTO

