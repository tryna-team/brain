"""Evaluate D102 EventType vector-search thresholds.

The default mode validates the labeled CSV without calling Upstage or Neo4j.
Pass ``--run`` to collect uncensored vector-search scores and calculate metrics.
Collected scores are cached so repeated threshold analysis does not call the
embedding API again.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.graph.neo4j_client import neo4j_client
from app.services.recommendation.embedding_service import EmbeddingService


DEFAULT_CASES_PATH = PROJECT_ROOT / "evaluation" / "event_type_cases.csv"
DEFAULT_RESULTS_PATH = (
    PROJECT_ROOT / "evaluation" / "results" / "event_type_scores.csv"
)
REQUIRED_COLUMNS = {
    "case_id",
    "query",
    "expected_code",
    "difficulty",
    "note",
}
SCORE_COLUMNS = [
    "case_id",
    "query",
    "expected_code",
    "difficulty",
    "model",
    "top1_code",
    "top1_score",
    "top2_code",
    "top2_score",
]
DEFAULT_REQUESTS_PER_SECOND = 1.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="D102 EventType 임베딩 임계값을 평가합니다.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Upstage와 Neo4j를 호출해 점수를 수집합니다.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="전체 데이터에서 고르게 선택해 실행할 최대 사례 수입니다.",
    )
    parser.add_argument(
        "--requests-per-second",
        type=float,
        default=DEFAULT_REQUESTS_PER_SECOND,
        help="Upstage 호출의 초당 최대 횟수입니다. (기본값: 1)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="저장된 점수를 무시하고 선택된 사례를 다시 호출합니다.",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="정답 CSV 경로입니다.",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="점수 캐시 CSV 경로입니다.",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit는 1 이상이어야 합니다.")
    if args.requests_per_second <= 0:
        parser.error("--requests-per-second는 0보다 커야 합니다.")
    if args.refresh and not args.run:
        parser.error("--refresh는 --run과 함께 사용해야 합니다.")
    return args


def _load_cases(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"평가 데이터 파일이 없습니다: {path}")

    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            raise RuntimeError(
                "평가 데이터에 필수 열이 없습니다: "
                + ", ".join(sorted(missing_columns))
            )
        cases = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]

    if not cases:
        raise RuntimeError("평가 데이터가 비어 있습니다.")

    seen_ids: set[str] = set()
    for line_number, case in enumerate(cases, start=2):
        if not case["case_id"] or not case["query"]:
            raise RuntimeError(
                f"{line_number}행의 case_id 또는 query가 비어 있습니다."
            )
        if case["case_id"] in seen_ids:
            raise RuntimeError(f"중복 case_id입니다: {case['case_id']}")
        if case["difficulty"] not in {"easy", "medium", "hard", "negative"}:
            raise RuntimeError(
                f"지원하지 않는 difficulty입니다: {case['difficulty']}"
            )
        if case["difficulty"] == "negative" and case["expected_code"]:
            raise RuntimeError(
                f"negative 사례에 expected_code가 있습니다: {case['case_id']}"
            )
        seen_ids.add(case["case_id"])

    return cases


def _select_evenly(
    cases: list[dict[str, str]],
    limit: int | None,
    preferred_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    if limit is None or limit >= len(cases):
        return cases

    preferred_ids = preferred_ids or set()
    preferred = [case for case in cases if case["case_id"] in preferred_ids]
    if len(preferred) >= limit:
        return preferred[:limit]

    remaining = [case for case in cases if case["case_id"] not in preferred_ids]
    needed = limit - len(preferred)
    if needed == 1:
        additions = [remaining[len(remaining) // 2]]
    else:
        indexes = {
            round(index * (len(remaining) - 1) / (needed - 1))
            for index in range(needed)
        }
        additions = [
            case for index, case in enumerate(remaining) if index in indexes
        ]

    selected_ids = {
        case["case_id"] for case in [*preferred, *additions]
    }
    return [case for case in cases if case["case_id"] in selected_ids]


def _load_cached_scores(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as file:
        return {
            row["case_id"]: row
            for row in csv.DictReader(file)
            if row.get("case_id")
        }


def _write_scores(path: Path, rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SCORE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _database_kwargs() -> dict[str, str]:
    if not settings.neo4j_database:
        return {}
    return {"database_": settings.neo4j_database}


def _load_active_event_type_codes() -> list[str]:
    records, _, _ = neo4j_client.driver.execute_query(
        """
        MATCH (node:EventType)
        WHERE node.isActive = true
          AND node.embedding IS NOT NULL
        RETURN node.code AS code
        ORDER BY node.code
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
            'event_type_embedding_idx',
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


def _is_cache_valid(
    cached: dict[str, str] | None,
    case: dict[str, str],
    model: str,
) -> bool:
    return bool(
        cached
        and cached.get("query") == case["query"]
        and cached.get("expected_code", "") == case["expected_code"]
        and cached.get("model") == model
    )


def _score_row(
    case: dict[str, str],
    model: str,
    candidates: list[dict[str, object]],
) -> dict[str, str]:
    top1 = candidates[0] if candidates else {}
    top2 = candidates[1] if len(candidates) > 1 else {}
    return {
        "case_id": case["case_id"],
        "query": case["query"],
        "expected_code": case["expected_code"],
        "difficulty": case["difficulty"],
        "model": model,
        "top1_code": str(top1.get("code", "")),
        "top1_score": (
            f"{float(top1['score']):.8f}" if "score" in top1 else ""
        ),
        "top2_code": str(top2.get("code", "")),
        "top2_score": (
            f"{float(top2['score']):.8f}" if "score" in top2 else ""
        ),
    }


def _threshold_metrics(
    rows: list[dict[str, str]],
    threshold: float,
) -> tuple[float, float, float, int, int, int]:
    true_positive = 0
    false_positive = 0
    false_negative = 0

    for row in rows:
        score = float(row["top1_score"])
        predicted = row["top1_code"] if score >= threshold else ""
        expected = row["expected_code"]

        if predicted and predicted == expected:
            true_positive += 1
        else:
            if predicted:
                false_positive += 1
            if expected:
                false_negative += 1

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return (
        precision,
        recall,
        f1,
        true_positive,
        false_positive,
        false_negative,
    )


def _print_metrics(rows: list[dict[str, str]]) -> None:
    print("\nthreshold precision recall f1    TP  FP  FN")
    best: tuple[float, float, float] | None = None
    for step in range(40, 81):
        threshold = step / 100
        precision, recall, f1, tp, fp, fn = _threshold_metrics(rows, threshold)
        print(
            f"{threshold:>9.2f} {precision:>9.3f} {recall:>6.3f} "
            f"{f1:>5.3f} {tp:>4} {fp:>3} {fn:>3}"
        )
        candidate = (f1, precision, threshold)
        if best is None or candidate > best:
            best = candidate

    if best is not None:
        print(
            "\n참고용 최고 F1: "
            f"threshold={best[2]:.2f}, f1={best[0]:.3f}, "
            f"precision={best[1]:.3f}"
        )


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
    selected_cases = _select_evenly(
        cases,
        args.limit,
        preferred_ids=valid_cached_ids,
    )
    expected_codes = {case["expected_code"] for case in cases if case["expected_code"]}

    print(
        f"validated: cases={len(cases)}, selected={len(selected_cases)}, "
        f"expected_codes={len(expected_codes)}"
    )
    if not args.run:
        print("dry-run complete: 외부 API와 Neo4j를 호출하지 않았습니다.")
        print("실행하려면 --run을 추가하세요. 첫 실행 권장: --run --limit 10")
        return

    embedding_service = EmbeddingService()
    model = embedding_service.model
    minimum_interval = 1.0 / args.requests_per_second

    neo4j_client.connect()
    neo4j_client.verify_connectivity()
    try:
        active_codes = _load_active_event_type_codes()
        if not active_codes:
            raise RuntimeError("임베딩이 저장된 활성 EventType이 없습니다.")
        missing_codes = expected_codes - set(active_codes)
        if missing_codes:
            raise RuntimeError(
                "Neo4j에 없는 expected_code가 있습니다: "
                + ", ".join(sorted(missing_codes))
            )

        api_calls = 0
        selected_ids = {case["case_id"] for case in selected_cases}
        for case in selected_cases:
            cached = cached_scores.get(case["case_id"])
            if not args.refresh and _is_cache_valid(cached, case, model):
                print(f"cached: {case['case_id']}")
                continue

            query_embedding = embedding_service.embed_query(case["query"])
            candidates = _query_all_candidates(
                query_embedding=query_embedding,
                candidate_count=len(active_codes),
            )
            cached_scores[case["case_id"]] = _score_row(
                case=case,
                model=model,
                candidates=candidates,
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
            print(
                f"scored: {case['case_id']}, "
                f"top1={cached_scores[case['case_id']]['top1_code']}, "
                f"score={cached_scores[case['case_id']]['top1_score']}"
            )
            if minimum_interval > 0:
                time.sleep(minimum_interval)

        ordered_rows = [
            cached_scores[case["case_id"]]
            for case in cases
            if case["case_id"] in cached_scores
        ]
        _write_scores(args.results, ordered_rows)
        evaluated_rows = [
            row for row in ordered_rows if row["case_id"] in selected_ids
        ]
    finally:
        neo4j_client.close()

    if not evaluated_rows or any(
        not row.get("top1_score") or not math.isfinite(float(row["top1_score"]))
        for row in evaluated_rows
    ):
        raise RuntimeError("평가할 수 있는 top1 점수가 없습니다.")

    print(
        f"complete: evaluated={len(evaluated_rows)}, api_calls={api_calls}, "
        f"results={args.results}"
    )
    _print_metrics(evaluated_rows)


if __name__ == "__main__":
    main()
