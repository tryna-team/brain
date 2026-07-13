from neo4j import Driver, GraphDatabase

from app.config import settings
from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException


class Neo4jClient:
    def __init__(self) -> None:
        self._driver: Driver | None = None

    def connect(self) -> None:
        if self._driver is not None:
            return
        if not all([settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password]):
            return
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

    def close(self) -> None:
        if self._driver is None:
            return
        self._driver.close()
        self._driver = None

    def verify_connectivity(self) -> None:
        if self._driver is None:
            raise BusinessException(ErrorCode.NEO4J_503)
        self._driver.verify_connectivity()

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            raise BusinessException(ErrorCode.NEO4J_503)
        return self._driver


neo4j_client = Neo4jClient()
