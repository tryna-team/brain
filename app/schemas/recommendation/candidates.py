# neo4j를 통해 조회한 추천 항목 후보

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCandidate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    template_id: str = Field(alias="templateId")
    title: str
    base_item_type: str = Field(alias="baseItemType")
    offset_days: int | None = Field(default=None, alias="offsetDays")
    score: int
    source_relations: list[str] = Field(
        default_factory=list,
        alias="sourceRelations",
    )


class CandidateSearchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: int = Field(alias="eventId")
    candidates: list[RecommendationCandidate] = Field(default_factory=list)