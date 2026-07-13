from __future__ import annotations

from neo4j import Driver


class RecommendationRepo:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def find_candidates_by_event_type(self, event_type: str) -> list[dict]:
        records, _, _ = self._driver.execute_query(
            """
            MATCH (e:EventType {name: $event_type})-[:RECOMMENDS]->(r:RecommendationTemplate)
            RETURN r.name AS name
            """,
            event_type=event_type,
        )
        return [record["name"] for record in records]
