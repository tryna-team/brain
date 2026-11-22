from uuid import uuid4

from pydantic import ValidationError

from app.schemas.recommendation.v2.candidate import RecommendationCandidateV2
from app.schemas.recommendation.v2.llm_output import LLMCandidateV2
from app.schemas.recommendation.v2.request import RecommendationRequestV2
from app.schemas.recommendation.v2.response import (
    RecommendationIssueV2, RecommendationProcessingV2, RecommendationResponseV2,
)
from app.services.recommendation.v2.recommendation_llm_service import (
    RecommendationLLMError, RecommendationLLMResult,
)


def _response_fields(request, duration_ms, llm_attempt_count):
    return dict(
        request_id=request.request_id, 
        temp_event_id=request.temp_event_id,
        event_id=request.event_id, 
        draft_revision=request.draft_revision,
        event=request.event.model_copy(deep=True),
        processing=RecommendationProcessingV2(
            duration_ms=duration_ms, llm_attempt_count=llm_attempt_count,
        ),
    )


def build_error_response(
    request: RecommendationRequestV2,
    error: RecommendationLLMError,
    *,
    duration_ms: int,
) -> RecommendationResponseV2:
    return RecommendationResponseV2(
        **_response_fields(request, duration_ms, error.llm_attempt_count),
        status="ERROR",
        error=RecommendationIssueV2(code=error.code, stage="LLM", message=str(error)),
    )


def build_recommendation_response(
    request: RecommendationRequestV2,
    result: RecommendationLLMResult,
    *,
    duration_ms: int,
) -> RecommendationResponseV2:
    output = result.output
    common = _response_fields(request, duration_ms, result.llm_attempt_count)
    if any(item.resolution == "EXISTING" for item in [*output.context.activities, *output.context.entities]):
        return RecommendationResponseV2(
            **common, status="ERROR",
            error=RecommendationIssueV2(
                code="UNVERIFIED_CONTEXT", stage="VALIDATION",
                message="Context contains existing knowledge that was not retrieved or verified.",
            ),
        )

    warnings = []

    def warn(code, message):
        warnings.append(RecommendationIssueV2(code=code, stage="VALIDATION", message=message))

    activities = {item.activity_ref for item in output.context.activities}
    entities = {item.entity_ref for item in output.context.entities}
    valid = []
    for index, raw in enumerate(output.candidates):
        if isinstance(raw, dict):
            raw = dict(raw)
            timing_keys = ("timing", "timingEvidence", "timing_evidence")
            if any(raw.get(key) is not None for key in timing_keys):
                warn("TIMING_OMITTED", f"Candidate at index {index}: unverified timing was omitted.")
            for key in timing_keys:
                raw.pop(key, None)
        try:
            candidate = LLMCandidateV2.model_validate(raw)
        except ValidationError:
            warn("INVALID_CANDIDATE", f"Candidate at index {index} failed schema validation.")
            continue
        if candidate.action.resolution == "EXISTING" or candidate.rule is not None:
            warn("UNVERIFIED_KNOWLEDGE", f"Candidate at index {index} references unverified knowledge.")
            continue
        if not set(candidate.activity_refs).issubset(activities) or not set(candidate.entity_refs).issubset(entities):
            warn("INVALID_REFERENCE", f"Candidate at index {index} contains unknown context references.")
            continue
        valid.append(candidate)

    valid.sort(key=lambda item: item.rank)
    candidates = []
    seen_refs = set()
    seen_actions = set()
    for candidate in valid:
        if candidate.candidate_ref in seen_refs:
            warn("DUPLICATE_REFERENCE", "A duplicate candidateRef was omitted.")
            continue
        seen_refs.add(candidate.candidate_ref)
        signature = (
            candidate.display_text, candidate.action.name, candidate.action.description,
            tuple(sorted(candidate.activity_refs)), tuple(sorted(candidate.entity_refs)),
        )
        if signature in seen_actions:
            warn("DUPLICATE_CANDIDATE", "An identical candidate was omitted.")
            continue
        seen_actions.add(signature)
        if len(candidates) == 10:
            warn("CANDIDATE_LIMIT", "Candidates beyond the limit of 10 were omitted.")
            break
        candidates.append(RecommendationCandidateV2(
            candidate_id=uuid4(), display_text=candidate.display_text,
            reason=candidate.reason, rank=len(candidates) + 1,
            activity_refs=candidate.activity_refs, entity_refs=candidate.entity_refs,
            action=candidate.action.model_copy(deep=True),
        ))

    return RecommendationResponseV2(
        **common, status=("PARTIAL" if warnings else "READY") if candidates else "EMPTY",
        context=output.context.model_copy(deep=True), candidates=candidates, warnings=warnings,
    )
