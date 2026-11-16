from typing import Literal

from pydantic import Field, model_validator

from app.schemas.recommendation.v2.base import ResponseModelV2

Resolution = Literal["EXISTING", "NEW", "UNKNOWN"]


class InterpretationEvidenceV2(ResponseModelV2):
    source: Literal["USER_CONFIRMED", "RULE_PARSED", "LLM_INFERRED", "UNKNOWN"]
    text: str | None = None
    uncertainty: str | None = None


class ActivityResolutionV2(ResponseModelV2):
    activity_ref: str = Field(alias="activityRef", min_length=1)
    resolution: Resolution
    activity_id: str | None = Field(default=None, alias="activityId", min_length=1)
    name: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    evidence: InterpretationEvidenceV2

    @model_validator(mode="after")
    def validate_resolution(self):
        if (self.resolution == "EXISTING") != (self.activity_id is not None):
            raise ValueError("Only EXISTING activities require activityId.")
        if self.resolution in ("EXISTING", "NEW") and self.name is None:
            raise ValueError("EXISTING/NEW activities require name.")
        if self.resolution == "NEW" and self.description is None:
            raise ValueError("NEW activities require description.")
        return self


class EntityResolutionV2(ResponseModelV2):
    entity_ref: str = Field(alias="entityRef", min_length=1)
    resolution: Resolution
    entity_id: str | None = Field(default=None, alias="entityId", min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["PERSON", "PLACE", "OBJECT", "ORGANIZATION", "SUBJECT", "OTHER", "UNKNOWN"]
    role: Literal["RECIPIENT", "TARGET_OBJECT", "LOCATION", "PERFORMER", "SUBJECT", "UNKNOWN"]
    activity_refs: list[str] = Field(default_factory=list, alias="activityRefs")
    identity_evidence: InterpretationEvidenceV2 = Field(alias="identityEvidence")
    role_evidence: InterpretationEvidenceV2 = Field(alias="roleEvidence")

    @model_validator(mode="after")
    def validate_resolution(self):
        if (self.resolution == "EXISTING") != (self.entity_id is not None):
            raise ValueError("Only EXISTING entities require entityId.")
        return self


class ContextAttributeV2(ResponseModelV2):
    value: str | bool | int | float | None = Field(allow_inf_nan=False)
    evidence: InterpretationEvidenceV2


class RecommendationContextV2(ResponseModelV2):
    activities: list[ActivityResolutionV2] = Field(default_factory=list)
    entities: list[EntityResolutionV2] = Field(default_factory=list)
    attributes: dict[str, ContextAttributeV2] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self):
        activity_refs = [item.activity_ref for item in self.activities]
        entity_refs = [item.entity_ref for item in self.entities]
        if len(activity_refs) != len(set(activity_refs)):
            raise ValueError("activityRef must be unique.")
        if len(entity_refs) != len(set(entity_refs)):
            raise ValueError("entityRef must be unique.")
        for entity in self.entities:
            if not set(entity.activity_refs).issubset(activity_refs):
                raise ValueError("Entity activityRefs must reference existing activityRef values.")
        return self
