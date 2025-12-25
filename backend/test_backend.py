"""
Basic tests for the FastAPI RAG Chatbot Backend.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    """
    return TestClient(app)


def test_root_endpoint(client):
    """
    Test the root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "RAG Chatbot Backend API" in data["message"]
    assert "status" in data
    assert data["status"] == "running"


def test_health_endpoint(client):
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["status"] == "healthy"
    assert data["service"] == "RAG Chatbot Backend"


def test_chat_endpoint_exists(client):
    """
    Test that the chat endpoint exists.
    """
    # Test that we get a proper error (422) for missing request body
    # rather than a 404 for endpoint not found
    response = client.post("/api/v1/chat")
    assert response.status_code == 422  # Unprocessable Entity due to missing body


if __name__ == "__main__":
    pytest.main([__file__])