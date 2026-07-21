# neo4j를 통해 조회한 추천 항목 후보
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.recommendation.schedule_context import ScheduleContext

MappingStatus = Literal["matched", "unmatched", "error"]
LookupStatus = Literal["success", "no_mapping", "no_candidates", "partial_error", "error"]

class MatchedBy(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_labels: list[str] = Field(alias= "sourceLabels")
    source_code: str = Field(alias= "sourceCode")
    suggestion_mode: str = Field(alias= "suggestionMode")
    reason: str

class RecommendationCandidate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str 
    name: str
    conditional_text: str = Field(alias= "conditionalText")
    description: str
    action_type: str = Field(alias= "actionType")
    target_type: str = Field(alias= "targetType")
    suggestion_level: str = Field(alias= "suggestionLevel")
    default_timing: str = Field(alias= "defaultTiming")
    default_rank: int | None = Field(default=None, alias="defaultRank")
    vector_score: float | None = Field(default=None, alias="vectorScore")
    matched_by: list[MatchedBy] = Field(default_factory=list, alias= "matchedBy")


class TypeCandidate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    code: str
    score: float


class CandidateSearchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    temp_event_id: str = Field(alias= "tempEventId")
    draft_revision: int = Field(alias= "draftRevision")
    mapping_status: MappingStatus = Field(alias= "mappingStatus")
    event_type_candidates: list[TypeCandidate] = Field(default_factory=list, alias= "eventTypeCandidates")
    selected_event_type: str | None = Field(default= None, alias= "selectedEventType")
    context_candidates: list[TypeCandidate] = Field(default_factory=list,alias= "contextCandidates")
    detected_contexts: list[str] = Field(default_factory=list, alias= "detectedContexts")
    resolved_contexts: list[str] = Field(default_factory=list,alias= "resolvedContexts")
    place_type_candidates: list[TypeCandidate] = Field(default_factory=list, alias= "placeTypeCandidates")
    selected_place_type: str | None = Field(default= None, alias= "selectedPlaceType")
    lookup_status: LookupStatus = Field(alias= "lookupStatus")
    recommendation_candidates: list[RecommendationCandidate] = Field(default_factory=list, alias= "recommendationCandidates")
    schedule_context: ScheduleContext = Field(alias= "scheduleContext")
    errors: list[str] = Field(default_factory=list)
