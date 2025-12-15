# Feature Specification: Embedded RAG Chatbot for Book Content

**Feature Branch**: `001-embed-rag-chatbot`
**Created**: 2025-12-15
**Status**: Draft
**Input**: User description: "Project: Integrated RAG Chatbot Embedded in a Published Technical Book Objective: Specify a Retrieval-Augmented Generation (RAG) chatbot that is embedded inside a published book and answers user questions strictly from book content or explicitly selected text. Target Audience: - Readers of a technical AI / Robotics book - Students and developers seeking accurate, grounded explanations - Users requiring source-bound answers while reading Core Functional Scope: 1. Book-wide Question Answering - Questions answered only after vector-based retrieval - Retrieved chunks act as the sole context for generation 2. Selected-Text Question Answering - User-selected text is the ONLY allowed context - Vector search and global context are disabled - No inference beyond selected text permitted 3. Embedded UX - Chatbot is embedded within the book frontend (Docusaurus) - Context-aware interaction tied to reading position Technology Stack (Mandatory): - Backend: FastAPI (Python) - Vector Store: Qdrant Cloud (Free Tier) - Metadata / Sessions: Neon Serverless Postgres - LLM Provider: Cohere - Embeddings: Cohere Embedding Models - Spec & Task Execution: Qwen CLI - Frontend: Docusaurus Credential Management: - All credentials must be loaded via environment variables - No secrets are allowed in source code or prompts Required Environment Variables: - QDRANT_API_KEY - QDRANT_URL - QDRANT_CLUSTER_ID - NEON_DATABASE_URL - COHERE_API_KEY RAG System Requirements: - Deterministic text chunking with stable chunk IDs - Each chunk must include: - Source chapter/section - Chunk identifier - Text content - Retrieval is mandatory before generation - Generation without context is forbidden Selected-Text Mode Constraints: - Context = user-selected text only - No retrieval calls allowed - No previous conversation memory allowed - If insufficient context, respond: The answer is not available in the selected text. Quality & Safety Constraints: - Zero hallucinations - No external or general AI knowledge - No OpenAI APIs, SDKs, or keys (explicitly forbidden) - Prompt injection resistance required Success Criteria: - 100% responses grounded in retrieved or selected text - Cohere-only AI pipeline - Selected-text isolation verified via tests - No secrets committed to repository - System is fully specifiable, plannable, and taskable via SpecifyKit Not Building: - General-purpose AI assistant - Web search or external retrieval - Creative or speculative responses - Vendor comparisons - OpenAI-based tooling"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Book-wide Question Answering (Priority: P1)

A reader of the technical book encounters a concept they don't understand while reading and wants to ask the embedded chatbot a question about the book content. The reader types their question into the chatbot interface, and the system retrieves relevant text chunks from the book using vector search, then generates an answer based only on the retrieved content.

**Why this priority**: This is the core functionality of the RAG system - the primary value proposition is enabling users to ask questions about the book content and receive accurate, grounded answers.

**Independent Test**: Can be fully tested by asking questions about various book topics and verifying that answers are based solely on retrieved content from the book, not external knowledge.

**Acceptance Scenarios**:

1. **Given** user is reading the book content and has access to the embedded chatbot, **When** user asks a question about the book content, **Then** the system retrieves relevant text chunks and generates an answer based only on those chunks.
2. **Given** user asks a question that cannot be answered by the book content, **When** the system processes the question, **Then** it responds with "The answer is not available in the provided content."

---

### User Story 2 - Selected-Text Question Answering (Priority: P2)

A student reading the book selects a specific text passage and wants an explanation of that text. The student highlights the text and asks a question about it using the embedded chatbot. The system must answer only based on the selected text, with no access to the global book context or vector search.

**Why this priority**: This feature enables focused understanding of specific passages, which is valuable for students and developers who need to understand complex concepts in detail.

**Independent Test**: Can be tested by selecting text passages and asking questions about them, verifying that answers are based exclusively on the selected text without any external knowledge or book-wide retrieval.

**Acceptance Scenarios**:

1. **Given** user has selected text within the book, **When** user asks a question about the selected text, **Then** the system generates an answer based only on the selected text without performing vector search or accessing global context.
2. **Given** user has selected text that is insufficient to answer the question, **When** user asks a question about the selected text, **Then** the system responds with "The answer is not available in the selected text."

---

### User Story 3 - Embedded UX Interaction (Priority: P3)

A user reading the book in the Docusaurus-based frontend encounters the embedded chatbot interface and wants to interact with it while maintaining context of their current reading position. The chatbot should feel seamlessly integrated with the book experience.

**Why this priority**: While not the core RAG functionality, this is essential for user adoption and makes the system useful in the reading context where users need it.

**Independent Test**: Can be tested by navigating through different book sections and verifying that the chatbot interface remains accessible and maintains appropriate context for the current reading position.

**Acceptance Scenarios**:

1. **Given** user is reading a specific section of the book, **When** user interacts with the embedded chatbot, **Then** the chatbot is accessible and responsive within the reading UI.
2. **Given** user switches between different book sections, **When** user asks questions, **Then** the chatbot maintains awareness of the reading context without losing conversational state inappropriately.

---

### Edge Cases

- What happens when a user asks a question while no book content has been indexed yet?
- How does the system handle very long or very short user queries?
- What happens when the vector store is unavailable or returns no results?
- How does the system handle attempts to inject prompts that bypass safety constraints?
- What occurs when users try to request information outside the scope of the book content?
- How does the system handle simultaneous requests from multiple users?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST retrieve relevant text chunks from book content using vector search before generating any answer
- **FR-002**: System MUST generate answers based solely on retrieved text chunks, with zero hallucinations or external knowledge
- **FR-003**: Users MUST be able to select specific text passages and ask questions about only that selected text
- **FR-004**: System MUST isolate selected-text mode from global book context, with no vector search or global retrieval
- **FR-005**: System MUST respond with "The answer is not available in the selected text" when selected text is insufficient for answering
- **FR-006**: System MUST implement prompt injection resistance to prevent bypassing safety constraints
- **FR-007**: System MUST ensure 100% of answers are grounded in retrieved or selected text
- **FR-008**: System MUST maintain deterministic text chunking with stable chunk IDs for retrieval consistency
- **FR-009**: Each text chunk MUST include source chapter/section, chunk identifier, and text content
- **FR-010**: System MUST use Cohere as the sole LLM provider, with no OpenAI API dependencies
- **FR-011**: System MUST use Cohere embedding models exclusively for vector generation
- **FR-012**: System MUST store embeddings in Qdrant Cloud (Free Tier)
- **FR-013**: System MUST manage metadata and sessions using Neon Serverless Postgres
- **FR-014**: System MUST provide an embedded chatbot interface within the Docusaurus frontend
- **FR-015**: System MUST load all credentials via environment variables, with no secrets in source code

### Key Entities *(include if feature involves data)*

- **Text Chunk**: Represents a segment of book content with source location and identifier
- **User Query**: A question posed by a user about the book content
- **Generated Response**: An answer produced by the system based on retrieved text chunks
- **Book Section**: A chapter or subsection of the technical book
- **Selected Text**: User-highlighted text that serves as exclusive context for a query

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: 100% of responses are grounded in retrieved or selected text with no hallucinations
- **SC-002**: Selected-text mode isolation is verified through automated tests with 95%+ accuracy
- **SC-003**: System operates with Cohere-only AI pipeline with zero OpenAI dependencies
- **SC-004**: No secrets are committed to the repository, with all credentials loaded from environment variables
- **SC-005**: The architecture is fully specifiable, plannable, and taskable via SpecifyKit workflows
- **SC-006**: Book-wide question answering achieves 90%+ accuracy in retrieving relevant text chunks
- **SC-007**: System responds to user queries within 5 seconds for 95% of requests
- **SC-008**: Prompt injection resistance prevents 99%+ of attempted safety constraint bypasses
