from pydantic import Field, model_validator
from typing import Literal
from datetime import date, time
from uuid import UUID
from app.schemas.recommendation.temporal import ItemType
from app.schemas.recommendation.candidates import MatchedBy
from app.schemas.recommendation.v2.base import ResponseModelV2


class CandidateDraftV2(ResponseModelV2):
    """조회·생성 후 검증과 평가를 기다리는 내부 후보. API 반환 모델과 구분한다.

    Neo4j code는 sourceTemplateId, name은 displayText로 옮긴다.
    candidateId는 서버에서 부여하고 최종 후보까지 유지한다.
    actionKey는 별도 행동 매핑 결과이며 템플릿 코드를 그대로 사용하지 않는다.
    """

    candidate_id: UUID = Field(alias="candidateId")
    action_key: str | None = Field(default=None, alias="actionKey", min_length=1)
    source_template_id: str | None = Field(default=None, alias="sourceTemplateId", min_length=1)
    origin: Literal["KNOWLEDGE_GRAPH", "LLM"]
    llm_reviewed: bool = Field(default=False, alias="llmReviewed")
    display_text: str = Field(alias="displayText", min_length=1)
    description: str = ""
    conditional_text: str | None = Field(default=None, alias="conditionalText")

    # 기존 템플릿의 분류와 시간 계산 재료. 미확정 LLM 후보는 null을 허용한다.
    action_type: str | None = Field(default=None, alias="actionType")
    target_type: str | None = Field(default=None, alias="targetType")
    suggestion_level: str | None = Field(default=None, alias="suggestionLevel")
    default_timing: str | None = Field(default=None, alias="defaultTiming")
    offset_days: int | None = Field(default=None, alias="offsetDays")

    # 검색 우선순위·유사도는 최종 적합도 점수 및 순위와 별개다.
    default_rank: int | None = Field(default=None, alias="defaultRank")
    vector_score: float | None = Field(default=None, alias="vectorScore", allow_inf_nan=False)
    matched_by: list[MatchedBy] = Field(default_factory=list, alias="matchedBy")

    @model_validator(mode="after")
    def validate_origin(self):
        if self.origin == "KNOWLEDGE_GRAPH" and self.source_template_id is None:
            raise ValueError("KNOWLEDGE_GRAPH requires sourceTemplateId.")
        if self.origin == "LLM" and self.source_template_id is not None:
            raise ValueError("New LLM candidates cannot reference a source template.")
        return self


class RecommendationCandidateV2(ResponseModelV2):
    candidate_id: UUID = Field(alias="candidateId")
    action_key: str | None = Field(default=None, alias="actionKey", min_length=1)
    source_template_id: str | None = Field(default=None, alias="sourceTemplateId", min_length=1)
    origin: Literal["KNOWLEDGE_GRAPH", "LLM"]
    llm_reviewed: bool = Field(alias="llmReviewed")
    display_text: str = Field(alias="displayText", min_length=1)
    item_type: ItemType = Field(alias="itemType")
    offset_days: int | None = Field(default=None, alias="offsetDays")
    display_date: date | None = Field(default=None, alias="displayDate")
    display_time: time | None = Field(default=None, alias="displayTime")
    relevance: Literal["HIGH", "MEDIUM"]
    base_score: float = Field(alias="baseScore", ge=0, le=1)
    base_rank: int = Field(alias="baseRank", ge=1, le=10)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_candidate(self):
        if self.item_type == "TIMED_ACTION" and self.display_date is None:
            raise ValueError("TIMED_ACTION requires displayDate.")
        if self.item_type == "UNTIMED_PREP" and any(
            value is not None for value in (self.offset_days, self.display_date, self.display_time)
        ):
            raise ValueError("UNTIMED_PREP cannot include timing fields.")
        if self.origin == "KNOWLEDGE_GRAPH" and self.source_template_id is None:
            raise ValueError("KNOWLEDGE_GRAPH requires sourceTemplateId.")
        if self.origin == "LLM" and self.source_template_id is not None:
            raise ValueError("New LLM candidates cannot reference a source template.")
        expected_score = {"HIGH": 0.85, "MEDIUM": 0.65}[self.relevance]
        if self.base_score != expected_score:
            raise ValueError("baseScore must match the relevance policy.")
        return self



