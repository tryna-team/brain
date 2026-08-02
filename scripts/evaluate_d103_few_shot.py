"""Run a small, rate-limited D103 few-shot regression evaluation.

The default mode only prints and validates the cases. Pass ``--run`` to call
Upstage. This script does not write to Neo4j.
"""

from __future__ import annotations

import argparse
import json
import time

from pydantic import ValidationError

from app.schemas.recommendation.refinement import LLMRefinementResponse
from app.services.recommendation.prompts.refinement_prompt import (
    FEW_SHOT_MESSAGES,
    FEW_SHOT_VERSION,
    SYSTEM_PROMPT,
)
from app.services.recommendation.refinement_llm_service import (
    RefinementLLMError,
    RefinementLLMService,
)


DEFAULT_REQUESTS_PER_SECOND = 1.0

EVALUATION_CASES = (
    {
        "name": "exam_variant",
        "payload": {
            "eventTitle": "다음 주 화요일 전공 중간고사",
            "selectedEventType": "exam",
            "resolvedContexts": ["academic"],
            "selectedPlaceType": "school",
            "recommendationCandidates": [
                {
                    "code": "check_exam_schedule",
                    "name": "시험 시간과 시험실 확인하기",
                    "suggestionLevel": "safe",
                },
                {
                    "code": "check_exam_scope",
                    "name": "시험 범위 확인하기",
                    "suggestionLevel": "safe",
                },
                {
                    "code": "check_weather",
                    "name": "여행지 날씨 확인하기",
                    "conditionalText": (
                        "짐을 싸기 전에 여행지 날씨를 확인할까요?"
                    ),
                    "suggestionLevel": "safe",
                },
            ],
        },
        "required_codes": [
            "check_exam_schedule",
            "check_exam_scope",
        ],
        "allowed_codes": [
            "check_exam_schedule",
            "check_exam_scope",
        ],
    },
    {
        "name": "outdoor_variant",
        "payload": {
            "eventTitle": "일요일 하루 종일 서울숲 피크닉",
            "selectedEventType": "social_meetup",
            "resolvedContexts": ["hangout"],
            "selectedPlaceType": "park_outdoor",
            "recommendationCandidates": [
                {
                    "code": "check_outdoor_weather",
                    "name": "야외 약속 시간대 날씨 확인하기",
                    "conditionalText": (
                        "야외에서 만날 예정이라면 그 시간대 날씨를 "
                        "확인할까요?"
                    ),
                    "suggestionLevel": "contextual",
                },
                {
                    "code": "check_location",
                    "name": "정확한 장소 다시 확인하기",
                    "conditionalText": (
                        "정확한 건물과 방문 장소를 다시 확인할까요?"
                    ),
                    "suggestionLevel": "safe",
                },
                {
                    "code": "pack_water",
                    "name": "마실 물 챙기기",
                    "conditionalText": (
                        "오래 밖에 있을 예정이라면 마실 물을 챙길까요?"
                    ),
                    "suggestionLevel": "conditional",
                },
            ],
        },
        "required_codes": [
            "check_location",
            "check_outdoor_weather",
        ],
        "allowed_codes": [
            "check_location",
            "check_outdoor_weather",
            "pack_water",
        ],
    },
    {
        "name": "irrelevant_candidate_variant",
        "payload": {
            "eventTitle": "집에서 소설 읽기",
            "selectedEventType": None,
            "resolvedContexts": [],
            "selectedPlaceType": None,
            "recommendationCandidates": [
                {
                    "code": "pack_passport",
                    "name": "여권 챙기기",
                    "conditionalText": (
                        "해외 출국에 필요한 여권을 챙길까요?"
                    ),
                    "suggestionLevel": "safe",
                },
            ],
        },
        "required_codes": [],
        "allowed_codes": [],
    },
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="D103 few-shot 회귀 평가를 실행합니다.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Upstage를 실제 호출합니다. 생략하면 dry-run입니다.",
    )
    parser.add_argument(
        "--requests-per-second",
        type=float,
        default=DEFAULT_REQUESTS_PER_SECOND,
        help=(
            "Upstage 호출의 초당 최대 횟수입니다. "
            f"(기본값: {DEFAULT_REQUESTS_PER_SECOND:g})"
        ),
    )
    args = parser.parse_args()
    if args.requests_per_second <= 0:
        parser.error("--requests-per-second는 0보다 커야 합니다.")
    return args


def _build_messages(payload: dict) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT_MESSAGES,
        {
            "role": "user",
            "content": json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        },
    ]


def _validate_result(case: dict, content: str) -> tuple[bool, list[str]]:
    try:
        response = LLMRefinementResponse.model_validate_json(content)
    except ValidationError as exc:
        print(f"FAIL {case['name']}: invalid JSON response: {exc}")
        return False, []

    selected_codes = [
        item.source_code
        for item in response.refined_items
    ]
    candidate_codes = {
        candidate["code"]
        for candidate in case["payload"]["recommendationCandidates"]
    }
    required_codes = set(case["required_codes"])
    allowed_codes = set(case["allowed_codes"])
    selected_code_set = set(selected_codes)

    contract_valid = (
        len(selected_codes) <= 3
        and len(selected_codes) == len(set(selected_codes))
        and set(selected_codes) <= candidate_codes
    )
    passed = (
        contract_valid
        and required_codes <= selected_code_set
        and selected_code_set <= allowed_codes
    )

    status = "PASS" if passed else "FAIL"
    print(
        f"{status} {case['name']}: "
        f"required={case['required_codes']}, "
        f"allowed={case['allowed_codes']}, "
        f"actual={selected_codes}"
    )
    return passed, selected_codes


def main() -> None:
    args = _parse_args()
    print(
        f"few_shot_version={FEW_SHOT_VERSION}, "
        f"cases={len(EVALUATION_CASES)}, "
        f"requests_per_second={args.requests_per_second:g}"
    )

    for case in EVALUATION_CASES:
        _build_messages(case["payload"])
        print(
            f"validated: {case['name']}, "
            f"required={case['required_codes']}, "
            f"allowed={case['allowed_codes']}"
        )

    if not args.run:
        print("dry-run complete: 실제 평가하려면 --run을 추가하세요.")
        return

    service = RefinementLLMService()
    minimum_interval = 1.0 / args.requests_per_second
    failed_cases: list[str] = []

    for case in EVALUATION_CASES:
        try:
            content = service.complete(_build_messages(case["payload"]))
        except RefinementLLMError as exc:
            print(f"FAIL {case['name']}: {exc}")
            failed_cases.append(case["name"])
        else:
            passed, _ = _validate_result(case, content)
            if not passed:
                failed_cases.append(case["name"])

        time.sleep(minimum_interval)

    if failed_cases:
        raise SystemExit(
            "evaluation failed: " + ", ".join(failed_cases)
        )

    print(f"evaluation passed: cases={len(EVALUATION_CASES)}")


if __name__ == "__main__":
    main()
