---

description: "Task list for Integrated RAG Chatbot Embedded in Technical Book feature"
---

# Tasks: Integrated RAG Chatbot Embedded in Technical Book

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The feature specification requires validation checks for hallucination resistance and context isolation, so test tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`
- Paths follow the structure defined in plan.md with backend architecture

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with FastAPI, Cohere SDK, Qdrant client, Pydantic, SQLAlchemy dependencies in requirements.txt
- [X] T003 [P] Configure linting (ruff) and formatting tools (black) in pyproject.toml
- [X] T004 [P] Create .env.example with environment variables from specification
- [X] T005 [P] Create docker-compose.yml configuration file
- [X] T006 Create main.py application entry point based on project structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Setup database models and SQLAlchemy base in backend/src/models/__init__.py
- [X] T008 [P] Create configuration management from environment variables in backend/src/core/config.py
- [X] T009 [P] Setup security utilities and credential management in backend/src/core/security.py
- [X] T010 Create constants module in backend/src/core/constants.py
- [X] T011 [P] Setup dependency injection for API in backend/src/api/dependencies.py
- [X] T012 Configure error handling infrastructure in backend/src/api/exceptions.py
- [X] T013 [P] Create logging infrastructure in backend/src/core/logging.py
- [X] T014 Setup Qdrant vector store connection in backend/src/core/vector_store.py
- [X] T015 Setup Neon Postgres connection using SQLAlchemy in backend/src/core/database.py
- [X] T016 Create API routing structure in backend/src/api/__init__.py
- [X] T017 Create Cohere client configuration in backend/src/core/llm_client.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Book-wide Question Answering (Priority: P1) 🎯 MVP

**Goal**: Enable readers to ask questions and get answers based on content search across the entire book, with proper citations to source chapters/sections.

**Independent Test**: Can ask questions about book content and verify that responses are grounded in the book's text with proper citations.

### Tests for User Story 1 (OPTIONAL - based on requirement for validation) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US1] Contract test for chat endpoint in backend/tests/contract/test_context_isolation.py
- [ ] T019 [P] [US1] Integration test for book-wide question answering in backend/tests/integration/test_api_chat.py

### Implementation for User Story 1

- [X] T020 [P] [US1] Create BookTextSegment model in backend/src/models/text_segment.py
- [X] T021 [P] [US1] Create BookSection model in backend/src/models/book_section.py
- [X] T022 [P] [US1] Create ConversationSession model in backend/src/models/conversation_session.py
- [X] T023 [US1] Implement chunking service with sentence-aware logic in backend/src/services/chunking_service.py
- [X] T024 [US1] Implement embedding service using Cohere in backend/src/services/embedding_service.py
- [X] T025 [US1] Implement retrieval service for vector search in backend/src/services/retrieval_service.py
- [X] T026 [US1] Implement validation service with hallucination checks in backend/src/services/validation_service.py
- [X] T027 [US1] Implement generation service with Cohere-based answer generation in backend/src/services/generation_service.py
- [X] T028 [US1] Implement chat endpoint with book-wide mode in backend/src/api/v1/chat.py
- [X] T029 [US1] Implement ingestion endpoint in backend/src/api/v1/ingestion.py
- [X] T030 [US1] Add health check endpoint in backend/src/api/v1/health.py
- [X] T031 [US1] Configure API routing for v1 in backend/src/api/v1/__init__.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Selected-Text Question Answering (Priority: P2)

**Goal**: Allow users to select specific text in the book and ask questions that are answered only using that selected text as context, without accessing broader book content.

**Independent Test**: Can select text and ask questions about that text, verifying responses are based only on the selected content.

### Tests for User Story 2 (OPTIONAL - based on requirement for validation) ⚠️

- [ ] T032 [P] [US2] Contract test for selected-text mode endpoint in backend/tests/contract/test_context_isolation.py
- [ ] T033 [P] [US2] Integration test for selected-text question answering in backend/tests/integration/test_api_chat.py

### Implementation for User Story 2

- [X] T034 [P] [US2] Enhance ConversationSession model to track mode in backend/src/models/conversation_session.py
- [X] T035 [US2] Update retrieval service to bypass vector search in selected-text mode in backend/src/services/retrieval_service.py
- [X] T036 [US2] Update validation service to enforce context isolation in backend/src/services/validation_service.py
- [X] T037 [US2] Enhance generation service for selected-text context in backend/src/services/generation_service.py
- [X] T038 [US2] Enhance chat endpoint with selected-text mode in backend/src/api/v1/chat.py
- [X] T039 [US2] Implement strict context isolation validation in backend/tests/unit/test_validation.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Context-aware Chatbot Interaction (Priority: P3)

**Goal**: Enable the chatbot to maintain awareness of the user's current reading position in the book and provide more contextually relevant responses based on their location.

**Independent Test**: Can navigate to different sections and verify that the chatbot is aware of the current context and can provide location-relevant responses.

### Tests for User Story 3 (OPTIONAL - based on requirement for validation) ⚠️

- [ ] T040 [P] [US3] Contract test for context-aware features in backend/tests/contract/test_context_isolation.py
- [ ] T041 [P] [US3] Integration test for context-aware interaction in backend/tests/integration/test_api_chat.py

### Implementation for User Story 3

- [ ] T042 [P] [US3] Enhance BookSection model with navigation tracking in backend/src/models/book_section.py
- [ ] T043 [US3] Update ConversationSession model to track reading position in backend/src/models/conversation_session.py
- [ ] T044 [US3] Enhance retrieval service with positional context awareness in backend/src/services/retrieval_service.py
- [ ] T045 [US3] Update generation service to include related section suggestions in backend/src/services/generation_service.py
- [ ] T046 [US3] Enhance chat endpoint with context-aware features in backend/src/api/v1/chat.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Documentation updates in backend/docs/
- [ ] T048 Code cleanup and refactoring across all components
- [ ] T049 Performance optimization for retrieval and generation services
- [ ] T050 [P] Additional unit tests for all services in backend/tests/unit/
- [ ] T051 Security hardening for prompt injection resistance
- [ ] T052 Run quickstart.md validation to ensure setup works as expected
- [ ] T053 Add comprehensive API documentation using FastAPI's auto-generation
- [ ] T054 Create deployment configuration files
- [ ] T055 Add monitoring and observability features
- [ ] T056 Final integration tests covering all user stories together

---

## Dependencies & Execution Order

### Phase Dependencies

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with FastAPI, Cohere SDK, Qdrant client, Pydantic, SQLAlchemy dependencies in requirements.txt
- [X] T003 [P] Configure linting (ruff) and formatting tools (black) in pyproject.toml
- [X] T004 [P] Create .env.example with environment variables from specification
- [X] T005 [P] Create docker-compose.yml configuration file
- [X] T006 Create main.py application entry point based on project structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Setup database models and SQLAlchemy base in backend/src/models/__init__.py
- [X] T008 [P] Create configuration management from environment variables in backend/src/core/config.py
- [X] T009 [P] Setup security utilities and credential management in backend/src/core/security.py
- [X] T010 Create constants module in backend/src/core/constants.py
- [X] T011 [P] Setup dependency injection for API in backend/src/api/dependencies.py
- [X] T012 Configure error handling infrastructure in backend/src/api/exceptions.py
- [X] T013 [P] Create logging infrastructure in backend/src/core/logging.py
- [X] T014 Setup Qdrant vector store connection in backend/src/core/vector_store.py
- [X] T015 Setup Neon Postgres connection using SQLAlchemy in backend/src/core/database.py
- [X] T016 Create API routing structure in backend/src/api/__init__.py
- [X] T017 Create Cohere client configuration in backend/src/core/llm_client.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Book-wide Question Answering (Priority: P1) 🎯 MVP

**Goal**: Enable readers to ask questions and get answers based on content search across the entire book, with proper citations to source chapters/sections.

**Independent Test**: Can ask questions about book content and verify that responses are grounded in the book's text with proper citations.

### Tests for User Story 1 (OPTIONAL - based on requirement for validation) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US1] Contract test for chat endpoint in backend/tests/contract/test_context_isolation.py
- [ ] T019 [P] [US1] Integration test for book-wide question answering in backend/tests/integration/test_api_chat.py

### Implementation for User Story 1

- [X] T020 [P] [US1] Create BookTextSegment model in backend/src/models/text_segment.py
- [X] T021 [P] [US1] Create BookSection model in backend/src/models/book_section.py
- [X] T022 [P] [US1] Create ConversationSession model in backend/src/models/conversation_session.py
- [X] T023 [US1] Implement chunking service with sentence-aware logic in backend/src/services/chunking_service.py
- [X] T024 [US1] Implement embedding service using Cohere in backend/src/services/embedding_service.py
- [X] T025 [US1] Implement retrieval service for vector search in backend/src/services/retrieval_service.py
- [X] T026 [US1] Implement validation service with hallucination checks in backend/src/services/validation_service.py
- [X] T027 [US1] Implement generation service with Cohere-based answer generation in backend/src/services/generation_service.py
- [X] T028 [US1] Implement chat endpoint with book-wide mode in backend/src/api/v1/chat.py
- [X] T029 [US1] Implement ingestion endpoint in backend/src/api/v1/ingestion.py
- [X] T030 [US1] Add health check endpoint in backend/src/api/v1/health.py
- [X] T031 [US1] Configure API routing for v1 in backend/src/api/v1/__init__.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Selected-Text Question Answering (Priority: P2)

**Goal**: Allow users to select specific text in the book and ask questions that are answered only using that selected text as context, without accessing broader book content.

**Independent Test**: Can select text and ask questions about that text, verifying responses are based only on the selected content.

### Tests for User Story 2 (OPTIONAL - based on requirement for validation) ⚠️

- [ ] T032 [P] [US2] Contract test for selected-text mode endpoint in backend/tests/contract/test_context_isolation.py
- [ ] T033 [P] [US2] Integration test for selected-text question answering in backend/tests/integration/test_api_chat.py

### Implementation for User Story 2

- [X] T034 [P] [US2] Enhance ConversationSession model to track mode in backend/src/models/conversation_session.py
- [X] T035 [US2] Update retrieval service to bypass vector search in selected-text mode in backend/src/services/retrieval_service.py
- [X] T036 [US2] Update validation service to enforce context isolation in backend/src/services/validation_service.py
- [X] T037 [US2] Enhance generation service for selected-text context in backend/src/services/generation_service.py
- [X] T038 [US2] Enhance chat endpoint with selected-text mode in backend/src/api/v1/chat.py
- [X] T039 [US2] Implement strict context isolation validation in backend/tests/unit/test_validation.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Context-aware Chatbot Interaction (Priority: P3)

**Goal**: Enable the chatbot to maintain awareness of the user's current reading position in the book and provide more contextually relevant responses based on their location.

**Independent Test**: Can navigate to different sections and verify that the chatbot is aware of the current context and can provide location-relevant responses.

### Tests for User Story 3 (OPTIONAL - based on requirement for validation) ⚠️

- [ ] T040 [P] [US3] Contract test for context-aware features in backend/tests/contract/test_context_isolation.py
- [ ] T041 [P] [US3] Integration test for context-aware interaction in backend/tests/integration/test_api_chat.py

### Implementation for User Story 3

- [ ] T042 [P] [US3] Enhance BookSection model with navigation tracking in backend/src/models/book_section.py
- [ ] T043 [US3] Update ConversationSession model to track reading position in backend/src/models/conversation_session.py
- [ ] T044 [US3] Enhance retrieval service with positional context awareness in backend/src/services/retrieval_service.py
- [ ] T045 [US3] Update generation service to include related section suggestions in backend/src/services/generation_service.py
- [ ] T046 [US3] Enhance chat endpoint with context-aware features in backend/src/api/v1/chat.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Documentation updates in backend/docs/
- [ ] T048 Code cleanup and refactoring across all components
- [ ] T049 Performance optimization for retrieval and generation services
- [ ] T050 [P] Additional unit tests for all services in backend/tests/unit/
- [ ] T051 Security hardening for prompt injection resistance
- [ ] T052 Run quickstart.md validation to ensure setup works as expected
- [ ] T053 Add comprehensive API documentation using FastAPI's auto-generation
- [ ] T054 Create deployment configuration files
- [ ] T055 Add monitoring and observability features
- [ ] T056 Final integration tests covering all user stories together

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for chat endpoint in backend/tests/contract/test_context_isolation.py"
Task: "Integration test for book-wide question answering in backend/tests/integration/test_api_chat.py"

# Launch all models for User Story 1 together:
Task: "Create BookTextSegment model in backend/src/models/text_segment.py"
Task: "Create BookSection model in backend/src/models/book_section.py"
Task: "Create ConversationSession model in backend/src/models/conversation_session.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence