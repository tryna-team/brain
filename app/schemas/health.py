from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel


class HealthStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DISABLED = "DISABLED"


class ComponentHealth(BaseModel):
    status: HealthStatus
    detail: str | None = None

    @classmethod
    def up(cls) -> "ComponentHealth":
        return cls(status=HealthStatus.UP, detail=None)

    @classmethod
    def down(cls, detail: str) -> "ComponentHealth":
        return cls(status=HealthStatus.DOWN, detail=detail)

    @classmethod
    def disabled(cls) -> "ComponentHealth":
        return cls(status=HealthStatus.DISABLED, detail=None)


class HealthComponents(BaseModel):
    neo4j: ComponentHealth
    redis: ComponentHealth


class HealthResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime
    components: HealthComponents

    @classmethod
    def of(
        cls,
        neo4j: ComponentHealth,
        redis: ComponentHealth,
    ) -> "HealthResponse":
        return cls(
            status=neo4j.status,
            timestamp=datetime.now(timezone.utc),
            components=HealthComponents(neo4j=neo4j, redis=redis),
        )

    def is_up(self) -> bool:
        return self.status == HealthStatus.UP
