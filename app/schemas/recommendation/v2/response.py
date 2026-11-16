from typing import Literal

from pydantic import Field, model_validator

from app.schemas.recommendation.v2.base import ResponseModelV2
from app.schemas.recommendation.v2.candidate import RecommendationCandidateV2
from app.schemas.recommendation.v2.context import RecommendationContextV2
from app.schemas.recommendation.v2.request import EventInputV2


class RecommendationIssueV2(ResponseModelV2):
    code: str = Field(min_length=1)
    stage: Literal["INPUT", "RETRIEVAL", "LLM", "VALIDATION", "KNOWLEDGE_STORAGE", "PIPELINE"]
    message: str = Field(min_length=1)


class RecommendationProcessingV2(ResponseModelV2):
    duration_ms: int = Field(alias="durationMs", ge=0)
    llm_attempt_count: int = Field(alias="llmAttemptCount", ge=0)


class RecommendationResponseV2(ResponseModelV2):
    contract_version: str = Field(default="2.0", alias="contractVersion", min_length=1)
    policy_version: str = Field(default="recommendation-v2.0", alias="policyVersion", min_length=1)
    request_id: str = Field(alias="requestId", min_length=1)
    temp_event_id: str | None = Field(default=None, alias="tempEventId", min_length=1)
    event_id: str | None = Field(default=None, alias="eventId", min_length=1)
    draft_revision: int = Field(alias="draftRevision", ge=0)
    status: Literal["READY", "EMPTY", "PARTIAL", "ERROR"]
    event: EventInputV2
    context: RecommendationContextV2 | None = None
    candidates: list[RecommendationCandidateV2] = Field(default_factory=list, max_length=10)
    warnings: list[RecommendationIssueV2] = Field(default_factory=list)
    error: RecommendationIssueV2 | None = None
    processing: RecommendationProcessingV2

    @model_validator(mode="after")
    def validate_response(self):
        if (self.temp_event_id is None) == (self.event_id is None):
            raise ValueError("Exactly one of tempEventId and eventId is required.")
        if self.status != "ERROR" and self.context is None:
            raise ValueError("Successful analysis requires context.")
        if self.status in ("READY", "PARTIAL") and not self.candidates:
            raise ValueError("READY/PARTIAL requires candidates.")
        if self.status in ("EMPTY", "ERROR") and self.candidates:
            raise ValueError("EMPTY/ERROR cannot include candidates.")
        if (self.status == "ERROR") != (self.error is not None):
            raise ValueError("Only ERROR requires an error object.")
        if self.status == "PARTIAL" and not self.warnings:
            raise ValueError("PARTIAL requires warnings explaining degradation.")
        ids = [item.candidate_id for item in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("candidateId must be unique within a response.")
        if [item.rank for item in self.candidates] != list(range(1, len(ids) + 1)):
            raise ValueError("Candidates must be ordered by consecutive rank values.")
        if self.context is not None:
            activity_refs = {item.activity_ref for item in self.context.activities}
            entity_refs = {item.entity_ref for item in self.context.entities}
            for candidate in self.candidates:
                if not set(candidate.activity_refs).issubset(activity_refs):
                    raise ValueError("Candidate activityRefs must reference context activities.")
                if not set(candidate.entity_refs).issubset(entity_refs):
                    raise ValueError("Candidate entityRefs must reference context entities.")
        return self
