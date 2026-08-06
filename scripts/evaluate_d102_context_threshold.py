"""Evaluate D102 Context thresholds using resolved multi-label contexts.

The default mode only validates the labeled CSV. ``--run`` calls Upstage and
Neo4j, caches all raw candidate scores, and evaluates thresholds offline.
"""

from __future__ import annotations

import argparse
import csv
import json
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


DEFAULT_CASES_PATH = PROJECT_ROOT / "evaluation" / "context_cases.csv"
DEFAULT_RESULTS_PATH = PROJECT_ROOT / "evaluation" / "results" / "context_scores.csv"
REQUIRED_COLUMNS = {
    "case_id", "query", "expected_resolved_codes", "difficulty", "note"
}
SCORE_COLUMNS = [
    "case_id", "query", "expected_resolved_codes", "difficulty", "model",
    "candidate_scores",
]
TRAVEL_SCOPES = {"domestic_travel", "international_travel"}
PARENTS = {
    "domestic_travel": {"travel"},
    "international_travel": {"travel"},
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="D102 Context 임계값을 평가합니다.")
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


def _split_codes(value: str) -> set[str]:
    return {code.strip() for code in value.split(";") if code.strip()}


def _load_cases(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError("필수 열이 없습니다: " + ", ".join(sorted(missing)))
        cases = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]
    if not cases:
        raise RuntimeError("평가 데이터가 비어 있습니다.")
    seen: set[str] = set()
    for case in cases:
        if not case["case_id"] or not case["query"]:
            raise RuntimeError("case_id 또는 query가 비어 있습니다.")
        if case["case_id"] in seen:
            raise RuntimeError(f"중복 case_id입니다: {case['case_id']}")
        if case["difficulty"] == "negative" and case["expected_resolved_codes"]:
            raise RuntimeError(f"negative 정답이 비어 있지 않습니다: {case['case_id']}")
        seen.add(case["case_id"])
    return cases


def _load_cache(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as file:
        return {row["case_id"]: row for row in csv.DictReader(file)}


def _valid_cache(row: dict[str, str] | None, case: dict[str, str]) -> bool:
    return bool(
        row
        and row.get("query") == case["query"]
        and row.get("expected_resolved_codes", "") == case["expected_resolved_codes"]
        and row.get("model") == settings.upstage_query_embedding_model
    )


def _select(cases: list[dict[str, str]], limit: int | None, cached: set[str]):
    if limit is None or limit >= len(cases):
        return cases
    preferred = [case for case in cases if case["case_id"] in cached][:limit]
    remaining = [case for case in cases if case["case_id"] not in cached]
    needed = limit - len(preferred)
    if needed <= 0:
        additions = []
    elif needed == 1:
        additions = [remaining[len(remaining) // 2]]
    else:
        indexes = {
            round(index * (len(remaining) - 1) / (needed - 1))
            for index in range(needed)
        }
        additions = [case for index, case in enumerate(remaining) if index in indexes]
    ids = {case["case_id"] for case in [*preferred, *additions]}
    return [case for case in cases if case["case_id"] in ids]


def _write_cache(path: Path, cases: list[dict[str, str]], cache: dict[str, dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SCORE_COLUMNS)
        writer.writeheader()
        writer.writerows(cache[c["case_id"]] for c in cases if c["case_id"] in cache)


def _db_kwargs() -> dict[str, str]:
    return {"database_": settings.neo4j_database} if settings.neo4j_database else {}


def _active_codes() -> list[str]:
    records, _, _ = neo4j_client.driver.execute_query(
        """
        MATCH (node:Context)
        WHERE node.isActive = true AND node.embedding IS NOT NULL
        RETURN node.code AS code ORDER BY node.code
        """,
        **_db_kwargs(),
    )
    return [str(record["code"]) for record in records]


def _query_scores(embedding: list[float], count: int) -> list[dict[str, object]]:
    records, _, _ = neo4j_client.driver.execute_query(
        """
        CALL db.index.vector.queryNodes('context_embedding_idx', $count, $embedding)
        YIELD node, score
        WHERE node.isActive = true
        RETURN node.code AS code, score ORDER BY score DESC
        """,
        count=count,
        embedding=embedding,
        **_db_kwargs(),
    )
    return [{"code": str(r["code"]), "score": float(r["score"])} for r in records]


def _resolved(scores: list[dict[str, object]], threshold: float) -> set[str]:
    passed = [item for item in scores if float(item["score"]) >= threshold]
    selected = {str(item["code"]) for item in passed if item["code"] not in TRAVEL_SCOPES}
    scopes = [item for item in passed if item["code"] in TRAVEL_SCOPES]
    if scopes:
        selected.add(str(max(scopes, key=lambda item: float(item["score"]))["code"]))
    resolved = set(selected)
    for code in selected:
        resolved.update(PARENTS.get(code, set()))
    return resolved


def _metrics(rows: list[dict[str, str]], threshold: float):
    tp = fp = fn = 0
    exact = 0
    for row in rows:
        expected = _split_codes(row["expected_resolved_codes"])
        predicted = _resolved(json.loads(row["candidate_scores"]), threshold)
        tp += len(expected & predicted)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
        exact += predicted == expected
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1, exact


def _print_metrics(rows: list[dict[str, str]]) -> None:
    print("\nthreshold precision recall f1    exact")
    best = None
    for step in range(40, 81):
        threshold = step / 100
        precision, recall, f1, exact = _metrics(rows, threshold)
        print(f"{threshold:>9.2f} {precision:>9.3f} {recall:>6.3f} {f1:>5.3f} {exact:>5}/{len(rows)}")
        candidate = (f1, precision, threshold)
        if best is None or candidate > best:
            best = candidate
    if best:
        print(f"\n참고용 최고 F1: threshold={best[2]:.2f}, f1={best[0]:.3f}")


def main() -> None:
    args = _parse_args()
    cases = _load_cases(args.cases)
    cache = _load_cache(args.results)
    valid_ids = {case["case_id"] for case in cases if _valid_cache(cache.get(case["case_id"]), case)}
    selected = _select(cases, args.limit, valid_ids)
    expected_codes = set().union(*(_split_codes(c["expected_resolved_codes"]) for c in cases))
    print(f"validated: cases={len(cases)}, selected={len(selected)}, expected_codes={len(expected_codes)}")
    if not args.run:
        print("dry-run complete: 외부 API와 Neo4j를 호출하지 않았습니다.")
        return

    service = EmbeddingService()
    neo4j_client.connect()
    neo4j_client.verify_connectivity()
    calls = 0
    try:
        active = _active_codes()
        missing = expected_codes - set(active)
        if missing:
            raise RuntimeError("Neo4j에 없는 expected code: " + ", ".join(sorted(missing)))
        for case in selected:
            if not args.refresh and _valid_cache(cache.get(case["case_id"]), case):
                print(f"cached: {case['case_id']}")
                continue
            scores = _query_scores(service.embed_query(case["query"]), len(active))
            cache[case["case_id"]] = {
                "case_id": case["case_id"], "query": case["query"],
                "expected_resolved_codes": case["expected_resolved_codes"],
                "difficulty": case["difficulty"], "model": service.model,
                "candidate_scores": json.dumps(scores, ensure_ascii=False, separators=(",", ":")),
            }
            _write_cache(args.results, cases, cache)
            calls += 1
            print(f"scored: {case['case_id']}, top1={scores[0]['code']}, score={scores[0]['score']:.8f}")
            time.sleep(1.0 / args.requests_per_second)
    finally:
        neo4j_client.close()

    selected_ids = {case["case_id"] for case in selected}
    rows = [cache[c["case_id"]] for c in cases if c["case_id"] in selected_ids]
    if not rows or any(not math.isfinite(float(json.loads(r["candidate_scores"])[0]["score"])) for r in rows):
        raise RuntimeError("평가 가능한 점수가 없습니다.")
    print(f"complete: evaluated={len(rows)}, api_calls={calls}, results={args.results}")
    _print_metrics(rows)


if __name__ == "__main__":
    main()
