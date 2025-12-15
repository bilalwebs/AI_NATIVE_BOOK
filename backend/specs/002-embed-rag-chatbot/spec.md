# Feature Specification: Integrated RAG Chatbot Embedded in Technical Book

**Feature Branch**: `002-embed-rag-chatbot`
**Created**: 2025-01-15
**Status**: Draft
**Input**: User description: "Project: Integrated RAG Chatbot Embedded in a Published Technical Book Objective: Specify a Retrieval-Augmented Generation (RAG) chatbot that is embedded inside a published book and answers user questions strictly from book content or explicitly selected text. Target Audience: - Readers of a technical AI / Robotics book - Students and developers seeking accurate, grounded explanations - Users requiring source-bound answers while reading Core Functional Scope: 1. Book-wide Question Answering - Questions answered only after vector-based retrieval - Retrieved chunks act as the sole context for generation 2. Selected-Text Question Answering - User-selected text is the ONLY allowed context - Vector search and global context are disabled - No inference beyond selected text permitted 3. Embedded UX - Chatbot is embedded within the book frontend (Docusaurus) - Context-aware interaction tied to reading position Technology Stack (Mandatory): - Backend: FastAPI (Python) - Vector Store: Qdrant Cloud (Free Tier) - Metadata / Sessions: Neon Serverless Postgres - LLM Provider: Cohere - Embeddings: Cohere Embedding Models - Spec & Task Execution: Qwen CLI - Frontend: Docusaurus Credential Management: - All credentials must be loaded via environment variables - No secrets are allowed in source code or prompts Required Environment Variables: - QDRANT_API_KEY - QDRANT_URL - QDRANT_CLUSTER_ID - NEON_DATABASE_URL - COHERE_API_KEY RAG System Requirements: - Deterministic text chunking with stable chunk IDs - Each chunk must include: - Source chapter/section - Chunk identifier - Text content - Retrieval is mandatory before generation - Generation without context is forbidden Selected-Text Mode Constraints: - Context = user-selected text only - No retrieval calls allowed - No previous conversation memory allowed - If insufficient context, respond: "The answer is not available in the selected text." Quality & Safety Constraints: - Zero hallucinations - No external or general AI knowledge - No OpenAI APIs, SDKs, or keys (explicitly forbidden) - Prompt injection resistance required Success Criteria: - 100% responses grounded in retrieved or selected text - Cohere-only AI pipeline - Selected-text isolation verified via tests - No secrets committed to repository - System is fully specifiable, plannable, and taskable via SpecifyKit Not Building: - General-purpose AI assistant - Web search or external retrieval - Creative or speculative responses - Vendor comparisons - OpenAI-based tooling"

## Assumptions

- The book content is available in digital format for text processing
- Users have access to an online version of the book where the chatbot is embedded
- The book content is properly structured with chapters and sections for accurate referencing

## Dependencies

- Access to the complete book content in a structured digital format
- Integration capability with the book's frontend system
- Reliable internet connection for real-time processing

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Book-wide Question Answering (Priority: P1)

A reader of the technical AI/Robotics book is reading a chapter and has a question about a concept. They type their question into the embedded chatbot, which searches the entire book's content and provides an answer based solely on information available in the book. The answer includes a reference to the specific chapter/section where the information was found.

**Why this priority**: This is the foundational functionality that provides value to readers by enabling them to get immediate answers to their questions directly from the book content, enhancing the learning experience.

**Independent Test**: Can be fully tested by asking questions about book content and verifying that responses are grounded in the book's text with proper citations.

**Acceptance Scenarios**:

1. **Given** a user is reading the technical book with the embedded chatbot, **When** they ask a question related to content in the book, **Then** the system performs content search across the book and generates an answer based solely on that found information.

2. **Given** a user asks a question that requires information from multiple sections of the book, **When** the system processes the query, **Then** it retrieves relevant information from different parts of the book and synthesizes an answer based only on that content.

3. **Given** a user asks a question that is not answerable from the book content, **When** the system processes the query, **Then** it responds with "I cannot answer that question as it's not covered in the book content."

---

### User Story 2 - Selected-Text Question Answering (Priority: P2)

A student reading the book highlights specific text and wants clarification only about that selected content. They use the chatbot's selected-text mode to ask questions, and the system only uses the highlighted text as context for generating answers, without performing content search or accessing the broader book content.

**Why this priority**: This mode ensures users can get focused explanations about specific passages they're struggling with, without the system pulling in unrelated information from elsewhere in the book.

**Independent Test**: Can be fully tested by selecting text and asking questions about that text, verifying responses are based only on the selected content.

**Acceptance Scenarios**:

1. **Given** a user has selected text within the book, **When** they ask a question in selected-text mode, **Then** the system responds based only on the selected text without performing content search or accessing other book content.

2. **Given** a user has selected text that doesn't contain sufficient information to answer their question, **When** they ask a question in selected-text mode, **Then** the system responds with "The answer is not available in the selected text."

3. **Given** a user has asked a question in selected-text mode, **When** they switch to book-wide mode, **Then** the system now performs content search across the entire book content.

---

### User Story 3 - Context-aware Chatbot Interaction (Priority: P3)

A developer reading the book navigates to different chapters and sections. The embedded chatbot maintains awareness of their current reading position and can relate answers to the context of where they are in the book, providing more relevant responses.

**Why this priority**: This enhances the user experience by making the chatbot more contextual and aware of the user's reading journey, potentially suggesting related content based on their current location in the book.

**Independent Test**: Can be fully tested by navigating to different sections and verifying that the chatbot is aware of the current context and can provide location-relevant responses.

**Acceptance Scenarios**:

1. **Given** a user is reading a specific chapter on a technical topic, **When** they ask a general question, **Then** the system can provide answers that reference the current context or suggest related sections in the book.

2. **Given** a user has been reading a sequence of related sections, **When** they ask a follow-up question, **Then** the system can use the reading context to provide more appropriate answers (when in book-wide mode).

---

### Edge Cases

- What happens when content searching is temporarily unavailable during a book-wide question?
- How does the system handle extremely long user-selected text that exceeds processing limits?
- What happens when a user asks a question that appears in multiple places in the book with slightly different contexts?
- How does the system handle malformed or potentially malicious queries designed to bypass safety constraints?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST perform content search from book content before any text generation in book-wide mode
- **FR-002**: System MUST only use user-selected text as context when in selected-text mode, with no content search or access to other book content
- **FR-003**: System MUST respond with "The answer is not available in the selected text." when selected-text context is insufficient to answer a question
- **FR-004**: System MUST maintain consistent text identification for reliable content search
- **FR-005**: Each text segment MUST include source chapter/section information, identifier, and text content
- **FR-006**: System MUST ensure 100% of responses are grounded in either retrieved book content or selected text only
- **FR-007**: System MUST implement zero hallucinations and use no external or general knowledge
- **FR-008**: System MUST resist prompt injection attempts and maintain safety constraints
- **FR-009**: System MUST store conversation sessions securely
- **FR-010**: System MUST securely manage all access credentials
- **FR-011**: System MUST be embedded within the book frontend
- **FR-012**: System MUST maintain awareness of user's current reading position in the book
- **FR-013**: System MUST use the designated AI provider for all language processing

### Key Entities

- **BookTextSegment**: Represents a segment of the book content with stable ID, source chapter/section reference, and the text content itself
- **ConversationSession**: Contains a series of user interactions with the chatbot, stored securely with user context
- **BookSection**: Represents a chapter or section of the book with metadata about its content and location in the book structure

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of chatbot responses are grounded in retrieved or selected book text with no hallucinations
- **SC-002**: Selected-text mode responses are 100% isolated from broader book context and content search
- **SC-003**: Book-wide responses are generated only after successful content search from book content
- **SC-004**: All system credentials are securely managed with zero exposure in source code
- **SC-005**: All tests verify selected-text isolation functionality works as expected
