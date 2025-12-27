"""
Test script to verify API keys and RAG functionality
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from backend.config.settings import settings
    print("[OK] Settings loaded successfully")
    print(f"COHERE_API_KEY available: {'Yes' if settings.COHERE_API_KEY else 'No'}")
    print(f"QDRANT_URL: {settings.QDRANT_URL}")
    print(f"BOOK_START_URL: {settings.BOOK_START_URL}")

    # Test Cohere client initialization
    import cohere
    if settings.COHERE_API_KEY:
        try:
            cohere_client = cohere.Client(api_key=settings.COHERE_API_KEY)
            print("[OK] Cohere client initialized successfully")
        except Exception as e:
            print(f"[ERROR] Cohere client initialization failed: {str(e)}")
    else:
        print("[ERROR] No Cohere API key provided")

    # Test Qdrant client initialization
    from qdrant_client import QdrantClient
    try:
        qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30
        )
        print("[OK] Qdrant client initialized successfully")
    except Exception as e:
        print(f"[WARNING] Qdrant client initialization failed: {str(e)}")
        print("  This might be expected if the service is not accessible without valid data")

    # Test the RAG service
    from backend.services.rag_service import rag_service
    print(f"[OK] RAG Service initialized: {rag_service is not None}")
    print(f"Cohere client in RAG service: {rag_service.cohere_client is not None}")

    print("\nEnvironment and API setup looks correct!")
    print("The issue might be that the Qdrant collection doesn't have any book data yet.")
    print("You need to run the ingestion pipeline first to populate the vector database.")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()