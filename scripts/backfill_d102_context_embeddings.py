"""Backfill missing passage embeddings for active Context nodes.

Running without ``--apply`` only validates and prints the targets. Actual writes
require an explicit ``--apply`` flag because this script can target production.
"""

from __future__ import annotations

import argparse

from app.core.config import settings
from app.graph.neo4j_client import neo4j_client
from app.services.recommendation.embedding_service import EmbeddingService


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Context 노드의 passage embedding을 저장합니다.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="검증 후 Neo4j에 embedding 속성을 실제로 저장합니다.",
    )
    return parser.parse_args()


def _database_kwargs() -> dict[str, str]:
    if not settings.neo4j_database:
        return {}
    return {"database_": settings.neo4j_database}


def _load_targets() -> list[dict]:
    skipped_records, _, _ = neo4j_client.driver.execute_query(
        """
        MATCH (node:Context)
        WHERE node.isActive = true
          AND node.embedding IS NULL
          AND (
              node.embeddingText IS NULL
              OR trim(node.embeddingText) = ''
          )
        RETURN node.code AS code
        ORDER BY node.code
        """,
        **_database_kwargs(),
    )

    for record in skipped_records:
        print(
            f"skipped: Context/{record['code']}, "
            "reason=empty embeddingText"
        )

    target_records, _, _ = neo4j_client.driver.execute_query(
        """
        MATCH (node:Context)
        WHERE node.isActive = true
          AND node.embedding IS NULL
          AND node.embeddingText IS NOT NULL
          AND trim(node.embeddingText) <> ''
        RETURN
            node.code AS code,
            node.embeddingText AS embeddingText,
            node.isActive AS isActive
        ORDER BY node.code
        """,
        **_database_kwargs(),
    )

    return [dict(record) for record in target_records]


def _generate_embeddings(targets: list[dict]) -> list[dict]:
    embedding_service = EmbeddingService()
    items: list[dict] = []

    for target in targets:
        code = target["code"]
        embedding_text = target["embeddingText"]
        embedding = embedding_service.embed_passage(embedding_text)

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
        print(f"generated: Context/{code}, dimension={len(embedding)}")

    return items


def _write_embeddings(transaction, items: list[dict]) -> list[dict]:
    result = transaction.run(
        """
        UNWIND $items AS item
        MATCH (node:Context {code: item.code})
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
            print("complete: 임베딩이 필요한 활성 Context가 없습니다.")
            return

        for target in targets:
            print(
                f"validated: Context/{target['code']}, "
                f"embeddingText={target['embeddingText']}"
            )

        if not args.apply:
            print("dry-run complete: 실제 저장하려면 --apply를 추가하세요.")
            return

        items = _generate_embeddings(targets)
        session_kwargs = (
            {"database": settings.neo4j_database}
            if settings.neo4j_database
            else {}
        )

        with neo4j_client.driver.session(**session_kwargs) as session:
            saved = session.execute_write(_write_embeddings, items)

        for record in saved:
            print(
                f"saved: Context/{record['code']}, "
                f"dimension={record['dimension']}"
            )
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
