<!-- SYNC IMPACT REPORT (generated during last update)
     Version Change: N/A (initial creation)
     Modified Principles: N/A (initial creation)
     Added Sections: All sections (initial creation)
     Removed Sections: None
     Templates Updated: N/A (initial creation)
     Follow-up TODOs: None
-->

# Project Constitution: Integrated RAG Chatbot

**Project Name:** Integrated RAG Chatbot embedded in a published technical book  
**Version:** 1.0.0  
**Ratification Date:** 2025-12-15  
**Last Amended Date:** 2025-12-15  

## Core Principles

### Groundedness First
The chatbot must never answer beyond retrieved or explicitly provided text. All responses must be directly grounded in the source material to maintain factual accuracy and prevent hallucinations.

### Source Authority
The book content is the single source of truth. No external knowledge, training data claims, or general AI knowledge unrelated to the book content is acceptable as a basis for responses.

### Deterministic Behavior
Responses should be explainable, reproducible, and traceable to retrieved chunks. The system must provide clear lineage from user query to retrieved content to generated response.

### Spec-Driven Development
All design and implementation must follow SpecifyKit workflows. This ensures systematic planning, specification, task breakdown, and verification throughout the development lifecycle.

### Model Neutrality
Architecture must not be coupled to specific LLM vendor APIs. The system should be designed for flexibility and vendor independence where possible, within the constraint of Cohere usage.

## LLM & AI Standards

### LLM Provider
Cohere is the mandatory LLM provider. All generation tasks must use Cohere's models exclusively.

### Embeddings
Cohere embedding models are the only allowed embeddings provider. This ensures consistency in vector representation and semantic search capabilities.

### CLI Tooling
Qwen CLI is the authoritative interface for prompt, spec, and task execution. All development workflows should leverage this tooling.

### OpenAI APIs Prohibition
OpenAI APIs are explicitly prohibited. No OpenAI keys, SDKs, or fallback mechanisms are allowed in the implementation.

## RAG Behavior Rules

### Mandatory Retrieval
The chatbot MUST retrieve relevant chunks from Qdrant before generating any answer. No direct generation from the LLM without retrieved context is permitted.

### No Context Fallback
If no relevant context is retrieved, the chatbot must reply: "The answer is not available in the provided content." No attempts to generate answers without appropriate context are allowed.

### Selected-Text Mode Constraints
For "selected-text mode":
- Only the user-selected text is allowed as context.
- Vector search and global book retrieval are disabled.
- Any external or inferred knowledge is forbidden.
- The system must strictly isolate selected text from the broader book corpus.

## Answer Constraints

### Hallucination Prevention
No hallucinations, speculation, or external knowledge is permitted. Answers must be strictly based on retrieved content.

### Training Data Claims
No claims about training data unless explicitly present in the retrieved text are allowed.

### General AI Knowledge
No "general AI knowledge" unless explicitly present in retrieved text. The system must not fall back to general knowledge when context is insufficient.

### Reference Requirement
Answers must reference the retrieved chunk(s) internally (IDs or citations) to maintain traceability.

## Data & Infrastructure Constraints

### Vector Store
Qdrant Cloud (Free Tier) is the designated vector store. All embedding storage and similarity search must use this platform.

### Metadata & Sessions
Neon Serverless Postgres is the database for metadata and user sessions. All state management must leverage this technology.

### API Layer
FastAPI (Python) is the specified framework for the API layer. All backend services must be implemented using this framework.

### Stateless Design
A stateless backend design is preferred to improve scalability and reliability.

### Secrets Management
All secrets must be managed via environment variables. No hardcoded credentials or API keys are permitted.

## Quality & Safety Standards

### Prompt Injection Resistance
Prompt injection resistance is required. The system must validate and sanitize user input to prevent manipulation of system behavior.

### Input Constraint Enforcement
User input must not override system or RAG constraints. The architecture must enforce grounding regardless of user requests.

### Selected-Text Isolation
Selected-text isolation must be strictly enforced. Content from selected text must not leak into global context queries and vice versa.

### Rate Limits and Degradation
Rate limits and graceful degradation are required, with awareness of free-tier limitations and constraints.

## Documentation Standards

### Module Documentation
Every module must include:
- Purpose
- Inputs / Outputs
- Failure modes

### RAG Pipeline Documentation
The RAG pipeline must be documented end-to-end, showing the complete flow from query processing to retrieval to generation.

### Clear Separation
Clear separation between ingestion, retrieval, and generation components must be maintained and documented.

## Success Criteria

### Grounding Assurance
100% of answers must be grounded in retrieved or selected text. No exceptions to this fundamental requirement.

### OpenAI Independence
Complete absence of OpenAI dependencies. The system must function exclusively with Cohere services.

### Cohere-Only Stack
Implementation must use only Cohere's AI stack, with no mixing of providers.

### Context Isolation
Selected-text questions must never leak global context. Strict isolation between modes is essential.

### Testing Compliance
System must pass manual hallucination and grounding tests with consistent performance.

### Specifiable Architecture
Architecture must be fully specifiable, plannable, and task-breakable via SpecifyKit methodologies.

## Non-Goals (Explicit)

### Creative Writing
No creative writing beyond source text is permitted. The system is not a creative writing assistant.

### Autonomous Reasoning
No autonomous reasoning outside provided context is allowed. The system must not reason beyond the provided text.

### Black-Box Behavior
No black-box LLM behavior. All responses must be explainable and traceable to source material.

## Amendment Procedure

Changes to this constitution require:
1. Formal proposal with justification
2. Review by project stakeholders
3. Approval by majority consensus
4. Version increment according to semantic versioning

## Versioning Policy

- MAJOR: Backwards incompatible changes to governance or principle definitions
- MINOR: Addition of new principles or substantial expansion of guidance
- PATCH: Clarifications, wording changes, non-semantic refinements

## Compliance Review Expectations

All implementations must undergo periodic compliance reviews to ensure adherence to constitutional principles, particularly:
- Grounding requirements verification
- OpenAI prohibition enforcement
- Selected-text isolation testing
- RAG pipeline traceability validation