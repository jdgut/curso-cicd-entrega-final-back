from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Movilidad EAFIT"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
    )

    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/movilidad"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")


settings = Settings()
