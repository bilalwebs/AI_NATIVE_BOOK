"""
Check Qdrant client methods
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from backend.config.settings import settings
    from qdrant_client import QdrantClient

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=30
    )

    # List available methods
    methods = [method for method in dir(qdrant_client) if not method.startswith('_')]
    print("Available Qdrant client methods:")
    for method in sorted(methods):
        print(f"  - {method}")

    # Check specifically for search methods
    search_methods = [method for method in methods if 'search' in method.lower()]
    print(f"\nSearch-related methods: {search_methods}")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()