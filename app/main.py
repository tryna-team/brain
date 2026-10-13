from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.handlers import register_exception_handlers
from app.core.valkey_client import valkey_client
from app.graph.neo4j_client import neo4j_client


@asynccontextmanager
async def lifespan(app: FastAPI):

    # 로컬 OCR 개발 환경에서만 Neo4j 연결 생략
    skip_neo4j = (
        settings.is_local
        and settings.skip_neo4j_connection
    )

    if not skip_neo4j:
        neo4j_client.connect()

    valkey_client.connect()

    try:
        yield
    finally:
        valkey_client.close()

        if not skip_neo4j:
            neo4j_client.close()


app = FastAPI(
    title=settings.app_name,
    description="Tryna context intelligence engine",
    version="0.1.0",
    lifespan=lifespan,

    # TODO_INFRA: 임시적 허용 범위 (추후 제거 예정)
    root_path=settings.root_path,
)

register_exception_handlers(app)


@app.get("/", response_class=PlainTextResponse)
def ping() -> str:
    return "OK"


app.include_router(api_router, prefix=settings.api_v1_prefix)
