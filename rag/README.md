# RAG Pipeline for Book Embeddings Storage

This directory contains the implementation of a Retrieval-Augmented Generation (RAG) pipeline that crawls Docusaurus book URLs, generates embeddings using Cohere models, and stores them in Qdrant Cloud.

## Overview

The pipeline consists of the following main components:

1. **Crawling Module**: Crawls Docusaurus URLs and extracts clean text content
2. **Processing Module**: Chunks text and generates embeddings using Cohere
3. **Storage Module**: Stores embeddings in Qdrant Cloud with proper indexing
4. **Search Module**: Implements similarity search for retrieving relevant content

## Architecture

```
URL List → [Crawling Module] → Clean Text Content
                                    ↓
                    [Chunking/Embedding Module] → Embedding Vectors
                                    ↓
                         [Storage Module] → Qdrant Cloud
                                    ↓
                      [Search Module] → Validated Results
```

## Configuration

The pipeline uses the following environment variables:

- `COHERE_API_KEY`: API key for Cohere embedding service
- `QDRANT_API_KEY`: API key for Qdrant Cloud
- `QDRANT_URL`: URL for Qdrant Cloud instance
- `CHUNK_SIZE`: Maximum size of text chunks (default: 512)
- `CHUNK_OVERLAP`: Overlap size for text chunks (default: 50)
- `COHERE_MODEL`: Cohere model to use for embeddings (default: embed-english-v3.0)

## Usage

### Command Line Interface

The pipeline provides a command-line interface:

```bash
# Process URLs directly
python -m rag.cli run --urls https://example.com/docs/page1 https://example.com/docs/page2

# Process URLs from a file
python -m rag.cli run --url-file urls.txt

# Validate the pipeline
python -m rag.cli validate

# Check configuration
python -m rag.cli check-config
```

### Direct API Usage

```python
from rag.pipeline import PipelineOrchestrator
from rag.config.config import Config

# Initialize the orchestrator
orchestrator = PipelineOrchestrator()

# Run the pipeline
result = orchestrator.run_pipeline(
    urls=['https://example.com/docs'],
    collection_name='my_embeddings',
    recreate_collection=False
)

print(f"Pipeline success: {result['success']}")
```

## Components

### Crawling
- `url_crawler.py`: Handles URL crawling with error handling and retry logic
- `content_extractor.py`: Extracts clean text content from HTML pages
- `docusaurus_selectors.py`: CSS selectors for Docusaurus-specific content extraction

### Processing
- `chunker.py`: Splits text into appropriately sized chunks
- `embedding_client.py`: Generates embeddings using Cohere API
- `pipeline.py`: Orchestrates the complete pipeline

### Storage
- `qdrant_storage.py`: Stores embeddings in Qdrant Cloud
- `qdrant_search.py`: Implements similarity search
- `qdrant_schema.py`: Defines collection schema and payload structure

## Performance

The pipeline is designed to process a 100-page book within 30 minutes, meeting the following success criteria:
- 95% URL crawling success rate
- 99% embedding generation success rate
- 99% storage success rate
- 90% search relevance accuracy

## Error Handling

The pipeline implements comprehensive error handling:
- Network request retries with exponential backoff
- Graceful degradation when individual URLs fail
- Detailed logging for debugging
- Validation of embeddings and storage operations

## Testing

To validate the pipeline functionality:

```bash
python -m rag.validation
```

For performance testing:

```bash
python -m rag.performance_test
```