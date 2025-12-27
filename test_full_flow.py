"""
Test the full API flow
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from backend.services.rag_service import rag_service
    from backend.config.settings import settings

    print(f"Cohere client initialized: {rag_service.cohere_client is not None}")

    # Simulate the full flow like in the API
    query = "Hello"

    # Step 1: Search for similar content
    print("Step 1: Searching for similar content...")
    similar_chunks = rag_service.search_similar_content(
        query=query,
        top_k=5,
        score_threshold=0.5
    )
    print(f"Found {len(similar_chunks)} similar chunks")

    # Step 2: Get context from chunks
    print("Step 2: Getting context from chunks...")
    context = rag_service.get_context_from_chunks(
        chunks=similar_chunks,
        max_length=settings.RAG_MAX_CONTEXT_LENGTH
    )
    print(f"Context length: {len(context)}")

    # Step 3: Generate response
    print("Step 3: Generating response...")
    response = rag_service.generate_response(
        query=query,
        context=context,
        history=None
    )
    print(f"Response: {response}")

except Exception as e:
    print(f"Error in full flow: {str(e)}")
    import traceback
    traceback.print_exc()