from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal
from app.schemas.recommendation.v2.context import RecommendationContextV2
from app.schemas.recommendation.v2.candidate import RecommendationCandidateV2
from app.schemas.recommendation.v2.base import ResponseModelV2

class RecommendationAttributeV2(ResponseModelV2):
    value: str | bool | int | float | None
    source: Literal["USER_CONFIRMED", "RULE", "LLM_INFERRED"]
    evidence: str | None = None

class RecommendationMetadataV2(ResponseModelV2):
    event_title: str = Field(alias="eventTitle", min_length=1)
    start_date: date = Field(alias="startDate")
    start_time: time | None = Field(default=None, alias="startTime")
    end_date: date | None = Field(default=None, alias="endDate")
    end_time: time | None = Field(default=None, alias="endTime")
    place: str | None = None
    attributes: dict[str, RecommendationAttributeV2] = Field(default_factory=dict)

class RecommendationIssueV2(ResponseModelV2):
    code: str = Field(min_length=1)
    stage: Literal["EMBEDDING", "CONTEXT", "CONTEXT_STORAGE", "LOOKUP", "REFINEMENT", "VALIDATION", "PIPELINE"]
    message: str = Field(min_length=1)

class RecommendationProcessingV2(ResponseModelV2):
    duration_ms: int = Field(alias="durationMs", ge=0)
    llm_attempt_count: int = Field(alias="llmAttemptCount", ge=0)

# /api/v2/recommendations responseDTO
class RecommendationResponseV2(ResponseModelV2):
    contract_version: Literal["2.0"] = Field(default="2.0", alias="contractVersion")
    policy_version: Literal["recommendation-v2.0"] = Field(default="recommendation-v2.0", alias="policyVersion")
    temp_event_id: str = Field(alias="tempEventId", min_length=1)
    draft_revision: int = Field(alias="draftRevision", ge=0)
    status: Literal["READY", "EMPTY", "PARTIAL", "ERROR"]
    context: RecommendationContextV2
    metadata: RecommendationMetadataV2
    candidates: list[RecommendationCandidateV2] = Field(default_factory=list, max_length=10)
    warnings: list[RecommendationIssueV2] = Field(default_factory=list)
    error: RecommendationIssueV2 | None = None
    processing: RecommendationProcessingV2

    @model_validator(mode="after")
    def validate_response(self):
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
        if [item.base_rank for item in self.candidates] != list(range(1, len(ids) + 1)):
            raise ValueError("Candidates must be ordered by consecutive baseRank values.")
        return self
