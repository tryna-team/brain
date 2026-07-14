from pydantic import BaseModel


class EventPreviewRequest(BaseModel):
    sourceText: str


class EventPreviewWarning(BaseModel):
    code: str
    message: str


class EventPreviewResponse(BaseModel):
    sourceText: str
    titleCandidate: str
    dateCandidate: str | None = None
    timeCandidate: str | None = None
    placeCandidate: str | None = None
    eventTypeCandidate: str | None = None
    isAllDayCandidate: bool
    needsConfirmation: bool
    warnings: list[EventPreviewWarning] = []

