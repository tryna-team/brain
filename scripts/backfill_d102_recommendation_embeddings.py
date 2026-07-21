"""Backfill passage embeddings for D102 travel RecommendationTemplate nodes.

Running without ``--apply`` only validates and prints the targets. Actual writes
require an explicit ``--apply`` flag because this script can target production.
"""

from __future__ import annotations

import argparse

from app.core.config import settings
from app.graph.neo4j_client import neo4j_client
from app.services.recommendation.embedding_service import EmbeddingService


TARGET_RECOMMENDATION_CODES = (
    "charge_phone",
    "check_baggage_rules",
    "check_departure_point",
    "check_departure_time",
    "check_entry_documents",
    "check_passport_validity",
    "check_power_adapter",
    "check_transport",
    "check_transport_ticket",
    "check_travel_dates",
    "check_travel_time",
    "check_weather",
    "pack_id",
    "pack_passport",
    "pack_phone_charger",
    "pack_power_bank",
    "pack_regular_medicine",
    "prepare_overseas_payment",
    "prepare_roaming",
    "save_reservations_offline",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "D102 여행 RecommendationTemplate 노드의 passage embedding을 "
            "저장합니다."
        ),
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
    records, _, _ = neo4j_client.driver.execute_query(
        """
        MATCH (node:RecommendationTemplate)
        WHERE node.code IN $codes
        RETURN
            node.code AS code,
            node.embeddingText AS embeddingText,
            node.embedding IS NOT NULL AS hasEmbedding,
            node.isActive AS isActive
        ORDER BY node.code
        """,
        codes=list(TARGET_RECOMMENDATION_CODES),
        **_database_kwargs(),
    )

    targets = [dict(record) for record in records]
    found_codes = {target["code"] for target in targets}
    missing_codes = set(TARGET_RECOMMENDATION_CODES) - found_codes

    if missing_codes:
        raise RuntimeError(
            "Neo4j에 대상 RecommendationTemplate이 없습니다: "
            + ", ".join(sorted(missing_codes))
        )

    for target in targets:
        code = target["code"]

        if target["isActive"] is not True:
            raise RuntimeError(
                f"비활성 RecommendationTemplate입니다: {code}"
            )
        if not target["embeddingText"]:
            raise RuntimeError(f"embeddingText가 없습니다: {code}")
        if target["hasEmbedding"]:
            raise RuntimeError(f"이미 embedding이 존재합니다: {code}")

    return targets


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
        print(
            f"generated: RecommendationTemplate/{code}, "
            f"dimension={len(embedding)}"
        )

    return items


def _write_embeddings(transaction, items: list[dict]) -> list[dict]:
    result = transaction.run(
        """
        UNWIND $items AS item
        MATCH (node:RecommendationTemplate {code: item.code})
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

        for target in targets:
            print(
                f"validated: RecommendationTemplate/{target['code']}, "
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
                f"saved: RecommendationTemplate/{record['code']}, "
                f"dimension={record['dimension']}"
            )
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
