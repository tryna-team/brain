from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tryna Brain"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"

    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    neo4j_database: str | None = None

    upstage_api_key: str | None = None
    internal_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
