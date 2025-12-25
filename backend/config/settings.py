from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Qdrant settings
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "book_embeddings"

    # OpenRouter settings
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"

    # Cohere settings (for embedding to match existing pipeline)
    COHERE_API_KEY: str = ""

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]  # In production, specify exact origins

    # RAG settings
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.5
    RAG_MAX_CONTEXT_LENGTH: int = 2000

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()