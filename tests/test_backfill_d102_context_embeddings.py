from unittest.mock import Mock

import pytest

from scripts import backfill_d102_context_embeddings as backfill


def test_load_targets_skips_inactive_and_embedded_contexts(monkeypatch):
    driver = Mock()
    driver.execute_query.side_effect = [
        (
            [
                {"code": code}
                for code in backfill.TARGET_CONTEXT_CODES
            ],
            None,
            None,
        ),
        (
            [
                {
                    "code": "academic",
                    "embeddingText": "학업 일정",
                    "isActive": True,
                }
            ],
            None,
            None,
        ),
    ]
    monkeypatch.setattr(backfill.neo4j_client, "_driver", driver)

    targets = backfill._load_targets()

    assert targets == [
        {
            "code": "academic",
            "embeddingText": "학업 일정",
            "isActive": True,
        }
    ]
    target_query = driver.execute_query.call_args_list[1].args[0]
    assert "node.isActive = true" in target_query
    assert "node.embedding IS NULL" in target_query


def test_load_targets_reports_only_nonexistent_codes(monkeypatch):
    driver = Mock()
    driver.execute_query.return_value = (
        [
            {"code": code}
            for code in backfill.TARGET_CONTEXT_CODES
            if code != "academic"
        ],
        None,
        None,
    )
    monkeypatch.setattr(backfill.neo4j_client, "_driver", driver)

    with pytest.raises(
        RuntimeError,
        match="Neo4j에 대상 Context가 없습니다: academic",
    ):
        backfill._load_targets()

    assert driver.execute_query.call_count == 1
