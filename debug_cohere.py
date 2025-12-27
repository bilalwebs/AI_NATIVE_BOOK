"""
Debug script to check Cohere client initialization issue
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from backend.config.settings import settings
    print(f"COHERE_API_KEY length: {len(settings.COHERE_API_KEY) if settings.COHERE_API_KEY else 0}")

    import cohere
    print("Attempting to initialize Cohere client...")

    # Test direct initialization
    try:
        cohere_client = cohere.Client(api_key=settings.COHERE_API_KEY)
        print("Direct initialization successful")

        # Test a simple embed call to verify the API key works
        response = cohere_client.embed(texts=["test"], model="embed-english-v3.0", input_type="search_query")
        print(f"Embed call successful, got {len(response.embeddings)} embedding(s)")
    except Exception as e:
        print(f"Direct initialization failed: {str(e)}")

    # Test the RAG service initialization
    print("\nTesting RAG service initialization...")
    from backend.services.rag_service import rag_service
    print(f"RAG service created: {rag_service is not None}")
    print(f"Cohere client in rag_service: {rag_service.cohere_client is not None}")

    if rag_service.cohere_client is None:
        print("Cohere client is None in the RAG service")
    else:
        print("Cohere client is initialized in the RAG service")

except Exception as e:
    print(f"Error in debug script: {str(e)}")
    import traceback
    traceback.print_exc()