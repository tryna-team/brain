from __future__ import annotations

from dataclasses import replace

from neo4j import Driver, Record
from neo4j.exceptions import DriverError, Neo4jError
from app.graph.exceptions import RecommendationRepositoryError
from app.graph.models.recommendation_candidate import (
    MatchedByRecord,
    RecommendationCandidateRecord,
    SemanticCandidateRecord,
)


class RecommendationRepo:

    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def _to_semantic_candidate(
        self,
        record,
    ) -> SemanticCandidateRecord:
        code = record.get("code")
        score = record.get("score")

        if not isinstance(code, str) or not code:
            raise RecommendationRepositoryError(
                "Neo4j semantic candidate has an invalid code."
            )

        if not isinstance(score, (int, float)):
            raise RecommendationRepositoryError(
                "Neo4j semantic candidate has an invalid score."
            )

        return SemanticCandidateRecord(
            code=code,
            score=float(score),
        )

    # 이벤트 타입, 맥락, 장소 후보 조회 공통 메서드
    def _find_semantic_candidates(
        self,
        index_name: str,                # 조회할 Neo4j 벡터 인덱스 이름
        query_embedding: list[float],   # D101에서 생성한 사용자 일정 벡터
        min_score: float,               # 후보로 인정할 최소 벡터 유사도
        internal_top_k: int,            # 인덱스에서 필터링 전 우선 조회할 후보 수
        result_limit: int,              # 활성 상태와 임계값 필터링 후 최종 반환할 최대 후보 수
    ) -> list[SemanticCandidateRecord]:
        try:
            records, _, _ = self._driver.execute_query(
                """
                CALL db.index.vector.queryNodes(
                    $index_name,
                    $internal_top_k,
                    $query_embedding
                )
                YIELD node, score
                WHERE node.isActive = true
                AND score >= $min_score
                RETURN node.code AS code, score
                ORDER BY score DESC
                LIMIT $result_limit
                """,
                index_name=index_name,
                internal_top_k=internal_top_k,
                query_embedding=query_embedding,
                min_score=min_score,
                result_limit=result_limit,
            )
        except (DriverError, Neo4jError) as exc:
            raise RecommendationRepositoryError(
                "Neo4j semantic candidate lookup failed."
            ) from exc

        return [
            self._to_semantic_candidate(record)
            for record in records
        ]
    
    # 이벤트 타입 후보 조회
    def find_event_type_candidates(
        self,
        query_embedding: list[float],
        min_score: float,
    ) -> list[SemanticCandidateRecord]:
        return self._find_semantic_candidates(
            index_name="event_type_embedding_idx",
            query_embedding=query_embedding,
            min_score=min_score,
            internal_top_k=5,
            result_limit=2,
        )

    # 맥락 후보 조회
    def find_context_candidates(
        self,
        query_embedding: list[float],
        min_score: float,
    ) -> list[SemanticCandidateRecord]:
        return self._find_semantic_candidates(
            index_name="context_embedding_idx",
            query_embedding=query_embedding,
            min_score=min_score,
            internal_top_k=5,
            result_limit=5,
        )

    # 장소 후보 조회
    def find_place_type_candidates(
        self,
        query_embedding: list[float],
        min_score: float,
    ) -> list[SemanticCandidateRecord]:
        return self._find_semantic_candidates(
            index_name="place_type_embedding_idx",
            query_embedding=query_embedding,
            min_score=min_score,
            internal_top_k=10,
            result_limit=2,
        )
    
    # 조회한 맥락 후보의 상위 맥락 조회
    def resolve_contexts(
        self,
        detected_contexts: list[str],
    ) -> list[str]:
        if not detected_contexts:
            return []

        try:
            records, _, _ = self._driver.execute_query(
                """
                MATCH (context:Context)
                WHERE context.code IN $detected_contexts
                AND context.isActive = true

                MATCH (context)-[:IS_A*0..2]->(resolved:Context)
                WHERE resolved.isActive = true

                WITH DISTINCT resolved.code AS code
                ORDER BY code
                RETURN collect(code) AS codes
                """,
                detected_contexts=detected_contexts,
            )
        except (DriverError, Neo4jError) as exc:
            raise RecommendationRepositoryError(
                "Neo4j context resolution failed."
            ) from exc

        if not records:
            return []

        codes = records[0].get("codes")

        if not isinstance(codes, list):
            raise RecommendationRepositoryError(
                "Neo4j context resolution returned invalid codes."
            )

        if any(
            not isinstance(code, str) or not code
            for code in codes
        ):
            raise RecommendationRepositoryError(
                "Neo4j context resolution returned an invalid code."
            )

        return list(dict.fromkeys(codes))
    
    # 관계 기반으로 recommendationTemplate 조회
    def find_relation_candidate_records(
        self,
        selected_event_type: str | None,
        resolved_contexts: list[str],
        selected_place_type: str | None,
    ) -> list[Record]:
        try:
            records, _, _ = self._driver.execute_query(
                """
                MATCH (source)-[relationship:RECOMMENDS]->
                    (template:RecommendationTemplate)
                WHERE (
                    (
                        source:EventType
                        AND source.code = $selected_event_type
                    )
                    OR (
                        source:Context
                        AND source.code IN $resolved_contexts
                    )
                    OR (
                        source:PlaceType
                        AND source.code = $selected_place_type
                    )
                )
                AND source.isActive = true
                AND template.isActive = true
                AND coalesce(relationship.isActive, true) = true

                AND all(
                    requiredContext
                    IN coalesce(relationship.requiredContexts, [])
                    WHERE requiredContext IN $resolved_contexts
                )

                AND all(
                    requiredContext
                    IN coalesce(template.requiredContexts, [])
                    WHERE requiredContext IN $resolved_contexts
                )

                AND none(
                    excludedContext
                    IN coalesce(template.excludedContexts, [])
                    WHERE excludedContext IN $resolved_contexts
                )

                AND (
                    $selected_place_type IS NULL
                    OR NOT $selected_place_type
                        IN coalesce(template.excludedPlaceTypes, [])
                )

                RETURN
                    labels(source) AS sourceLabels,
                    source.code AS sourceCode,
                    relationship.suggestionMode AS suggestionMode,
                    relationship.reason AS reason,
                    relationship.defaultRank AS defaultRank,

                    template.code AS code,
                    template.name AS name,
                    template.conditionalText AS conditionalText,
                    template.description AS description,
                    template.actionType AS actionType,
                    template.targetType AS targetType,
                    template.suggestionLevel AS suggestionLevel,
                    template.defaultTiming AS defaultTiming
                """,
                selected_event_type=selected_event_type,
                resolved_contexts=resolved_contexts,
                selected_place_type=selected_place_type,
            )
        except (DriverError, Neo4jError) as exc:
            raise RecommendationRepositoryError(
                "Neo4j relation candidate lookup failed."
            ) from exc

        return records

    # 관계 기반 조회 결과 정제      
    def find_relation_candidates(
        self,
        selected_event_type: str | None,
        resolved_contexts: list[str],
        selected_place_type: str | None,
        limit: int = 12,
    ) -> list[RecommendationCandidateRecord]:
        records = self.find_relation_candidate_records(
            selected_event_type=selected_event_type,
            resolved_contexts=resolved_contexts,
            selected_place_type=selected_place_type,
        )

        candidates_by_code: dict[
            str,
            RecommendationCandidateRecord,
        ] = {}

        for record in records:
            code = record["code"]
            default_rank = record["defaultRank"]

            matched_by = MatchedByRecord(
                source_labels=list(record["sourceLabels"]),
                source_code=record["sourceCode"],
                suggestion_mode=(
                    record["suggestionMode"]
                    or record["suggestionLevel"]
                ),
                reason=record["reason"],
            )

            existing_candidate = candidates_by_code.get(code)

            if existing_candidate is None:
                candidates_by_code[code] = RecommendationCandidateRecord(
                    code=code,
                    name=record["name"],
                    conditional_text=record["conditionalText"],
                    description=record["description"],
                    action_type=record["actionType"],
                    target_type=record["targetType"],
                    suggestion_level=record["suggestionLevel"],
                    default_timing=record["defaultTiming"],
                    default_rank=default_rank,
                    vector_score=None,
                    matched_by=[matched_by],
                )
                continue

            ranks = [
                rank
                for rank in (
                    existing_candidate.default_rank,
                    default_rank,
                )
                if rank is not None
            ]

            candidates_by_code[code] = replace(
                existing_candidate,
                default_rank=min(ranks) if ranks else None,
                matched_by=[
                    *existing_candidate.matched_by,
                    matched_by,
                ],
            )

        candidates = sorted(
            candidates_by_code.values(),
            key=lambda candidate: (
                candidate.default_rank is None,
                candidate.default_rank or 0,
                candidate.code,
            ),
        )

        return candidates[:limit]
    
    # 벡터 기반으로 RecommendationTemplate 조회
    def find_recommendation_vector_candidate_records(
        self,
        query_embedding: list[float],
        min_score: float,
        selected_event_type: str | None,
        resolved_contexts: list[str],
        selected_place_type: str | None,
    ) -> list[Record]:
        try:
            records, _, _ = self._driver.execute_query(
                """
                CALL db.index.vector.queryNodes(
                    'recommendation_embedding_idx',
                    30,
                    $query_embedding
                )
                YIELD node AS template, score

                WHERE template.isActive = true
                AND score >= $min_score

                AND all(
                    requiredContext
                    IN coalesce(template.requiredContexts, [])
                    WHERE requiredContext IN $resolved_contexts
                )

                AND none(
                    excludedContext
                    IN coalesce(template.excludedContexts, [])
                    WHERE excludedContext IN $resolved_contexts
                )

                AND (
                    $selected_place_type IS NULL
                    OR NOT $selected_place_type
                        IN coalesce(template.excludedPlaceTypes, [])
                )

                MATCH (source)-[relationship:RECOMMENDS]->(template)
                WHERE (
                    (
                        source:EventType
                        AND source.code = $selected_event_type
                    )
                    OR (
                        source:Context
                        AND source.code IN $resolved_contexts
                    )
                    OR (
                        source:PlaceType
                        AND source.code = $selected_place_type
                        AND (
                            $selected_event_type IS NOT NULL
                            OR size($resolved_contexts) > 0
                        )
                    )
                )
                AND source.isActive = true
                AND coalesce(relationship.isActive, true) = true

                AND all(
                    requiredContext
                    IN coalesce(relationship.requiredContexts, [])
                    WHERE requiredContext IN $resolved_contexts
                )

                RETURN
                    labels(source) AS sourceLabels,
                    source.code AS sourceCode,
                    relationship.suggestionMode AS suggestionMode,
                    relationship.reason AS reason,

                    template.code AS code,
                    template.name AS name,
                    template.conditionalText AS conditionalText,
                    template.description AS description,
                    template.actionType AS actionType,
                    template.targetType AS targetType,
                    template.suggestionLevel AS suggestionLevel,
                    template.defaultTiming AS defaultTiming,

                    score AS vectorScore
                ORDER BY vectorScore DESC
                """,
                query_embedding=query_embedding,
                min_score=min_score,
                selected_event_type=selected_event_type,
                resolved_contexts=resolved_contexts,
                selected_place_type=selected_place_type,
            )
        except (DriverError, Neo4jError) as exc:
            raise RecommendationRepositoryError(
                "Neo4j recommendation vector lookup failed."
            ) from exc

        return records
    
    # 벡터 기반 조회 결과 정제
    def find_recommendation_vector_candidates(
        self,
        query_embedding: list[float],
        min_score: float,
        selected_event_type: str | None,
        resolved_contexts: list[str],
        selected_place_type: str | None,
        limit: int = 8,
    ) -> list[RecommendationCandidateRecord]:
        records = self.find_recommendation_vector_candidate_records(
            query_embedding=query_embedding,
            min_score=min_score,
            selected_event_type=selected_event_type,
            resolved_contexts=resolved_contexts,
            selected_place_type=selected_place_type,
        )

        candidates_by_code: dict[
            str,
            RecommendationCandidateRecord,
        ] = {}

        for record in records:
            code = record["code"]
            vector_score = float(record["vectorScore"])

            matched_by = MatchedByRecord(
                source_labels=list(record["sourceLabels"]),
                source_code=record["sourceCode"],
                suggestion_mode=(
                    record["suggestionMode"]
                    or record["suggestionLevel"]
                ),
                reason=record["reason"],
            )

            existing_candidate = candidates_by_code.get(code)

            if existing_candidate is None:
                candidates_by_code[code] = RecommendationCandidateRecord(
                    code=code,
                    name=record["name"],
                    conditional_text=record["conditionalText"],
                    description=record["description"],
                    action_type=record["actionType"],
                    target_type=record["targetType"],
                    suggestion_level=record["suggestionLevel"],
                    default_timing=record["defaultTiming"],
                    default_rank=None,
                    vector_score=vector_score,
                    matched_by=[matched_by],
                )
                continue

            candidates_by_code[code] = replace(
                existing_candidate,
                vector_score=max(
                    existing_candidate.vector_score or 0.0,
                    vector_score,
                ),
                matched_by=[
                    *existing_candidate.matched_by,
                    matched_by,
                ],
            )

        candidates = sorted(
            candidates_by_code.values(),
            key=lambda candidate: (
                -(candidate.vector_score or 0.0),
                candidate.code,
            ),
        )

        return candidates[:limit]

