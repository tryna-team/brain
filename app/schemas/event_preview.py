from pydantic import BaseModel


class EventPreviewRequest(BaseModel):
    sourceText: str


class EventPreviewWarning(BaseModel):
    code: str
    message: str


class EventPreviewResponse(BaseModel):
    sourceText: str
    startDate: str | None = None
    endDate: str | None = None
    startTime: str | None = None
    endTime: str | None = None
    placeCandidate: str | None = None
    toEmbedding: list[str]
    isAllDayCandidate: bool
    needsConfirmation: bool
    warnings: list[EventPreviewWarning] = []
