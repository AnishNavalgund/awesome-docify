from typing import Set
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    # OpenAI settings
    OPENAI_API_KEY: str
    
    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "openai_docs"
    
    # API settings
    OPENAPI_URL: str = "/openapi.json"
    
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
