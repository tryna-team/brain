from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel


class HealthStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class ComponentHealth(BaseModel):
    status: HealthStatus
    detail: str | None = None

    @classmethod
    def up(cls) -> "ComponentHealth":
        return cls(status=HealthStatus.UP, detail=None)

    @classmethod
    def down(cls, detail: str) -> "ComponentHealth":
        return cls(status=HealthStatus.DOWN, detail=detail)


class HealthComponents(BaseModel):
    neo4j: ComponentHealth
    redis: ComponentHealth


class HealthResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime
    components: HealthComponents

    @classmethod
    def of(cls, neo4j: ComponentHealth, redis: ComponentHealth) -> "HealthResponse":
        overall = (
            HealthStatus.UP
            if neo4j.status == HealthStatus.UP and redis.status == HealthStatus.UP
            else HealthStatus.DOWN
        )
        return cls(
            status=overall,
            timestamp=datetime.now(timezone.utc),
            components=HealthComponents(neo4j=neo4j, redis=redis),
        )

    def is_up(self) -> bool:
        return self.status == HealthStatus.UP
