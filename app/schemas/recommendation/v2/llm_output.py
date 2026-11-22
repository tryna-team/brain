from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from app.schemas.recommendation.v2.base import ResponseModelV2
from app.schemas.recommendation.v2.candidate import (
    CandidateActionV2,
    CandidateTimingV2,
    RuleReferenceV2,
)
from app.schemas.recommendation.v2.context import (
    InterpretationEvidenceV2,
    RecommendationContextV2,
)


class LLMCandidateV2(ResponseModelV2):
    candidate_ref: str = Field(alias="candidateRef", min_length=1)
    display_text: str = Field(alias="displayText", min_length=1)
    reason: str = Field(min_length=1)
    rank: int = Field(ge=1, le=10)
    activity_refs: list[str] = Field(default_factory=list, alias="activityRefs")
    entity_refs: list[str] = Field(default_factory=list, alias="entityRefs")
    action: CandidateActionV2
    rule: RuleReferenceV2 | None = None
    timing: CandidateTimingV2 | None = None
    timing_evidence: InterpretationEvidenceV2 | None = Field(default=None, alias="timingEvidence")

    @model_validator(mode="after")
    def validate_candidate(self):
        if self.rule is not None and self.action.resolution != "EXISTING":
            raise ValueError("An approved rule must reference an existing action.")
        if (self.timing is None) != (self.timing_evidence is None):
            raise ValueError("timing and timingEvidence must be provided together.")
        return self


class ActivityProposalV2(ResponseModelV2):
    kind: Literal["ACTIVITY"]
    activity_ref: str = Field(alias="activityRef", min_length=1)
    reason: str = Field(min_length=1)


class ActionProposalV2(ResponseModelV2):
    kind: Literal["ACTION"]
    candidate_ref: str = Field(alias="candidateRef", min_length=1)
    reason: str = Field(min_length=1)


class RuleProposalV2(ResponseModelV2):
    kind: Literal["PREPARATION_RULE"]
    name: str = Field(min_length=1)
    activity_ref: str = Field(alias="activityRef", min_length=1)
    candidate_ref: str = Field(alias="candidateRef", min_length=1)
    condition_text: str | None = Field(default=None, alias="conditionText", min_length=1)
    timing_text: str | None = Field(default=None, alias="timingText", min_length=1)
    reason: str = Field(min_length=1)


KnowledgeProposalV2 = Annotated[
    ActivityProposalV2 | ActionProposalV2 | RuleProposalV2,
    Field(discriminator="kind"),
]


class LLMRecommendationOutputV2(ResponseModelV2):
    context: RecommendationContextV2
    candidates: list[LLMCandidateV2] = Field(max_length=10)
    knowledge_proposals: list[KnowledgeProposalV2] = Field(default_factory=list, alias="knowledgeProposals")

    @model_validator(mode="after")
    def validate_references(self):
        activities = {item.activity_ref: item for item in self.context.activities}
        entities = {item.entity_ref for item in self.context.entities}
        candidates = {item.candidate_ref: item for item in self.candidates}
        if len(candidates) != len(self.candidates):
            raise ValueError("candidateRef must be unique.")
        if [item.rank for item in self.candidates] != list(range(1, len(self.candidates) + 1)):
            raise ValueError("Candidates must be ordered by consecutive rank values.")
        for candidate in self.candidates:
            if not set(candidate.activity_refs).issubset(activities):
                raise ValueError("Candidate activityRefs must reference context activities.")
            if not set(candidate.entity_refs).issubset(entities):
                raise ValueError("Candidate entityRefs must reference context entities.")
        for proposal in self.knowledge_proposals:
            if isinstance(proposal, (ActivityProposalV2, RuleProposalV2)):
                activity = activities.get(proposal.activity_ref)
                if activity is None or activity.resolution == "UNKNOWN":
                    raise ValueError("Knowledge proposals require a resolved activity reference.")
                if isinstance(proposal, ActivityProposalV2) and activity.resolution != "NEW":
                    raise ValueError("Activity proposals require a NEW activity.")
            if isinstance(proposal, (ActionProposalV2, RuleProposalV2)):
                candidate = candidates.get(proposal.candidate_ref)
                if candidate is None:
                    raise ValueError("Knowledge proposals must reference an existing candidateRef.")
                if isinstance(proposal, ActionProposalV2) and candidate.action.resolution != "NEW":
                    raise ValueError("Action proposals require a NEW action.")
                if isinstance(proposal, RuleProposalV2) and proposal.activity_ref not in candidate.activity_refs:
                    raise ValueError("Rule activityRef must belong to the referenced candidate.")
        return self


class RawLLMRecommendationOutputV2(ResponseModelV2):
    context: RecommendationContextV2
    candidates: list[JsonValue]
    knowledge_proposals: list[JsonValue] = Field(default_factory=list, alias="knowledgeProposals")
