from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tryna Brain"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"

    # TODO_INFRA: 임시적 허용 범위 (추후 제거 예정)
    # ALB -> Nginx가 "/ai" 접두사를 떼어내고 FastAPI로 넘기므로, Swagger/OpenAPI가
    # 외부에 노출된 실제 경로를 알 수 있도록 root_path로 되돌려준다. (prod에서만 "/ai")
    root_path: str = ""

    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    neo4j_database: str | None = None

    upstage_api_key: str | None = None
    upstage_embedding_model: str = "solar-embedding-1-large-query"

    internal_api_key: str | None = None

    valkey_host: str | None = None
    valkey_port: int = 6379
    valkey_db: int = 0
    valkey_key_prefix: str = "tryna:brain"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",

    )


settings = Settings()
