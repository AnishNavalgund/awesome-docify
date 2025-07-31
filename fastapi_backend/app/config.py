from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAPI docs
    OPENAPI_URL: str = "/openapi.json"


    DATABASE_URL: str | None = None
    TEST_DATABASE_URL: str | None = None

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS - using string that will be parsed
    CORS_ORIGINS_STR: str = "http://localhost:3000,http://127.0.0.1:3000"

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "awesome-docify"

    @property
    def CORS_ORIGINS(self) -> Set[str]:
        return {origin.strip() for origin in self.CORS_ORIGINS_STR.split(",")}

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
