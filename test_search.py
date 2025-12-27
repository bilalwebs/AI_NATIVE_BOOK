"""
Test script to check the actual error in the RAG service
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from backend.services.rag_service import rag_service
    print(f"Cohere client initialized: {rag_service.cohere_client is not None}")
    print(f"Qdrant client initialized: {rag_service.qdrant_client is not None}")
    print(f"Collection name: {rag_service.collection_name}")

    # Test the search function directly
    try:
        results = rag_service.search_similar_content("test", top_k=1, score_threshold=0.1)
        print(f"Search successful, got {len(results)} results")
    except Exception as e:
        print(f"Search failed: {str(e)}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"Error in test: {str(e)}")
    import traceback
    traceback.print_exc()