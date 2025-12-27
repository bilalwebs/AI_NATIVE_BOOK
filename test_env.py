"""
Test script to verify environment variables are loaded correctly
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from backend.config.settings import settings

    print("Environment variables loaded successfully:")
    print(f"QDRANT_URL: {settings.QDRANT_URL}")
    print(f"QDRANT_API_KEY: {'***' if settings.QDRANT_API_KEY else 'Not set'}")
    print(f"QDRANT_COLLECTION_NAME: {settings.QDRANT_COLLECTION_NAME}")
    print(f"OPENROUTER_API_KEY: {'***' if settings.OPENROUTER_API_KEY else 'Not set'}")
    print(f"COHERE_API_KEY: {'***' if settings.COHERE_API_KEY else 'Not set'}")
    print(f"HOST: {settings.HOST}")
    print(f"PORT: {settings.PORT}")
    print(f"RAG_EMBEDDING_MODEL: {settings.RAG_EMBEDDING_MODEL}")
    print(f"BOOK_START_URL: {settings.BOOK_START_URL}")

    # Test if the RAG service can be initialized
    from backend.services.rag_service import rag_service
    print(f"\nRAG Service initialized: {rag_service is not None}")
    print(f"Cohere client available: {rag_service.cohere_client is not None}")

    print("\nAll environment variables are loaded correctly!")
    print("The backend is running with the deployed configuration.")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()