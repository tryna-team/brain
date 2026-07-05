from pydantic import BaseModel


# TODO: D102~D105 추천 생성 요청 DTO (파싱 결과 + 맥락 정보)
class RecommendationRequest(BaseModel):
    source_text: str
    event_type: str | None = None
    title: str | None = None
    scheduled_at: str | None = None
    place: str | None = None


# TODO: 추천 항목 단건 DTO
class RecommendationItem(BaseModel):
    title: str
    category: str | None = None
    is_timed: bool = False
    suggested_offset_minutes: int | None = None


# TODO: LLM 정제 후 최종 추천 응답 DTO
class RecommendationResponse(BaseModel):
    items: list[RecommendationItem] = []
