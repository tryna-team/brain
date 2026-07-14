from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.graph.neo4j_client import Neo4jClient, neo4j_client
from app.graph.repositories.recommendation_repo import RecommendationRepo
from app.services.recommendation.embedding_service import EmbeddingService
from app.services.recommendation.schedule_context_service import ScheduleContextService


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


ScheduleContextServiceDep = Annotated[
    ScheduleContextService,
    Depends(get_schedule_context_service),
]


# 참고용 입니다!!!! 이런 코드가 있으면 좋을 것 같다는 의견!! 입니다!
# TODO: ScheduleContextRepo 의존성 주입 (일정 맥락 조회 구현 후 활성화)
# def get_schedule_context_repo(client: Neo4jClientDep) -> ScheduleContextRepo:
#     from app.graph.repositories.schedule_context_repo import ScheduleContextRepo
#
#     return ScheduleContextRepo(client.driver)
#
# ScheduleContextRepoDep = Annotated[ScheduleContextRepo, Depends(get_schedule_context_repo)]


# TODO: ParserService 의존성 주입 (C101/C102 자연어 일정 1차 파싱 구현 후 활성화)
# def get_parser_service() -> ParserService:
#     from app.services.parser_service import ParserService
#
#     return ParserService()
#
# ParserServiceDep = Annotated[ParserService, Depends(get_parser_service)]


# TODO: ScheduleContextService 의존성 주입 (Neo4j 맥락 분석 구현 후 활성화)
# def get_schedule_context_service(
#     repo: ScheduleContextRepoDep,
# ) -> ScheduleContextService:
#     from app.services.schedule_context_service import ScheduleContextService
#
#     return ScheduleContextService(repo=repo)
#
# ScheduleContextServiceDep = Annotated[ScheduleContextService, Depends(get_schedule_context_service)]


# TODO: RecommendationService 의존성 주입 (parser → graph → llm → recommender 파이프라인 구현 후 활성화)
# def get_recommendation_service(
#     parser_service: ParserServiceDep,
#     recommendation_repo: RecommendationRepoDep,
# ) -> RecommendationService:
#     from app.services.recommendation_service import RecommendationService
#
#     return RecommendationService(
#         parser_service=parser_service,
#         recommendation_repo=recommendation_repo,
#     )
#
# RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


# TODO: LLMService 의존성 주입 (Upstage LLM 연동 구현 후 활성화)
# def get_llm_service() -> LLMService:
#     from app.services.llm_service import LLMService
#
#     return LLMService()
#
# LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
