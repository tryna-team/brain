import ssl

from redis import Redis

from app.core.config import settings
from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException

VALKEY_CONNECT_TIMEOUT_SECONDS = 2 if settings.app_env == "prod" else 3


def _create_client() -> Redis | None:
    if not settings.valkey_host:
        return None

    client_kwargs: dict = {
        "host": settings.valkey_host,
        "port": settings.valkey_port,
        "db": settings.valkey_db,
        "decode_responses": True,
        "socket_connect_timeout": VALKEY_CONNECT_TIMEOUT_SECONDS,
        "socket_timeout": VALKEY_CONNECT_TIMEOUT_SECONDS,
    }
    if settings.valkey_password:
        client_kwargs["password"] = settings.valkey_password

    # backend application-prod.yaml: spring.data.redis.ssl.enabled=true 와 동일하게 prod에서만 TLS 사용
    if settings.app_env == "prod":
        client_kwargs["ssl"] = True
        client_kwargs["ssl_cert_reqs"] = ssl.CERT_REQUIRED

    return Redis(**client_kwargs)


valkey_client: Redis | None = _create_client()


def verify_connectivity() -> None:
    if valkey_client is None:
        raise BusinessException(ErrorCode.VALKEY_503)
    valkey_client.ping()
