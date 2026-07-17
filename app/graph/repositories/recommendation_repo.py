from __future__ import annotations

from neo4j import Driver
from neo4j.exceptions import ServiceUnavailable, SessionExpired

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.graph.models.recommendation_candidate import RecommendationCandidateRecord


class RecommendationRepo:
    EVENT_TYPE_SCORE = 50

    BASE_ITEM_TYPE_BY_TIMING_TYPE: dict[str | None, str] = {
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
        # conditions: list[str], -> 맥락 구조화 과정에서 제외되어서 없어도 될듯함
        place_type: str | None,
        limit: int = 12,
    ) -> list[RecommendationCandidateRecord]:
        if event_type is None:
            return []

        try:
            records, _, _ = self._driver.execute_query(
                """
                MATCH (eventType:EventType {code: $event_type})
                    -[relationship:RECOMMENDS]->
                    (template:RecommendationTemplate)
                WHERE coalesce(eventType.isActive, true) = true
                AND coalesce(template.isActive, true) = true
                RETURN
                template.code AS templateId,
                template.name AS title,
                template.timingType AS timingType,
                relationship.defaultRank AS defaultRank,
                relationship.reason AS reason
                ORDER BY relationship.defaultRank ASC
                LIMIT $limit
                """,
                event_type=event_type,
                limit=limit,
            )
        except (ServiceUnavailable, SessionExpired) as exc:
            raise BusinessException(ErrorCode.NEO4J_503) from exc

        return [
            self._to_event_type_candidate(
                record=record,
                event_type=event_type,
            )
            for record in records
        ]

    def find_fallback_candidates(
        self,
        limit: int = 2,
    ) -> list[RecommendationCandidateRecord]:
        raise NotImplementedError
    
    def _to_event_type_candidate(
        self,
        record,
        event_type: str,
    ) -> RecommendationCandidateRecord:
        timing_type = record["timingType"]

        try:
            base_item_type = self.BASE_ITEM_TYPE_BY_TIMING_TYPE[timing_type]
        except KeyError as exc:
            raise ValueError(
                f"지원하지 않는 RecommendationTemplate timingType입니다: {timing_type}"
            ) from exc

        return RecommendationCandidateRecord(
            template_id=record["templateId"],
            title=record["title"],
            base_item_type=base_item_type,
            offset_days=None,
            score=self.EVENT_TYPE_SCORE,
            source_relations=[f"EventType:{event_type}"],
        )

