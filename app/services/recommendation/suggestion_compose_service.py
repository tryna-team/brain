from app.schemas.recommendation.recommendation import (
    RecommendationResponse,
    SuggestionItem,
)
from app.schemas.recommendation.temporal import TemporalValidationResult


class SuggestionCompositionService:
    def compose(
        self,
        temporal_result: TemporalValidationResult,
    ) -> RecommendationResponse:
        if temporal_result.temporal_status == "error":
            return RecommendationResponse(
                tempEventId=temporal_result.temp_event_id,
                draftRevision=temporal_result.draft_revision,
                suggestionStatus="error",
                suggestions=[],
                errors=temporal_result.errors,
            )

        if (
            temporal_result.temporal_status == "no_items"
            or not temporal_result.items
        ):
            return RecommendationResponse(
                tempEventId=temporal_result.temp_event_id,
                draftRevision=temporal_result.draft_revision,
                suggestionStatus="empty",
                suggestions=[],
                errors=temporal_result.errors,
            )

        errors = list(temporal_result.errors)

        sorted_items = sorted(
            temporal_result.items,
            key=lambda item: item.selection_rank,
        )

        ranks = [item.selection_rank for item in sorted_items]
        if len(ranks) != len(set(ranks)):
            errors.append("Duplicate selectionRank detected.")

        suggestions = [
            SuggestionItem(
                sourceCode=item.source_code,
                displayText=item.display_text,
                itemType=item.item_type,
                offsetDays=item.offset_days,
                displayDate=item.display_date,
                actionType=item.action_type,
                targetType=item.target_type,
                defaultTiming=item.default_timing,
                selectionRank=item.selection_rank,
                parentTempEventId=temporal_result.temp_event_id,
            )
            for item in sorted_items
        ]

        return RecommendationResponse(
            tempEventId=temporal_result.temp_event_id,
            draftRevision=temporal_result.draft_revision,
            suggestionStatus="ready",
            suggestions=suggestions,
            errors=errors,
        )