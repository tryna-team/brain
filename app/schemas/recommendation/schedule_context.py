from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EmbeddingStatus = Literal["ready", "error"]


class DateCandidate(BaseModel):
    value: date


class TimeCandidate(BaseModel):
    value: time


class ScheduleContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date_candidate: DateCandidate | None = Field(
        default=None,
        alias="dateCandidate",
    )
    time_candidate: TimeCandidate | None = Field(
        default=None,
        alias="timeCandidate",
    )
    place_candidate: str | None = Field(
        default=None,
        alias="placeCandidate",
    )


class EmbeddingMeta(BaseModel):
    model: str
    profile: Literal["query"] = "query"
    dimension: int


class ScheduleContextResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    temp_event_id: str = Field(alias= "tempEventId")
    draft_revision: int = Field(alias="draftRevision")
    query_embedding: list[float] | None = Field(
        default=None,
        alias="queryEmbedding",
    )
    embedding_status: EmbeddingStatus = Field(alias="embeddingStatus")
    semantic_input_version: str = Field(
        default="v1",
        alias="semanticInputVersion",
    )
    schedule_context: ScheduleContext = Field(alias="scheduleContext")
    embedding_meta: EmbeddingMeta | None = Field(
        default=None,
        alias="embeddingMeta",
    )