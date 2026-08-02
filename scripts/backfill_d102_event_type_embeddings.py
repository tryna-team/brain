"""Backfill missing passage embeddings for active EventType nodes.

Running without ``--apply`` only validates and prints the targets. Actual writes
require an explicit ``--apply`` flag because this script can target production.
Embeddings are generated and persisted in batches so a later failure does not
require regenerating already-saved batches.
"""

from __future__ import annotations

import argparse
import time

from app.core.config import settings
from app.graph.neo4j_client import neo4j_client
from app.services.recommendation.embedding_service import EmbeddingService


DEFAULT_BATCH_SIZE = 10
DEFAULT_REQUESTS_PER_SECOND = 2.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="임베딩이 없는 활성 EventType 노드를 배치로 저장합니다.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="검증 후 Neo4j에 embedding 속성을 실제로 저장합니다.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"한 번에 생성하고 저장할 노드 수입니다. (기본값: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--requests-per-second",
        type=float,
        default=DEFAULT_REQUESTS_PER_SECOND,
        help=(
            "Upstage 임베딩 호출의 초당 최대 횟수입니다. "
            f"(기본값: {DEFAULT_REQUESTS_PER_SECOND:g})"
        ),
    )
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size는 1 이상이어야 합니다.")
    if args.requests_per_second <= 0:
        parser.error("--requests-per-second는 0보다 커야 합니다.")
    return args


def _database_kwargs() -> dict[str, str]:
    if not settings.neo4j_database:
        return {}
    return {"database_": settings.neo4j_database}


def _load_targets() -> list[dict]:
    records, _, _ = neo4j_client.driver.execute_query(
        """
        MATCH (node:EventType)
        WHERE node.isActive = true
          AND node.embedding IS NULL
        RETURN
            node.code AS code,
            node.embeddingText AS embeddingText,
            node.isActive AS isActive
        ORDER BY node.code
        """,
        **_database_kwargs(),
    )

    targets = [dict(record) for record in records]

    for target in targets:
        code = target["code"]

        if target["isActive"] is not True:
            raise RuntimeError(f"비활성 EventType입니다: {code}")
        if not target["embeddingText"]:
            raise RuntimeError(f"embeddingText가 없습니다: {code}")

    return targets


def _batches(items: list[dict], batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def _generate_embeddings(
    targets: list[dict],
    requests_per_second: float,
) -> list[dict]:
    embedding_service = EmbeddingService()
    items: list[dict] = []
    minimum_interval = 1.0 / requests_per_second

    for target in targets:
        code = target["code"]
        embedding_text = target["embeddingText"]
        embedding = embedding_service.embed_passage(embedding_text)
        time.sleep(minimum_interval)

        if len(embedding) != settings.d102_embedding_dimension:
            raise RuntimeError(
                f"벡터 차원 불일치: {code} "
                f"(expected={settings.d102_embedding_dimension}, "
                f"actual={len(embedding)})"
            )

        items.append(
            {
                "code": code,
                "embedding_text": embedding_text,
                "embedding": embedding,
            }
        )
        print(f"generated: EventType/{code}, dimension={len(embedding)}")

    return items


def _write_embeddings(transaction, items: list[dict]) -> list[dict]:
    result = transaction.run(
        """
        UNWIND $items AS item
        MATCH (node:EventType {code: item.code})
        WHERE node.isActive = true
          AND node.embedding IS NULL
          AND node.embeddingText = item.embedding_text
        SET node.embedding = item.embedding
        RETURN node.code AS code, size(node.embedding) AS dimension
        ORDER BY node.code
        """,
        items=items,
    )
    saved = [dict(record) for record in result]

    if len(saved) != len(items):
        raise RuntimeError(
            "저장 직전 노드 상태가 변경되어 작업을 취소했습니다. "
            f"expected={len(items)}, matched={len(saved)}"
        )

    return saved


def main() -> None:
    args = _parse_args()
    neo4j_client.connect()
    neo4j_client.verify_connectivity()

    try:
        targets = _load_targets()

        if not targets:
            print("complete: 임베딩이 필요한 활성 EventType이 없습니다.")
            return

        for target in targets:
            print(
                f"validated: EventType/{target['code']}, "
                f"embeddingText={target['embeddingText']}"
            )

        if not args.apply:
            print(
                f"dry-run complete: targets={len(targets)}, "
                f"batch_size={args.batch_size}, "
                f"requests_per_second={args.requests_per_second:g}, "
                "실제 저장하려면 --apply를 추가하세요."
            )
            return

        session_kwargs = (
            {"database": settings.neo4j_database}
            if settings.neo4j_database
            else {}
        )

        with neo4j_client.driver.session(**session_kwargs) as session:
            saved_count = 0
            total_batches = (
                len(targets) + args.batch_size - 1
            ) // args.batch_size

            for batch_number, target_batch in enumerate(
                _batches(targets, args.batch_size),
                start=1,
            ):
                print(
                    f"batch {batch_number}/{total_batches}: "
                    f"generating {len(target_batch)} embeddings "
                    f"at max {args.requests_per_second:g} requests/second"
                )
                items = _generate_embeddings(
                    target_batch,
                    args.requests_per_second,
                )
                saved = session.execute_write(_write_embeddings, items)

                for record in saved:
                    print(
                        f"saved: EventType/{record['code']}, "
                        f"dimension={record['dimension']}"
                    )

                saved_count += len(saved)
                print(
                    f"batch {batch_number}/{total_batches} complete: "
                    f"saved={len(saved)}"
                )

        print(f"complete: saved={saved_count}")
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
