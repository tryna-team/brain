from app.graph.repositories.recommendation_repo import RecommendationRepo
from app.schemas.recommendation.candidates import (
    CandidateSearchResult,
    RecommendationCandidate,
)
from app.schemas.recommendation.schedule_context import ScheduleContextResult


class CandidateSearchService:
    def __init__(
        self,
        recommendation_repo: RecommendationRepo,
    ) -> None:
        self.recommendation_repo = recommendation_repo

    def search(
        self,
        context: ScheduleContextResult,
    ) -> CandidateSearchResult:
        event_type = context.event_type_candidate

        if event_type == "unknown":
            event_type = None

        records = self.recommendation_repo.find_candidates(
            event_type=event_type,
            contexts=context.context_candidates,
            place_type=context.place_type_candidate,
        )

        candidates = [
            RecommendationCandidate(
                templateId=record.template_id,
                title=record.title,
                baseItemType=record.base_item_type,
                offsetDays=record.offset_days,
                score=record.score,
                sourceRelations=record.source_relations,
            )
            for record in records
        ]

        return CandidateSearchResult(
            eventId=context.event_id,
            candidates=candidates,
        )