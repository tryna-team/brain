from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recommendation.schedule_context import ScheduleContext


RefinementStatus = Literal[
    "success",
    "no_candidates",
    "fallback",
    "error",
]


class LLMRefinedItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    source_code: str = Field(alias="sourceCode", min_length=1)
    display_text: str = Field(alias="displayText", min_length=1)


class LLMRefinementResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refined_items: list[LLMRefinedItem] = Field(alias="refinedItems")


class RefinementModelMeta(BaseModel):
    provider: Literal["upstage"] = "upstage"
    model: str


class RefinedRecommendationItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    source_code: str = Field(alias="sourceCode", min_length=1)
    display_text: str = Field(alias="displayText", min_length=1)
    action_type: str = Field(alias="actionType")
    target_type: str = Field(alias="targetType")
    suggestion_level: str = Field(alias="suggestionLevel")
    default_timing: str = Field(alias="defaultTiming")
    offset_days: int | None = Field(default=None, alias="offsetDays")
    selection_rank: int = Field(alias="selectionRank", ge=1, le=3)


class RecommendationRefinementResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    temp_event_id: str = Field(alias="tempEventId")
    draft_revision: int = Field(alias="draftRevision")
    refinement_status: RefinementStatus = Field(alias="refinementStatus")
    prompt_version: str = Field(alias="promptVersion")
    few_shot_version: str = Field(alias="fewShotVersion")
    model_meta: RefinementModelMeta = Field(alias="modelMeta")
    refined_items: list[RefinedRecommendationItem] = Field(default_factory=list, alias="refinedItems", max_length=3)
    schedule_context: ScheduleContext = Field(alias="scheduleContext")
    errors: list[str] = Field(default_factory=list)
