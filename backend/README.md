# RAG Chatbot Backend

FastAPI-based backend for the Retrieval-Augmented Generation (RAG) chatbot.

## Overview

This backend provides a REST API for a RAG chatbot that retrieves relevant information from a vector database (Qdrant Cloud) and generates responses using an LLM (via OpenRouter).

## Features

- FastAPI-based REST API
- Retrieval-Augmented Generation functionality
- Integration with Qdrant Cloud for vector storage
- OpenRouter integration for LLM access
- Streaming chat responses (planned)
- CORS support for frontend integration

## Architecture

```
Frontend UI → FastAPI Backend → Qdrant Cloud (retrieval) → OpenRouter (generation)
```

## Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/chat` - Main chat endpoint
- `POST /api/v1/chat/stream` - Streaming chat endpoint (planned)
- `GET /api/v1/chat/models` - Available models

## Configuration

The backend uses environment variables for configuration. Create a `.env` file with the following variables:

```env
# Qdrant Configuration
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION_NAME=book_embeddings

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Cohere Configuration (for embedding to match existing pipeline)
COHERE_API_KEY=your_cohere_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in a `.env` file

3. Run the server:
   ```bash
   python -m backend.main
   ```

## Running Tests

```bash
python -m pytest backend/test_backend.py
```

## API Usage

### Chat Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your question here",
    "top_k": 5,
    "score_threshold": 0.5
  }'
```

## Dependencies

- FastAPI
- Pydantic
- Qdrant Client
- OpenAI (for OpenRouter API)
- Cohere (for embedding)
- Pydantic Settings