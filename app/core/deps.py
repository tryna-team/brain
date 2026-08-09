from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.graph.neo4j_client import Neo4jClient, neo4j_client
from app.graph.repositories.recommendation_repo import RecommendationRepo
from app.services.recommendation.embedding_service import EmbeddingService
from app.services.recommendation.schedule_context_service import ScheduleContextService
from app.services.recommendation.recommendation_service import RecommendationService
from app.services.recommendation.candidate_search_service import CandidateSearchService
from app.services.recommendation.refinement_llm_service import RefinementLLMService
from app.services.recommendation.refinement_service import RecommendationRefinementService
from app.services.recommendation.temporal_validation_service import TemporalValidationService
from app.services.recommendation.suggestion_compose_service import SuggestionCompositionService
from app.services.recommendation.revision_guard_service import RevisionGuardService
from app.core.valkey_client import valkey_client


def get_neo4j_client() -> Neo4jClient:
    return neo4j_client


Neo4jClientDep = Annotated[Neo4jClient, Depends(get_neo4j_client)]


def get_recommendation_repo(client: Neo4jClientDep) -> RecommendationRepo:
    return RecommendationRepo(client.driver)


RecommendationRepoDep = Annotated[RecommendationRepo, Depends(get_recommendation_repo)]


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]


def get_schedule_context_service(
    embedding_service: EmbeddingServiceDep,
) -> ScheduleContextService:
    return ScheduleContextService(embedding_service=embedding_service)


ScheduleContextServiceDep = Annotated[ScheduleContextService, Depends(get_schedule_context_service)]


def get_candidate_search_service(
    recommendation_repo: RecommendationRepoDep,
) -> CandidateSearchService:
    return CandidateSearchService(
        recommendation_repo=recommendation_repo,
    )


CandidateSearchServiceDep = Annotated[CandidateSearchService, Depends(get_candidate_search_service)]


def get_refinement_llm_service() -> RefinementLLMService:
    return RefinementLLMService()


RefinementLLMServiceDep = Annotated[RefinementLLMService, Depends(get_refinement_llm_service)]


def get_recommendation_refinement_service(
    llm_service: RefinementLLMServiceDep,
) -> RecommendationRefinementService:
    return RecommendationRefinementService(
        llm_service=llm_service,
    )


RecommendationRefinementServiceDep = Annotated[RecommendationRefinementService, Depends(get_recommendation_refinement_service)]


def get_temporal_validation_service() -> TemporalValidationService:
    return TemporalValidationService()


TemporalValidationServiceDep = Annotated[TemporalValidationService, Depends(get_temporal_validation_service)]


def get_suggestion_compose_service() -> SuggestionCompositionService:
    return SuggestionCompositionService()

SuggestionCompositionServiceDep = Annotated[SuggestionCompositionService, Depends(get_suggestion_compose_service)]


def get_revision_guard_service() -> RevisionGuardService:
    return RevisionGuardService(client=valkey_client)


RevisionGuardServiceDep = Annotated[RevisionGuardService, Depends(get_revision_guard_service)]


def get_recommendation_service(
    schedule_context_service: ScheduleContextServiceDep,
    candidate_search_service: CandidateSearchServiceDep,
    refinement_service: RecommendationRefinementServiceDep,
    temporal_validation_service: TemporalValidationServiceDep,
    suggestion_compose_service: SuggestionCompositionServiceDep,
    revision_guard_service: RevisionGuardServiceDep,
) -> RecommendationService:
    return RecommendationService(
        schedule_context_service=schedule_context_service,
        candidate_search_service=candidate_search_service,
        refinement_service=refinement_service,
        temporal_validation_service=temporal_validation_service,
        suggestion_compose_service=suggestion_compose_service,
        revision_guard_service=revision_guard_service,
    )


RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]
