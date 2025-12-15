# Quickstart Guide: Integrated RAG Chatbot

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git
- Access to Qdrant Cloud (Free Tier)
- Access to Cohere API
- Access to Neon Serverless Postgres

## Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create and configure your environment file:
   ```bash
   cp .env.example .env
   ```

5. Add your credentials to `.env`:
   ```env
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_URL=your_qdrant_cluster_url
   QDRANT_CLUSTER_ID=your_qdrant_cluster_id
   NEON_DATABASE_URL=your_neon_database_connection_string
   COHERE_API_KEY=your_cohere_api_key
   ```

## Book Content Ingestion

1. Prepare your book content in a structured format (e.g., markdown files)

2. Run the ingestion script:
   ```bash
   python -m src.scripts.ingest_book --source-path /path/to/book/content
   ```

3. The script will:
   - Chunk the book content using sentence-aware chunking
   - Generate embeddings using Cohere
   - Store vectors in Qdrant
   - Store metadata in Neon Postgres

## Running the API Server

1. Start the FastAPI server:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

2. The API will be available at `http://localhost:8000`

3. API documentation available at `http://localhost:8000/docs`

## Testing the API

1. Book-wide question answering:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is the main concept of chapter 3?",
       "mode": "book-wide"
     }'
   ```

2. Selected-text question answering:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Explain this concept",
       "mode": "selected-text",
       "selected_text": "The technical concept is defined as..."
     }'
   ```

## Frontend Integration

1. The API endpoints are designed to be consumed by a Docusaurus frontend
2. Implement a chat widget that can:
   - Capture user questions
   - Detect if text is selected
   - Call the appropriate API endpoint based on mode
   - Display responses with source attribution

## Health Checks

Check the health of the system:
```bash
curl http://localhost:8000/health
```

This will verify:
- Database connectivity
- Vector store connectivity
- AI service connectivity
- Overall system health