from fastapi import APIRouter

from app.schemas.event_preview import EventPreviewRequest, EventPreviewResponse
from app.services.event_preview_service import preview_event

router = APIRouter()


@router.post("/event-previews", response_model=EventPreviewResponse)
def create_event_preview(request: EventPreviewRequest) -> EventPreviewResponse:
    return preview_event(request)

