from unittest.mock import Mock

import pytest

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.services.recommendation.recommendation_service import RecommendationService


def _recommendation_service(revision_guard_service: Mock) -> RecommendationService:
    return RecommendationService(
        schedule_context_service=Mock(),
        candidate_search_service=Mock(),
        refinement_service=Mock(),
        temporal_validation_service=Mock(),
        suggestion_compose_service=Mock(),
        revision_guard_service=revision_guard_service,
    )


def _request() -> Mock:
    return Mock(temp_event_id="event-123", draft_revision=2)


def test_stale_request_is_stopped_before_d101():
    guard = Mock()
    guard.ensure_current.side_effect = BusinessException(
        ErrorCode.STALE_DRAFT_REVISION_409
    )
    service = _recommendation_service(guard)

    with pytest.raises(BusinessException):
        service.run_pipeline(_request())

    service.schedule_context_service.structure_context.assert_not_called()


def test_request_that_becomes_stale_after_d101_does_not_run_d102():
    guard = Mock()
    guard.ensure_current.side_effect = [
        None,
        BusinessException(ErrorCode.STALE_DRAFT_REVISION_409),
    ]
    service = _recommendation_service(guard)
    service.schedule_context_service.structure_context.return_value = Mock(
        embedding_status="READY"
    )

    with pytest.raises(BusinessException):
        service.run_pipeline(_request())

    service.schedule_context_service.structure_context.assert_called_once()
    service.candidate_search_service.search.assert_not_called()
