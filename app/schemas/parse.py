from pydantic import BaseModel


# TODO: C101/C102 자연어 일정 파싱 요청 DTO
class ParseScheduleRequest(BaseModel):
    source_text: str


# TODO: C102 일정 기본 정보 1차 파싱 응답 DTO
class ParseScheduleResponse(BaseModel):
    source_text: str
    title_candidate: str | None = None
    date_candidate: str | None = None
    time_candidate: str | None = None
    place_candidate: str | None = None
    event_type_candidate: str | None = None
