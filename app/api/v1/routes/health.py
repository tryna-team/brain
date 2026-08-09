from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.valkey_client import valkey_client
from app.graph.neo4j_client import neo4j_client
from app.schemas.health import ComponentHealth, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()

NEO4J_DOWN_MESSAGE = "Neo4j connectivity check failed"
REDIS_DOWN_MESSAGE = "Redis connectivity check failed"


@router.get("/health")
def health_check() -> JSONResponse:
    neo4j = _check_neo4j()
    redis = _check_redis()
    response = HealthResponse.of(neo4j=neo4j, redis=redis)
    status_code = HTTPStatus.OK if response.is_up() else HTTPStatus.SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code.value,
        content=response.model_dump(mode="json"),
    )


def _check_neo4j() -> ComponentHealth:
    try:
        neo4j_client.verify_connectivity()
        return ComponentHealth.up()
    except BusinessException as exc:
        logger.warning("[Health] Neo4j 헬스체크 실패: %s", exc.message)
        return ComponentHealth.down(exc.message)
    except Exception:
        logger.warning("[Health] Neo4j 헬스체크 실패", exc_info=True)
        return ComponentHealth.down(NEO4J_DOWN_MESSAGE)


def _check_redis() -> ComponentHealth:
    if not settings.valkey_host:
        return ComponentHealth.disabled()

    client = valkey_client.client
    if client is None:
        return ComponentHealth.down(REDIS_DOWN_MESSAGE)

    try:
        client.ping()
        return ComponentHealth.up()
    except RedisError:
        logger.warning("[Health] Redis 헬스체크 실패", exc_info=True)
        return ComponentHealth.down(REDIS_DOWN_MESSAGE)
