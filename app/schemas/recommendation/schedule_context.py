from pydantic import BaseModel, ConfigDict, Field
from app.schemas.types import SourceType, ConfidenceLevel

# D101 일정 맥락 구조화 결과 DTO
class ScheduleContextResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    event_id: int = Field(alias= "eventId")
    source_type: SourceType = Field(alias= "sourceType")
    event_type_candidate: str = Field(alias= "eventTypeCandidate")
    context_candidates: list[str] = Field(default_factory=list, alias= "contextCandidates")
    place_type_candidate: str | None = Field(default= None, alias= "placeTypeCandidate")
    confidence_level: ConfidenceLevel = Field(alias= "confidenceLevel")
