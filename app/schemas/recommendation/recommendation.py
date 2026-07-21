from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.types import SourceType

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
    place_candidate: str | None = Field(default= None, alias= "placeCandidate")
    description: str | None = None
    external_event_id : str | None = Field(default= None, alias= "externalEventId")
    provider: str | None = None # external_event_id 값이 존재하면 provider 값도 존재해야함 해당 검증 로직은 spring 서버에서 구현 예정
    embedding_words: list[str] = Field(default_factory=list, alias="embeddingWords")

# /api/v1/recommendations responseDTO

