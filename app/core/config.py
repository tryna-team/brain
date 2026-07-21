from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tryna Brain"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    internal_api_key: str | None = None

    # TODO_INFRA: 임시적 허용 범위 (추후 제거 예정)
    # ALB -> Nginx가 "/ai" 접두사를 떼어내고 FastAPI로 넘기므로, Swagger/OpenAPI가
    # 외부에 노출된 실제 경로를 알 수 있도록 root_path로 되돌려준다. (prod에서만 "/ai")
    root_path: str = ""

    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    neo4j_database: str | None = None

    upstage_api_key: str | None = None
    upstage_api_key_multi: str | None = None
    upstage_query_embedding_model: str = "solar-embedding-1-large-query"
    upstage_passage_embedding_model: str = "solar-embedding-1-large-passage"

    d102_embedding_dimension: int = 4096
    d102_event_type_min_score: float = Field(ge=0.0, le=1.0)
    d102_context_min_score: float = Field(ge=0.0, le=1.0)
    d102_place_type_min_score: float = Field(ge=0.0, le=1.0)
    d102_recommendation_min_score: float = Field(ge=0.0, le=1.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",

    )


settings = Settings()
