from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.handlers import register_exception_handlers
from app.graph.neo4j_client import neo4j_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    neo4j_client.connect()
    yield
    neo4j_client.close()


app = FastAPI(
    title=settings.app_name,
    description="Tryna context intelligence engine",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
