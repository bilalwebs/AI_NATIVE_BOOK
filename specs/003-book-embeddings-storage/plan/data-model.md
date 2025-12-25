# Data Model: Book Embeddings Storage

## Core Entities

### Document Chunk
- **chunk_id**: Unique identifier for the text chunk
- **content**: The text content of the chunk (string)
- **source_url**: Original URL where the content was found (string)
- **page_title**: Title of the source page (string)
- **chunk_order**: Sequential order of the chunk in the document (integer)
- **metadata**: Additional metadata about the chunk (JSON object)

### Embedding Vector
- **embedding_id**: Unique identifier for the embedding record
- **chunk_id**: Reference to the source chunk
- **vector**: The embedding vector (array of floats)
- **model**: Name of the model used to generate the embedding (string)
- **created_at**: Timestamp when the embedding was generated (datetime)

### Storage Record
- **record_id**: Unique identifier for the storage record
- **embedding_id**: Reference to the embedding
- **payload**: Metadata payload stored with the vector in Qdrant (JSON object)
  - Includes: content, source_url, page_title, chunk_order
- **vector_size**: Dimension of the embedding vector (integer)

## Qdrant Collection Schema

### Collection Name: `book_embeddings`

### Vector Configuration:
- Size: 1024 (for Cohere embed-english-v3.0)
- Distance: Cosine

### Payload Schema:
```
{
  "content": "string",
  "source_url": "string",
  "page_title": "string",
  "chunk_order": "integer",
  "chunk_id": "string"
}
```

## Relationships
- Each Document Chunk generates one Embedding Vector
- Each Embedding Vector is stored as one Storage Record in Qdrant
- Multiple chunks from the same source URL are linked via the source_url field