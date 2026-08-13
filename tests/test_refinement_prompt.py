import json

from app.services.recommendation.prompts.refinement_prompt import (
    FEW_SHOT_MESSAGES,
    FEW_SHOT_VERSION,
    PROMPT_VERSION,
)


EXPECTED_SELECTIONS = {
    "다음 주 중간고사": [
        "check_exam_schedule",
        "check_exam_scope",
    ],
    "토요일 하루 종일 한강 피크닉": [
        "check_location",
        "check_outdoor_weather",
        "pack_water",
    ],
    "집에서 책 읽기": [],
}


def _few_shot_pairs() -> list[tuple[dict, dict]]:
    assert len(FEW_SHOT_MESSAGES) % 2 == 0

    pairs: list[tuple[dict, dict]] = []
    for index in range(0, len(FEW_SHOT_MESSAGES), 2):
        user_message = FEW_SHOT_MESSAGES[index]
        assistant_message = FEW_SHOT_MESSAGES[index + 1]

        assert user_message["role"] == "user"
        assert assistant_message["role"] == "assistant"

        pairs.append(
            (
                json.loads(user_message["content"]),
                json.loads(assistant_message["content"]),
            )
        )

    return pairs


def test_prompt_versions_are_updated():
    assert PROMPT_VERSION == "d103_prompt_v2"
    assert FEW_SHOT_VERSION == "d103_fewshot_v3"


def test_few_shot_messages_follow_selection_contract():
    pairs = _few_shot_pairs()

    assert 3 <= len(pairs) <= 6

    for user_payload, assistant_payload in pairs:
        candidate_codes = {
            candidate["code"]
            for candidate in user_payload["recommendationCandidates"]
        }
        refined_items = assistant_payload["refinedItems"]
        selected_codes = [
            item["sourceCode"]
            for item in refined_items
        ]

        assert len(refined_items) <= 3
        assert len(selected_codes) == len(set(selected_codes))
        assert set(selected_codes) <= candidate_codes
        assert all(
            item["displayText"].strip()
            for item in refined_items
        )


def test_new_few_shot_examples_keep_expected_selections():
    selections_by_title = {
        user_payload["eventTitle"]: [
            item["sourceCode"]
            for item in assistant_payload["refinedItems"]
        ]
        for user_payload, assistant_payload in _few_shot_pairs()
    }

    for event_title, expected_codes in EXPECTED_SELECTIONS.items():
        assert selections_by_title[event_title] == expected_codes
