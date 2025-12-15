# API Contract: RAG Chatbot Service

## Overview
API contract for the Retrieval-Augmented Generation (RAG) chatbot embedded in a technical book. The API supports both book-wide question answering (with vector retrieval) and selected-text question answering (with isolated context).

## Base URL
`/api/v1`

## Authentication
All endpoints require API key authentication via header:
```
Authorization: Bearer {API_KEY}
```

## Endpoints

### POST /chat
Process user questions using either book-wide retrieval or selected-text context.

#### Request
```json
{
  "query": "What is the main concept of chapter 3?",
  "mode": "book-wide",
  "selected_text": "Optional text when mode is 'selected-text'"
}
```

#### Request Parameters
- `query` (string, required): The user's question
- `mode` (string, required): Either "book-wide" or "selected-text"
- `selected_text` (string, optional): Text selected by the user (required when mode is "selected-text")

#### Response (Success)
```json
{
  "response": "The main concept of chapter 3 is...",
  "sources": [
    {
      "chapter": "Chapter 3",
      "section": "3.1 Introduction",
      "text": "The relevant text that was used to generate the response"
    }
  ],
  "mode_used": "book-wide",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Response (Insufficient Context - Selected Text Mode)
```json
{
  "response": "The answer is not available in the selected text.",
  "sources": [],
  "mode_used": "selected-text",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Response (Error)
```json
{
  "error": {
    "code": "INSUFFICIENT_CONTEXT",
    "message": "The query cannot be answered with the provided context"
  }
}
```

#### Error Codes
- `INSUFFICIENT_CONTEXT`: Query cannot be answered with available context
- `INVALID_MODE`: Mode parameter is not valid
- `VALIDATION_ERROR`: Request parameters don't meet requirements
- `INTERNAL_ERROR`: Unexpected server error

### POST /ingest
Ingest book content for RAG functionality.

#### Request
```json
{
  "book_content": [
    {
      "chapter": "Chapter 1",
      "section": "1.1 Introduction",
      "content": "Full text content of the section..."
    }
  ],
  "book_id": "technical-book-001"
}
```

#### Response (Success)
```json
{
  "status": "success",
  "chunks_processed": 45,
  "book_id": "technical-book-001",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### GET /health
Check the health status of the service and its dependencies.

#### Response (Success)
```json
{
  "status": "healthy",
  "checks": {
    "database": "connected",
    "vector_store": "connected",
    "ai_service": "available",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

## Mode Behaviors

### Book-wide Mode
1. Performs content search across the entire book
2. Retrieves relevant segments using vector similarity
3. Generates response based on retrieved information
4. Includes source citations in the response

### Selected-text Mode
1. Uses only the provided selected_text as context
2. No content search or access to other book content
3. Generates response based only on the selected text
4. If selected_text is insufficient, returns "The answer is not available in the selected text."

## Response Guarantees

1. All responses are grounded in either retrieved book content or selected text only
2. No external or general knowledge is used
3. Zero hallucinations - information only comes from provided context
4. In selected-text mode, responses are 100% isolated from broader book context