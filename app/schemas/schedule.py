from pydantic import BaseModel


# TODO: Spring Server에서 전달받는 일정 맥락 분석 요청 DTO
class ScheduleContextRequest(BaseModel):
    source_text: str
    title: str | None = None
    event_type: str | None = None
    scheduled_at: str | None = None
    place: str | None = None


# TODO: Neo4j 맥락 분석 결과 응답 DTO
class ScheduleContextResponse(BaseModel):
    event_type: str | None = None
    context_nodes: list[str] = []
    graph_query_summary: str | None = None
