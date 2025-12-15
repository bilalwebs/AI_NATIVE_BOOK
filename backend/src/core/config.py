from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_title: str = "RAG Chatbot Backend API"
    app_description: str = "Backend API for RAG chatbot embedded in technical book"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # External service configuration
    qdrant_api_key: Optional[str] = None
    qdrant_url: Optional[str] = None
    qdrant_cluster_id: Optional[str] = None
    neon_database_url: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # Application-specific settings
    chunk_size: int = 350  # tokens
    chunk_overlap: int = 50  # tokens
    max_tokens_per_chunk: int = 400
    top_k_retrieval: int = 5

    class Config:
        env_file = ".env"


settings = Settings()