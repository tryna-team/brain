from pydantic import BaseModel


class EventPreviewRequest(BaseModel):
    sourceText: str


class EventPreviewWarning(BaseModel):
    code: str
    message: str


class EventPreviewResponse(BaseModel):
    sourceText: str
    dateCandidate: str | None = None
    timeCandidate: str | None = None
    placeCandidate: str | None = None
    toEmbedding: list[str]
    isAllDayCandidate: bool
    needsConfirmation: bool
    warnings: list[EventPreviewWarning] = []

