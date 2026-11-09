from datetime import date as Date, time as Time
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.recommendation.v2.base import ResponseModelV2
from app.schemas.recommendation.v2.request import validate_timezone


class CandidateActionV2(ResponseModelV2):
    resolution: Literal["EXISTING", "NEW"]
    action_id: str | None = Field(default=None, alias="actionId", min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None

    @model_validator(mode="after")
    def validate_resolution(self):
        if (self.resolution == "EXISTING") != (self.action_id is not None):
            raise ValueError("Only EXISTING actions require actionId.")
        return self


class RuleReferenceV2(ResponseModelV2):
    rule_id: str = Field(alias="ruleId", min_length=1)
    version: int = Field(ge=1)


class CandidateTimingV2(ResponseModelV2):
    date: Date
    time: Time | None = None
    timezone: str = Field(min_length=1)

    _validate_timezone = field_validator("timezone")(validate_timezone)


class RecommendationCandidateV2(ResponseModelV2):
    candidate_id: UUID = Field(alias="candidateId")
    display_text: str = Field(alias="displayText", min_length=1)
    reason: str = Field(min_length=1)
    rank: int = Field(ge=1, le=10)
    activity_refs: list[str] = Field(default_factory=list, alias="activityRefs")
    entity_refs: list[str] = Field(default_factory=list, alias="entityRefs")
    action: CandidateActionV2
    rule: RuleReferenceV2 | None = None
    timing: CandidateTimingV2 | None = None

    @model_validator(mode="after")
    def validate_rule_action(self):
        if self.rule is not None and self.action.resolution != "EXISTING":
            raise ValueError("An approved rule must reference an existing action.")
        return self
