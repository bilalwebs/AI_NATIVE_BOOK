import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the RAG pipeline"""

    # Cohere API configuration
    COHERE_API_KEY = os.getenv('COHERE_API_KEY')
    COHERE_MODEL = os.getenv('COHERE_MODEL', 'embed-english-v3.0')

    # Qdrant Cloud configuration
    QDRANT_URL = os.getenv('QDRANT_URL')
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

    # Chunking configuration
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '512'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))

    # Processing configuration
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))

    # Validation
    @classmethod
    def validate(cls):
        """Validate that required configuration values are present"""
        errors = []
        if not cls.COHERE_API_KEY:
            errors.append("COHERE_API_KEY is required")
        if not cls.QDRANT_URL:
            errors.append("QDRANT_URL is required")
        if not cls.QDRANT_API_KEY:
            errors.append("QDRANT_API_KEY is required")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")