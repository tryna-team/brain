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

        if temporal_result.temporal_status == "NO_ITEMS":
            if temporal_result.items:
                raise ValueError(
                    "D105 received items with NO_ITEMS status."
                )

            return RecommendationResponse(
                tempEventId=temporal_result.temp_event_id,
                draftRevision=temporal_result.draft_revision,
                suggestionStatus="EMPTY",
                suggestions=[],
                errors=temporal_result.errors,
            )

        if not temporal_result.items:
            raise ValueError(
                "D105 received SUCCESS status without items."
            )

        if len(temporal_result.items) > 3:
            raise ValueError(
                "D105 received more than 3 items."
            )

        errors = list(temporal_result.errors)

        sorted_items = sorted(
            temporal_result.items,
            key=lambda item: item.selection_rank,
        )

        ranks = [
            item.selection_rank
            for item in sorted_items
        ]

        expected_ranks = list(
            range(1, len(sorted_items) + 1)
        )

        if ranks != expected_ranks:
            raise ValueError(
                "D105 received invalid selectionRank values."
            )

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
            suggestionStatus="READY",
            suggestions=suggestions,
            errors=errors,
        )
