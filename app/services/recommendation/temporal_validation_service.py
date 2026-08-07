from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.schemas.recommendation.refinement import RecommendationRefinementResult, RefinedRecommendationItem
from app.schemas.recommendation.schedule_context import ScheduleContext
from app.schemas.recommendation.temporal import TemporalRecommendationItem, TemporalValidationResult


ASIA_SEOUL = ZoneInfo("Asia/Seoul")

USABLE_DATE_SOURCES = {
    "EXPLICIT",
    "RELATIVE_EXPRESSION",
}

MAX_TIMED_ITEMS = 2

class TemporalValidationService:

    def _build_no_items_result(
        self,
        refinement_result: RecommendationRefinementResult,
    ) -> TemporalValidationResult:
        return TemporalValidationResult(
            tempEventId=refinement_result.temp_event_id,
            draftRevision=refinement_result.draft_revision,
            temporalStatus="NO_ITEMS",
            items=[],
            scheduleContext=refinement_result.schedule_context,
            errors=list(refinement_result.errors),
        )
    
    
    def _resolve_display_date(
        self,
        item: RefinedRecommendationItem,
        schedule_context: ScheduleContext,
    ) -> date | None:
        start_date_candidate = schedule_context.start_date_candidate

        if start_date_candidate.date_source not in USABLE_DATE_SOURCES:
            return None

        if item.offset_days is None:
            return None

        display_date = (
            start_date_candidate.value
            + timedelta(days=item.offset_days)
        )

        today = datetime.now(ASIA_SEOUL).date()

        if display_date < today:
            return None

        return display_date
    

    def _build_temporal_item(
        self,
        item: RefinedRecommendationItem,
        display_date: date | None,
    ) -> TemporalRecommendationItem:
        item_type = (
            "TIMED_ACTION"
            if display_date is not None
            else "UNTIMED_PREP"
        )

        return TemporalRecommendationItem(
            sourceCode=item.source_code,
            displayText=item.display_text,
            itemType=item_type,
            offsetDays=item.offset_days,
            displayDate=display_date,
            displayTime=None,
            actionType=item.action_type,
            targetType=item.target_type,
            suggestionLevel=item.suggestion_level,
            defaultTiming=item.default_timing,
            selectionRank=item.selection_rank,
        )

    
    def temporal_validate(
        self,
        refinement_result: RecommendationRefinementResult,
    ) -> TemporalValidationResult:
        if not refinement_result.refined_items:
            return self._build_no_items_result(refinement_result)

        sorted_items = sorted(
            refinement_result.refined_items,
            key=lambda item: item.selection_rank,
        )

        temporal_items: list[TemporalRecommendationItem] = []
        timed_item_count = 0

        for item in sorted_items:
            display_date = self._resolve_display_date(
                item=item,
                schedule_context=refinement_result.schedule_context,
            )

            if display_date is not None:
                if timed_item_count >= MAX_TIMED_ITEMS:
                    display_date = None
                else:
                    timed_item_count += 1

            temporal_items.append(
                self._build_temporal_item(
                    item=item,
                    display_date=display_date,
                )
            )

        return TemporalValidationResult(
            tempEventId=refinement_result.temp_event_id,
            draftRevision=refinement_result.draft_revision,
            temporalStatus="SUCCESS",
            items=temporal_items,
            scheduleContext=refinement_result.schedule_context,
            errors=list(refinement_result.errors),
        )
