from typing import Optional, Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: Optional[str] = None

    # OpenAI settings
    OPENAI_API_KEY: str

    # LLM Model settings
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024

    # RAG settings
    TOP_K_DOCS: int = 10  # Increased for similarity filtering
    MIN_CHARS_PER_CHUNK: int = 100

    # Similarity score threshold
    MIN_SIMILARITY_SCORE: float = 0.1  # Minimum similarity score to include document

    # Qdrant settings
    QDRANT_PATH: str
    QDRANT_COLLECTION_NAME: str = "openai_docs"

    # Document loader settings
    DOCUMENT_LOADER_DIR: str

    # Document chunking settings
    CHUNK_SIZE: int = 4000
    CHUNK_OVERLAP: int = 200

    # Embedding settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_BATCH_SIZE: int = 100

    # Vector store settings
    VECTOR_DIMENSION: int = 1536  # text-embedding-3-small dimension
    INGESTION_BATCH_SIZE: int = 50

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
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
