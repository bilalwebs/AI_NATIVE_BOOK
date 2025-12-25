import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the RAG pipeline"""

    # Cohere API configuration
    COHERE_API_KEY = os.getenv('COHERE_API_KEY')
    COHERE_MODEL = os.getenv('COHERE_MODEL', 'embed-english-v3.0')

    # Qdrant configuration
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
    QDRANT_URL = os.getenv('QDRANT_URL')
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))

    # Chunking configuration
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 512))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))

    # Crawling configuration
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', 1.0))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))

    # Validation
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        missing_vars = []
        if not cls.COHERE_API_KEY:
            missing_vars.append('COHERE_API_KEY')
        if not cls.QDRANT_API_KEY:
            missing_vars.append('QDRANT_API_KEY')
        if not cls.QDRANT_URL:
            missing_vars.append('QDRANT_URL')

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        return True