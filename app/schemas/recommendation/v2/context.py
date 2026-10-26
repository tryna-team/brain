from pydantic import Field, model_validator
from typing import Literal
from app.schemas.recommendation.v2.base import ResponseModelV2

class ContextProposalV2(ResponseModelV2):
    category: Literal["EVENT_TYPE", "CONTEXT", "PLACE_TYPE"]
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)

class RecommendationContextV2(ResponseModelV2):
    mapping_status: Literal["MATCHED", "PROPOSED", "UNRESOLVED", "ERROR"] = Field(alias="mappingStatus")
    resolved_by: Literal["EMBEDDING", "LLM", "NONE"] = Field(alias="resolvedBy")
    event_type: str | None = Field(default=None, alias="eventType", min_length=1)
    contexts: list[str] = Field(default_factory=list)
    place_type: str | None = Field(default=None, alias="placeType", min_length=1)
    history_context_key: str | None = Field(default=None, alias="historyContextKey")
    proposal: ContextProposalV2 | None = None

    @model_validator(mode="after")
    def validate_context(self):
        if self.mapping_status == "MATCHED" and not (self.event_type or self.contexts):
            raise ValueError("MATCHED requires an eventType or contexts.")
        if self.mapping_status == "PROPOSED" and self.proposal is None:
            raise ValueError("PROPOSED requires a proposal.")
        if self.proposal is not None and self.mapping_status != "PROPOSED":
            raise ValueError("Only PROPOSED can include a proposal.")
        if self.history_context_key is not None:
            if self.mapping_status != "MATCHED" or not self.event_type:
                raise ValueError("History requires a matched eventType.")
            if self.history_context_key != f"EVENT_TYPE:{self.event_type}":
                raise ValueError("historyContextKey must identify eventType.")
        return self