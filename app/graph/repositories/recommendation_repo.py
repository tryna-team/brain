from __future__ import annotations

from typing import ClassVar

from neo4j import Driver
from neo4j.exceptions import ServiceUnavailable, SessionExpired

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.graph.models.recommendation_candidate import RecommendationCandidateRecord


class RecommendationRepo:
    EVENT_TYPE_SCORE = 50
    CONTEXT_SCORE = 20
    PLACE_TYPE_SCORE = 15

    BASE_ITEM_TYPE_BY_TIMING_TYPE: ClassVar[
        dict[str | None, str]
    ] = {
        None: "UNTIMED_PREP",
        "non_timed": "UNTIMED_PREP",
        "timed": "TIMED_ACTION",
    }

    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def find_candidates(
        self,
        event_type: str | None,
        contexts: list[str],
        place_type: str | None,
        limit: int = 12,
    ) -> list[RecommendationCandidateRecord]:
        if event_type is None and not contexts and place_type is None:
            return [] # 조회 정보가 모두 없으면 빈리스트 반환 -> 추후 fallback 후보 조회로 개선 예정

        try:
            records, _, _ = self._driver.execute_query(
                """
                CALL {
                    MATCH (eventType:EventType {code: $event_type})
                        -[:RECOMMENDS]->
                        (template:RecommendationTemplate)
                    WHERE $event_type IS NOT NULL
                    AND coalesce(eventType.isActive, true) = true
                    RETURN
                        template,
                        $event_type_score AS relationScore,
                        "EventType:" + eventType.code AS sourceRelation

                    UNION ALL

                    MATCH (context:Context)
                        -[:RECOMMENDS]->
                        (template:RecommendationTemplate)
                    WHERE context.code IN $contexts
                    AND coalesce(context.isActive, true) = true
                    RETURN
                        template,
                        $context_score AS relationScore,
                        "Context:" + context.code AS sourceRelation

                    UNION ALL

                    MATCH (placeType:PlaceType {code: $place_type})
                        -[:RECOMMENDS]->
                        (template:RecommendationTemplate)
                    WHERE $place_type IS NOT NULL
                    AND coalesce(placeType.isActive, true) = true
                    RETURN
                        template,
                        $place_type_score AS relationScore,
                        "PlaceType:" + placeType.code AS sourceRelation
                }
                WITH
                    template,
                    sourceRelation,
                    max(relationScore) AS sourceScore
                WITH
                    template,
                    sum(sourceScore) AS score,
                    collect(sourceRelation) AS sourceRelations
                WHERE coalesce(template.isActive, true) = true
                RETURN
                    template.code AS templateId,
                    template.name AS title,
                    template.timingType AS timingType,
                    score,
                    sourceRelations
                ORDER BY score DESC, templateId ASC
                LIMIT $limit
                """,
                event_type=event_type,
                contexts=contexts,
                place_type=place_type,
                event_type_score=self.EVENT_TYPE_SCORE,
                context_score=self.CONTEXT_SCORE,
                place_type_score=self.PLACE_TYPE_SCORE,
                limit=limit,
            )
        except (ServiceUnavailable, SessionExpired) as exc:
            raise BusinessException(ErrorCode.NEO4J_503) from exc

        return [
            self._to_candidate(record)
            for record in records
        ]

    def find_fallback_candidates(
        self,
        limit: int = 2,
    ) -> list[RecommendationCandidateRecord]:
        raise NotImplementedError
    
    def _to_candidate(
        self,
        record,
    ) -> RecommendationCandidateRecord:
        timing_type = record["timingType"]

        try:
            base_item_type = self.BASE_ITEM_TYPE_BY_TIMING_TYPE[timing_type]
        except KeyError as exc:
            raise ValueError(
                "지원하지 않는 RecommendationTemplate "
                f"timingType입니다: {timing_type}"
            ) from exc

        return RecommendationCandidateRecord(
            template_id=record["templateId"],
            title=record["title"],
            base_item_type=base_item_type,
            offset_days=None,
            score=record["score"],
            source_relations=list(record["sourceRelations"]),
        )

