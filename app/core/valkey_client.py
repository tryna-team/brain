import logging
from ssl import CERT_REQUIRED

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


logger = logging.getLogger(__name__)

VALKEY_DB = 0
VALKEY_TIMEOUT_SECONDS = 5
VALKEY_SSL_CA_CERTS = "/etc/ssl/certs/ca-certificates.crt"


class ValkeyClient:

    def __init__(self) -> None:
        self._client: Redis | None = None

    def connect(self) -> None:
        if self._client is not None:
            return
        if not settings.valkey_host:
            logger.info("Valkey is not configured; Redis-backed features are disabled.")
            return

        client_kwargs: dict = {
            "host": settings.valkey_host,
            "port": settings.valkey_port,
            "db": VALKEY_DB,
            "decode_responses": True,
            "socket_connect_timeout": VALKEY_TIMEOUT_SECONDS,
            "socket_timeout": VALKEY_TIMEOUT_SECONDS,
        }
        if settings.valkey_password:
            client_kwargs["password"] = settings.valkey_password
        if settings.is_prod:
            client_kwargs.update(
                ssl=True,
                ssl_cert_reqs=CERT_REQUIRED,
                ssl_ca_certs=VALKEY_SSL_CA_CERTS,
            )

        client = Redis(**client_kwargs)
        try:
            client.ping()
        except RedisError:
            client.close()
            logger.warning(
                "Valkey connection failed; continuing without Redis-backed features.",
                exc_info=True,
            )
            return

        self._client = client
        logger.info("Valkey connection established.")

    def close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None
        logger.info("Valkey connection closed.")

    @property
    def client(self) -> Redis | None:
        return self._client


valkey_client = ValkeyClient()
