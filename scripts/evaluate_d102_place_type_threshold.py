"""Evaluate the D102 PlaceType vector-search threshold."""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.graph.neo4j_client import neo4j_client
from app.services.recommendation.embedding_service import EmbeddingService
from scripts.evaluate_d102_event_type_threshold import (
    _is_cache_valid,
    _load_cached_scores,
    _load_cases,
    _print_metrics,
    _score_row,
    _select_evenly,
    _write_scores,
)


DEFAULT_CASES_PATH = PROJECT_ROOT / "evaluation" / "place_type_cases.csv"
DEFAULT_RESULTS_PATH = (
    PROJECT_ROOT / "evaluation" / "results" / "place_type_scores.csv"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="D102 PlaceType 임베딩 임계값을 평가합니다.",
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--requests-per-second", type=float, default=1.0)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit는 1 이상이어야 합니다.")
    if args.requests_per_second <= 0:
        parser.error("--requests-per-second는 0보다 커야 합니다.")
    if args.refresh and not args.run:
        parser.error("--refresh는 --run과 함께 사용해야 합니다.")
    return args


def _database_kwargs() -> dict[str, str]:
    return {"database_": settings.neo4j_database} if settings.neo4j_database else {}


def _active_codes() -> list[str]:
    records, _, _ = neo4j_client.driver.execute_query(
        """
        MATCH (node:PlaceType)
        WHERE node.isActive = true AND node.embedding IS NOT NULL
        RETURN node.code AS code ORDER BY node.code
        """,
        **_database_kwargs(),
    )
    return [str(record["code"]) for record in records]


def _query_all_candidates(
    query_embedding: list[float],
    candidate_count: int,
) -> list[dict[str, object]]:
    records, _, _ = neo4j_client.driver.execute_query(
        """
        CALL db.index.vector.queryNodes(
            'place_type_embedding_idx',
            $candidate_count,
            $query_embedding
        )
        YIELD node, score
        WHERE node.isActive = true
        RETURN node.code AS code, score
        ORDER BY score DESC
        """,
        candidate_count=candidate_count,
        query_embedding=query_embedding,
        **_database_kwargs(),
    )
    return [dict(record) for record in records]


def main() -> None:
    args = _parse_args()
    cases = _load_cases(args.cases)
    cached_scores = _load_cached_scores(args.results)
    valid_cached_ids = {
        case["case_id"]
        for case in cases
        if _is_cache_valid(
            cached_scores.get(case["case_id"]),
            case,
            settings.upstage_query_embedding_model,
        )
    }
    selected_cases = _select_evenly(cases, args.limit, valid_cached_ids)
    expected_codes = {
        case["expected_code"] for case in cases if case["expected_code"]
    }
    print(
        f"validated: cases={len(cases)}, selected={len(selected_cases)}, "
        f"expected_codes={len(expected_codes)}"
    )
    if not args.run:
        print("dry-run complete: 외부 API와 Neo4j를 호출하지 않았습니다.")
        return

    service = EmbeddingService()
    minimum_interval = 1.0 / args.requests_per_second
    neo4j_client.connect()
    neo4j_client.verify_connectivity()
    api_calls = 0
    try:
        active_codes = _active_codes()
        missing = expected_codes - set(active_codes)
        if missing:
            raise RuntimeError(
                "Neo4j에 없는 expected_code: " + ", ".join(sorted(missing))
            )
        for case in selected_cases:
            cached = cached_scores.get(case["case_id"])
            if not args.refresh and _is_cache_valid(cached, case, service.model):
                print(f"cached: {case['case_id']}")
                continue
            candidates = _query_all_candidates(
                service.embed_query(case["query"]),
                len(active_codes),
            )
            cached_scores[case["case_id"]] = _score_row(
                case,
                service.model,
                candidates,
            )
            _write_scores(
                args.results,
                [
                    cached_scores[item["case_id"]]
                    for item in cases
                    if item["case_id"] in cached_scores
                ],
            )
            api_calls += 1
            row = cached_scores[case["case_id"]]
            print(
                f"scored: {case['case_id']}, top1={row['top1_code']}, "
                f"score={row['top1_score']}"
            )
            time.sleep(minimum_interval)
    finally:
        neo4j_client.close()

    selected_ids = {case["case_id"] for case in selected_cases}
    rows = [
        cached_scores[case["case_id"]]
        for case in cases
        if case["case_id"] in selected_ids
    ]
    if not rows or any(
        not row.get("top1_score")
        or not math.isfinite(float(row["top1_score"]))
        for row in rows
    ):
        raise RuntimeError("평가할 수 있는 top1 점수가 없습니다.")
    print(
        f"complete: evaluated={len(rows)}, api_calls={api_calls}, "
        f"results={args.results}"
    )
    _print_metrics(rows)


if __name__ == "__main__":
    main()
