from unittest.mock import Mock

import pytest

from scripts import backfill_d102_event_type_embeddings as event_type
from scripts import backfill_d102_place_type_embeddings as place_type
from scripts import backfill_d102_recommendation_embeddings as recommendation


@pytest.mark.parametrize(
    ("module", "label", "load_args"),
    [
        (event_type, "EventType", ()),
        (place_type, "PlaceType", ()),
        (recommendation, "RecommendationTemplate", (20,)),
    ],
)
def test_load_targets_reports_empty_text_and_keeps_valid_targets(
    monkeypatch,
    capsys,
    module,
    label,
    load_args,
):
    driver = Mock()
    driver.execute_query.side_effect = [
        ([{"code": "bad_node"}], None, None),
        (
            [
                {
                    "code": "valid_node",
                    "embeddingText": "정상 임베딩 문구",
                }
            ],
            None,
            None,
        ),
    ]
    monkeypatch.setattr(module.neo4j_client, "_driver", driver)

    targets = module._load_targets(*load_args)

    assert targets == [
        {
            "code": "valid_node",
            "embeddingText": "정상 임베딩 문구",
        }
    ]
    assert (
        f"skipped: {label}/bad_node, reason=empty embeddingText"
        in capsys.readouterr().out
    )

    skipped_query = driver.execute_query.call_args_list[0].args[0]
    target_query = driver.execute_query.call_args_list[1].args[0]

    assert "node.embeddingText IS NULL" in skipped_query
    assert "trim(node.embeddingText) = ''" in skipped_query
    assert "node.embeddingText IS NOT NULL" in target_query
    assert "trim(node.embeddingText) <> ''" in target_query
    assert "node.isActive AS isActive" not in target_query

    if module is recommendation:
        assert target_query.index("trim(node.embeddingText)") < (
            target_query.index("LIMIT $limit")
        )
        assert driver.execute_query.call_args_list[1].kwargs["limit"] == 20
