# Quickstart Guide: Book Embeddings Storage

## Prerequisites

- Python 3.8 or higher
- Cohere API key
- Qdrant Cloud account and API key
- List of Docusaurus book URLs to process

## Setup

1. **Install dependencies**
   ```bash
   pip install cohere qdrant-client beautifulsoup4 requests python-dotenv
   ```

2. **Set up environment variables**
   Create a `.env` file with:
   ```
   COHERE_API_KEY=your_cohere_api_key
   QDRANT_URL=your_qdrant_cloud_url
   QDRANT_API_KEY=your_qdrant_api_key
   CHUNK_SIZE=512
   CHUNK_OVERLAP=50
   COHERE_MODEL=embed-english-v3.0
   ```

3. **Prepare your URL list**
   Create a text file with the Docusaurus book URLs you want to process, one per line.

## Running the Pipeline

### Phase 1: Content Extraction
```bash
python -m rag.crawling.url_crawler --urls urls.txt --output content.json
```

### Phase 2: Chunking and Embedding
```bash
python -m rag.processing.chunker --input content.json --output embeddings.json
```

### Phase 3: Storage
```bash
python -m rag.storage.qdrant_storage --input embeddings.json --collection book_embeddings
```

### Phase 4: Validation
```bash
python -m rag.validation.search_test --query "your test query here"
```

## Configuration Options

- `CHUNK_SIZE`: Size of text chunks (default: 512)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50)
- `COHERE_MODEL`: Cohere model to use (default: embed-english-v3.0)
- `BATCH_SIZE`: Number of chunks to process at once (default: 10)

## Expected Output

After running the complete pipeline:
- Content extracted and stored in content.json
- Embeddings generated and stored in embeddings.json
- Vectors stored in Qdrant Cloud collection
- Validation results showing search accuracy

## Troubleshooting

- **API Rate Limits**: The system implements automatic retry with exponential backoff
- **Large Documents**: Documents are automatically chunked to fit model limits
- **Network Issues**: Connection failures are retried with circuit breaker pattern