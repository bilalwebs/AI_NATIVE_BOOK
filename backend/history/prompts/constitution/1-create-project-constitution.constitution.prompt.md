---
id: 1
title: Create-Project-Constitution
stage: constitution
date: 2025-12-15
surface: agent
model: Qwen
feature: none
branch: main
user: user
command: /sp.constitution
labels: [constitution,specify,rag-chatbot]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
---

## Prompt

```
/sp.constitution Project: Integrated RAG Chatbot embedded in a published technical book

Purpose:
Design and implement a Retrieval-Augmented Generation (RAG) chatbot that is embedded inside a published book and answers user questions strictly based on the book’s content or user-selected text.

Core Principles:
- Groundedness First: The chatbot must never answer beyond retrieved or explicitly provided text.
- Source Authority: The book content is the single source of truth.
- Deterministic Behavior: Responses should be explainable, reproducible, and traceable to retrieved chunks.
- Spec-Driven Development: All design and implementation must follow SpecifyKit workflows.
- Model Neutrality: Architecture must not be coupled to OpenAI APIs.

LLM & AI Standards:
- LLM Provider: Cohere (mandatory)
- Embeddings: Cohere embedding models only
- CLI Tooling: Qwen CLI is the authoritative interface for prompt, spec, and task execution
- OpenAI APIs: Explicitly prohibited (no keys, no SDKs, no fallback)

RAG Behavior Rules:
- The chatbot MUST retrieve relevant chunks from Qdrant before generating any answer.
- If no relevant context is retrieved, the chatbot must reply:
  "The answer is not available in the provided content."
- For "selected-text mode":
  - Only the user-selected text is allowed as context.
  - Vector search and global book retrieval are disabled.
  - Any external or inferred knowledge is forbidden.

Answer Constraints:
- No hallucinations, speculation, or external knowledge
- No training-data claims
- No "general AI knowledge" unless explicitly present in retrieved text
- Answers must reference the retrieved chunk(s) internally (IDs or citations)

Data & Infrastructure Constraints:
- Vector Store: Qdrant Cloud (Free Tier)
- Metadata & Sessions: Neon Serverless Postgres
- API Layer: FastAPI (Python)
- Stateless backend design preferred
- All secrets managed via environment variables

Quality & Safety Standards:
- Prompt injection resistance required
- User input must not override system or RAG constraints
- Selected-text isolation must be strictly enforced
- Rate limits and graceful degradation required (free-tier aware)

Documentation Standards:
- Every module must include:
  - Purpose
  - Inputs / Outputs
  - Failure modes
- RAG pipeline must be documented end-to-end
- Clear separation between ingestion, retrieval, and generation

Success Criteria:
- 100% answers are grounded in retrieved or selected text
- Zero OpenAI dependencies
- Cohere-only AI stack
- Selected-text questions never leak global context
- System passes manual hallucination and grounding tests
- Architecture is fully specifiable, plannable, and task-breakable via SpecifyKit

Non-Goals (Explicit):
- No creative writing beyond source text
- No autonomous reasoning outside provided context
- No black-box LLM behavior
```

## Response snapshot

The project constitution for the Integrated RAG Chatbot has been successfully created at `.specify/memory/constitution.md`. The file includes all the specified sections:

- Core Principles
- LLM & AI Standards
- RAG Behavior Rules
- Answer Constraints
- Data & Infrastructure Constraints
- Quality & Safety Standards
- Documentation Standards
- Success Criteria
- Non-Goals (Explicit)
- Amendment Procedure
- Versioning Policy
- Compliance Review Expectations

The constitution is properly formatted with clear headings, detailed sections, and follows all the requirements specified by the user. The version is set to 1.0.0, with today's date as both ratification and last amended date.

## Outcome

- ✅ Impact: Successfully created the project constitution file containing all required principles and constraints
- 🧪 Tests: N/A (Documentation creation task)
- 📁 Files: Created .specify/memory/constitution.md with all required sections
- 🔁 Next prompts: User can now proceed with specification, planning, and implementation using the constitution as a guide
- 🧠 Reflection: The constitution provides a strong foundation for the RAG chatbot project with clear constraints and guidelines

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Begin with project specification based on the established constitution