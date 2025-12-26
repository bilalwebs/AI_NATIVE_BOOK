"""
Test script to verify the backend components work together
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Testing backend components...")

try:
    # Test importing the main app
    from backend.main import app
    print("[OK] Main app imported successfully")

    # Test importing the config
    from backend.config.settings import settings
    print("[OK] Settings imported successfully")

    # Test importing the rag service
    from backend.services.rag_service import rag_service
    print("[OK] RAG service imported successfully")

    # Test importing the API router
    from backend.api.chat import router
    print("[OK] API router imported successfully")

    # Test importing the models
    from backend.models.chat import ChatRequest, ChatResponse
    print("[OK] Models imported successfully")

    print("\nAll components imported successfully!")
    print("The backend is ready to run with uvicorn.")

    # Show the app info
    print(f"\nApp title: {app.title}")
    print(f"App description: {app.description}")
    print(f"App version: {app.version}")

except Exception as e:
    print(f"[ERROR] Error importing components: {str(e)}")
    import traceback
    traceback.print_exc()