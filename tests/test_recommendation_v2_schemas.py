from copy import deepcopy
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.event_preview import EventPreviewResponse
from app.schemas.recommendation.v2.candidate import CandidateActionV2, CandidateTimingV2
from app.schemas.recommendation.v2.context import ActivityResolutionV2, EntityResolutionV2
from app.schemas.recommendation.v2.request import RecommendationRequestV2
from app.schemas.recommendation.v2.response import RecommendationResponseV2


@pytest.fixture
def response():
    return {
        "requestId": "request-1", "tempEventId": "draft-1", "draftRevision": 2,
        "status": "READY",
        "event": {"title": "수정한 시험", "isAllDay": True, "timezone": "Asia/Seoul"},
        "context": {
            "activities": [{"activityRef": "a1", "resolution": "NEW", "name": "시험 응시",
                            "description": "시험에 응시하는 활동", "evidence": {"source": "LLM_INFERRED"}}],
            "entities": [{"entityRef": "e1", "resolution": "UNKNOWN", "name": "데베",
                          "kind": "SUBJECT", "role": "SUBJECT", "activityRefs": ["a1"],
                          "identityEvidence": {"source": "LLM_INFERRED"},
                          "roleEvidence": {"source": "LLM_INFERRED"}}],
        },
        "candidates": [{"candidateId": str(uuid4()), "displayText": "시험 범위 확인하기",
                        "reason": "시험 준비", "rank": 1, "activityRefs": ["a1"],
                        "entityRefs": ["e1"], "action": {"resolution": "NEW", "name": "시험 범위 확인"}}],
        "processing": {"durationMs": 100, "llmAttemptCount": 1},
    }


def test_request_reuses_preview_without_overwriting_latest_event(response):
    preview = EventPreviewResponse(
        tempEventId="draft-1", eventTitle="원래 제목", draftRevision=0,
        toEmbedding=["시험"], isAllDayCandidate=True, needsConfirmation=True,
    )
    request = RecommendationRequestV2(
        requestId="request-1", ownerId="user-1", tempEventId="draft-1",
        draftRevision=2, event=response["event"], parsingResult=preview,
    )
    assert request.parsing_result is preview
    assert request.event.title == "수정한 시험"
    assert request.parsing_result.draft_revision == 0
    dumped = request.model_dump(mode="json", by_alias=True)
    assert dumped["parsingResult"]["toEmbedding"] == ["시험"]
    assert RecommendationRequestV2.model_validate(dumped) == request
    for invalid in (None, []):
        dumped["parsingResult"] = invalid
        with pytest.raises(ValidationError):
            RecommendationRequestV2.model_validate(dumped)


@pytest.mark.parametrize("ids", [{}, {"tempEventId": "draft-1", "eventId": "event-1"}])
def test_request_and_response_require_one_event_id(response, ids):
    response.pop("tempEventId")
    response.update(ids)
    with pytest.raises(ValidationError):
        RecommendationResponseV2.model_validate(response)
    request = {
        **response, "ownerId": "u1", "parsingResult": {
            "tempEventId": "draft-1", "eventTitle": "시험", "draftRevision": 0,
            "toEmbedding": [], "isAllDayCandidate": True, "needsConfirmation": False,
        },
    }
    with pytest.raises(ValidationError):
        RecommendationRequestV2.model_validate(request)


def test_response_roundtrip_and_existing_action_without_rule(response):
    response["candidates"][0]["action"] = {"resolution": "EXISTING", "actionId": "action-1", "name": "확인"}
    model = RecommendationResponseV2.model_validate(response)
    assert model.candidates[0].rule is None
    assert model.candidates[0].timing is None
    assert RecommendationResponseV2.model_validate_json(model.model_dump_json(by_alias=True)) == model


@pytest.mark.parametrize("status", ["EMPTY", "ERROR", "PARTIAL"])
def test_supported_statuses(response, status):
    response["status"] = status
    issue = {"code": "TEST", "stage": "LLM", "message": "test"}
    if status == "PARTIAL":
        response["warnings"] = [issue]
    else:
        response["candidates"] = []
    if status == "ERROR":
        response["error"] = issue
        response["context"] = None
    if status == "EMPTY":
        response["warnings"] = [issue]
    assert RecommendationResponseV2.model_validate(response).status == status


@pytest.mark.parametrize("change", [
    {"status": "EMPTY"}, {"status": "ERROR"}, {"status": "PARTIAL"},
    {"context": None}, {"candidates": []},
    {"error": {"code": "X", "stage": "LLM", "message": "failed"}},
])
def test_invalid_status_combinations(response, change):
    response.update(change)
    with pytest.raises(ValidationError):
        RecommendationResponseV2.model_validate(response)


@pytest.mark.parametrize("failure", ["duplicate_id", "rank", "limit", "activity", "entity", "entity_activity", "duplicate_activity", "duplicate_entity"])
def test_candidate_limits_and_reference_integrity(response, failure):
    candidate = response["candidates"][0]
    if failure == "duplicate_id":
        second = deepcopy(candidate)
        second["rank"] = 2
        response["candidates"].append(second)
    elif failure == "rank":
        candidate["rank"] = 2
    elif failure == "limit":
        response["candidates"] = [dict(candidate, candidateId=str(uuid4())) for _ in range(11)]
    elif failure in ("activity", "entity"):
        candidate[f"{failure}Refs"] = ["missing"]
    elif failure == "entity_activity":
        response["context"]["entities"][0]["activityRefs"] = ["missing"]
    elif failure == "duplicate_activity":
        response["context"]["activities"] *= 2
    else:
        response["context"]["entities"] *= 2
    with pytest.raises(ValidationError):
        RecommendationResponseV2.model_validate(response)


@pytest.mark.parametrize("resolution, identifier", [("EXISTING", None), ("NEW", "id-1"), ("UNKNOWN", "id-1")])
def test_resolution_id_consistency(response, resolution, identifier):
    activity = dict(response["context"]["activities"][0], resolution=resolution, activityId=identifier)
    entity = dict(response["context"]["entities"][0], resolution=resolution, entityId=identifier)
    with pytest.raises(ValidationError):
        ActivityResolutionV2.model_validate(activity)
    with pytest.raises(ValidationError):
        EntityResolutionV2.model_validate(entity)
    with pytest.raises(ValidationError):
        CandidateActionV2(resolution=resolution, actionId=identifier, name="확인")


def test_new_activity_requires_definition(response):
    activity = response["context"]["activities"][0]
    activity.pop("description")
    with pytest.raises(ValidationError):
        ActivityResolutionV2.model_validate(activity)


def test_unknown_activity_and_empty_context_allowed(response):
    activity = ActivityResolutionV2(activityRef="a1", resolution="UNKNOWN", evidence={"source": "UNKNOWN"})
    assert activity.name is None
    response.update(status="EMPTY", candidates=[], context={})
    assert RecommendationResponseV2.model_validate(response).context.activities == []


def test_rule_requires_existing_action(response):
    response["candidates"][0]["rule"] = {"ruleId": "rule-1", "version": 1}
    with pytest.raises(ValidationError):
        RecommendationResponseV2.model_validate(response)
    response["candidates"][0]["action"].update(resolution="EXISTING", actionId="action-1")
    assert RecommendationResponseV2.model_validate(response).candidates[0].rule.version == 1


def test_date_only_timing_and_invalid_timezone(response):
    timing = CandidateTimingV2(date="2026-11-10", timezone="Asia/Seoul")
    assert timing.time is None
    with pytest.raises(ValidationError):
        CandidateTimingV2(date="2026-11-10", timezone="Invalid/Zone")
    response["event"]["timezone"] = "Invalid/Zone"
    with pytest.raises(ValidationError):
        RecommendationResponseV2.model_validate(response)

