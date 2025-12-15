# Implementation Plan: Integrated RAG Chatbot Embedded in Technical Book

**Branch**: `002-embed-rag-chatbot` | **Date**: 2025-01-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements a Retrieval-Augmented Generation (RAG) chatbot that is embedded inside a technical book and answers user questions strictly from book content or explicitly selected text. The implementation will feature book-wide question answering with vector-based retrieval, selected-text question answering with isolated context, and a backend API structure using FastAPI with Cohere for LLM and embeddings.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, Cohere SDK, Qdrant client, Pydantic, SQLAlchemy
**Storage**: Qdrant Cloud (vector storage), Neon Serverless Postgres (metadata/session storage)
**Testing**: pytest for backend, manual validation for hallucination checks
**Target Platform**: Linux/Windows server (backend API), Web browser (frontend integration)
**Project Type**: Web application (backend API serving RAG functionality to frontend)
**Performance Goals**: <2s response time for queries, handle 100 concurrent users
**Constraints**: Zero hallucinations, strict context isolation, no external knowledge, <200ms embedding generation
**Scale/Scope**: Single book with up to 1000+ pages of technical content, 10k monthly active readers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Uses single project structure (not violating multi-project constraint)
- [x] Uses designated technology stack (FastAPI, Cohere, Qdrant, Postgres)
- [x] Implements proper security with environment variables for credentials
- [x] Follows RAG architecture constraints (no general knowledge, zero hallucinations)
- [x] Implements proper testing strategy with validation checks

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── text_segment.py          # BookTextSegment entity
│   │   ├── conversation_session.py  # ConversationSession entity
│   │   └── book_section.py          # BookSection entity
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embedding_service.py     # Cohere embedding generation
│   │   ├── retrieval_service.py     # Vector search and retrieval
│   │   ├── generation_service.py    # Cohere-based answer generation
│   │   ├── chunking_service.py      # Text segmentation logic
│   │   └── validation_service.py    # Hallucination and context checks
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py              # Chat endpoints
│   │   │   ├── ingestion.py         # Content ingestion endpoints
│   │   │   └── health.py            # Health check endpoints
│   │   └── dependencies.py          # API dependency injection
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration from environment
│   │   ├── security.py              # Security utilities
│   │   └── constants.py             # Application constants
│   └── main.py                      # Application entry point
├── tests/
│   ├── unit/
│   │   ├── test_chunking.py         # Chunking service tests
│   │   ├── test_retrieval.py        # Retrieval service tests
│   │   ├── test_generation.py       # Generation service tests
│   │   └── test_validation.py       # Validation service tests
│   ├── integration/
│   │   ├── test_api_chat.py         # Chat API integration tests
│   │   └── test_api_ingestion.py    # Ingestion API integration tests
│   └── contract/
│       └── test_context_isolation.py # Context isolation validation
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
└── docker-compose.yml              # Docker configuration
```

**Structure Decision**: Web application structure with backend API serving RAG functionality. The API will be consumed by the frontend Docusaurus application. This separates concerns between the RAG logic (backend) and presentation (frontend), enabling independent scaling and development cycles.

## Phases Implementation

### Phase 1: Ingestion
- Extract Markdown book content
- Deterministic chunking service with stable IDs
- Embedding generation using Cohere
- Vector + metadata storage in Qdrant with Neon Postgres for metadata

### Phase 2: Retrieval
- Query embedding service
- Top-k vector search (book-wide mode)
- Retrieval bypass for selected-text mode

### Phase 3: Generation
- Context-constrained prompting
- Cohere-based answer generation
- Fallback handling for insufficient context

### Phase 4: Validation
- Hallucination checks
- Context isolation verification
- System health validation

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |