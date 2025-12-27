"""
Test OpenRouter API connection
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from backend.config.settings import settings
    import httpx
    import openai

    print(f"OpenRouter API Key: {'***' if settings.OPENROUTER_API_KEY else 'Not set'}")
    print(f"OpenRouter Model: {settings.OPENROUTER_MODEL}")

    # Test OpenAI client with OpenRouter
    timeout = httpx.Timeout(timeout=60.0, connect=10.0)
    http_client = httpx.Client(timeout=timeout)

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        http_client=http_client
    )

    print("OpenAI client created successfully")

    # Test a simple chat completion
    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[{"role": "user", "content": "Hello, test"}],
        temperature=0.7,
        max_tokens=50
    )

    print(f"OpenRouter test successful")

except Exception as e:
    print(f"Error testing OpenRouter: {str(e)}")
    import traceback
    traceback.print_exc()