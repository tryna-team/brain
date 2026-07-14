from redis import Redis

from app.core.config import settings


valkey_client: Redis | None = None

if settings.valkey_host:
    valkey_client = Redis(
        host=settings.valkey_host,
        port=settings.valkey_port,
        db=settings.valkey_db,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )