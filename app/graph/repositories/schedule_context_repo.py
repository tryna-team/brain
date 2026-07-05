from __future__ import annotations

from neo4j import Driver


class ScheduleContextRepo:
    # TODO: 일정 맥락 기반 Neo4j 조회 로직 구현
    # - parser 결과(일정 유형, 장소, 시간 등)를 Cypher 파라미터로 변환
    # - EventType, Location, TimeContext 노드 간 관계 조회
    # - 추천 후보 조회 전 맥락 확장 쿼리 캡슐화

    def __init__(self, driver: Driver) -> None:
        self._driver = driver
