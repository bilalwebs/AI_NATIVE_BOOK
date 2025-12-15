# Research: Integrated RAG Chatbot Embedded in Technical Book

## Phase 0: Design Research

### Decision: Chunk Size Selection
- **Rationale**: For technical book content, we need to balance retrieval accuracy with contextual coherence. After researching best practices for RAG systems, 300-400 tokens is optimal for technical content as it captures complete concepts while maintaining precise retrieval.
- **Decision**: Set chunk size to 350 tokens with 50-token overlap
- **Alternatives considered**:
  1. 200-token chunks: More precise retrieval but may fragment technical concepts
  2. 500-token chunks: Better context but potential for mixed topics within chunks
  3. Variable chunks based on section breaks: More semantically meaningful but complex to implement

### Decision: Vector Database Selection
- **Rationale**: Qdrant Cloud was specified in requirements, but research confirmed its advantages for this use case: efficient similarity search, good Python integration, and free tier availability suitable for prototype.
- **Decision**: Use Qdrant Cloud as specified in requirements
- **Alternatives considered**:
  1. Pinecone: More enterprise-focused, higher cost
  2. Weaviate: Good capabilities but Cohere integration not as seamless
  3. Supabase Vector: Newer option, less proven for production use

### Decision: Embedding Model Selection
- **Rationale**: Cohere embeddings were specified in requirements. Research shows Cohere embeddings perform well for retrieval tasks, especially for technical content, with good semantic understanding.
- **Decision**: Use Cohere embedding models as specified
- **Alternatives considered**:
  1. OpenAI embeddings: Higher cost, violates requirement to avoid OpenAI
  2. Sentence Transformers: Self-hosted option but requires more infrastructure
  3. Google embeddings: Different ecosystem than required

### Decision: API Architecture Pattern
- **Rationale**: For RAG systems, we need stateless APIs that can handle both book-wide retrieval and selected-text modes. FastAPI provides excellent async support and performance for AI applications.
- **Decision**: Implement REST API with FastAPI
- **Alternatives considered**:
  1. GraphQL: More flexible but unnecessary complexity for this use case
  2. gRPC: Better performance but more complex client integration
  3. Serverless functions: Scalable but more complex state management

### Decision: Text Chunking Algorithm
- **Rationale**: Deterministic chunking is required for consistent retrieval. Research shows sentence-boundary aware chunking works best for technical content to avoid breaking logical units.
- **Decision**: Use sentence-aware chunking with overlap for context continuity
- **Alternatives considered**:
  1. Fixed token boundaries: Simpler but may split sentences
  2. Semantic chunking: More contextually relevant but computationally expensive
  3. Chapter/section-based chunking: Respects document structure but may create oversized chunks

### Decision: Conversation Session Management
- **Rationale**: For selected-text mode, we must ensure no conversation memory is used, but for book-wide mode we can store sessions. Neon Serverless Postgres is specified and supports both requirements.
- **Decision**: Store sessions with strict isolation between modes
- **Alternatives considered**:
  1. In-memory storage: Faster but not persistent
  2. No session storage: Simpler but loses conversation context for book-wide mode
  3. Redis: Better performance but adds infrastructure complexity

### Decision: Safety and Validation Approach
- **Rationale**: Zero hallucinations is a hard requirement. Research indicates multi-layer validation is needed: context validation, source attribution, and response verification.
- **Decision**: Implement validation at multiple levels (input, retrieval, generation, output)
- **Alternatives considered**:
  1. Single validation at generation: Simpler but less robust
  2. External fact-checking service: More accurate but slower and adds dependencies
  3. LLM-based validation: Self-validating approach but still risk of hallucination

### Decision: Frontend Integration Pattern
- **Rationale**: Docusaurus integration needs to pass selected text to backend and display responses. Research on similar implementations suggests iframe or direct API integration.
- **Decision**: Direct API integration to maintain full control over UX
- **Alternatives considered**:
  1. iFrame embedding: Isolated but more complex communication
  2. Widget approach: Reusable but potentially less integrated feel
  3. Server-side rendering: More complex but possible performance benefits