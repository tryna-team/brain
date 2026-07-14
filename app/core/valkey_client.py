from redis import Redis

from app.core.config import settings
from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException


def _create_client() -> Redis | None:
    if not settings.valkey_host:
        return None

    client_kwargs: dict = {
        "host": settings.valkey_host,
        "port": settings.valkey_port,
        "db": settings.valkey_db,
        "decode_responses": True,
        "socket_connect_timeout": 3,
        "socket_timeout": 3,
    }
    if settings.valkey_password:
        client_kwargs["password"] = settings.valkey_password

    return Redis(**client_kwargs)


valkey_client: Redis | None = _create_client()


def verify_connectivity() -> None:
    if valkey_client is None:
        raise BusinessException(ErrorCode.VALKEY_503)
    valkey_client.ping()
