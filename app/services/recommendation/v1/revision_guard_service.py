import logging

from redis.exceptions import RedisError

from app.core.error_code import ErrorCode
from app.core.exceptions import BusinessException
from app.core.valkey_client import ValkeyClient


logger = logging.getLogger("uvicorn.error")

LATEST_REVISION_KEY_PREFIX = "recommendation:latest-revision"


class RevisionGuardService:

    def __init__(self, client: ValkeyClient) -> None:
        self._valkey_client = client

    @staticmethod
    def build_key(temp_event_id: str) -> str:
        return f"{LATEST_REVISION_KEY_PREFIX}:{temp_event_id}"

    def ensure_current(self, temp_event_id: str, draft_revision: int) -> None:
        client = self._valkey_client.client
        if client is None:
            return

        try:
            stored_revision = client.get(self.build_key(temp_event_id))
            if stored_revision is None:
                return
            latest_revision = int(stored_revision)
        except (RedisError, TypeError, ValueError):
            logger.warning(
                "Draft revision lookup failed; continuing recommendation pipeline: "
                "tempEventId=%s",
                temp_event_id,
                exc_info=True,
            )
            return

        if draft_revision < latest_revision:
            logger.info(
                "Stale recommendation request stopped: "
                "tempEventId=%s, requestRevision=%s, latestRevision=%s",
                temp_event_id,
                draft_revision,
                latest_revision,
            )
            raise BusinessException(ErrorCode.STALE_DRAFT_REVISION_409)
