from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.types import SourceType

# /api/v1/recommendations requestDTO
class RecommendationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: int = Field(alias= "eventId")
    external_event_id : str | None = Field(default= None, alias= "externalEventId")
    source_type: SourceType = Field(alias= "sourceType")
    source_text: str = Field(alias= "sourceText", min_length=1)
    start_date: date = Field(alias= "startDate")
    start_time: time | None = Field(default= None, alias= "startTime")
    end_date: date | None = Field(default= None, alias= "endDate")
    end_time: time | None = Field(default= None, alias= "endTime")
    location: str | None = None
    description: str | None = None
    provider: str | None = None # external_event_id 값이 존재하면 provider 값도 존재해야함 해당 검증 로직은 service쪽에서 구현 예정
    embedding_words: list[str] = Field(alias="embeddingWords")
# /api/v1/recommendations responseDTO

