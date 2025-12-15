# Data Model: Integrated RAG Chatbot Embedded in Technical Book

## Entity: BookTextSegment

Represents a segment of the book content with stable ID, source chapter/section reference, and the text content itself.

### Fields:
- `id` (String): Stable, unique identifier for the text segment
- `content` (String): The actual text content of the segment
- `source_chapter` (String): The chapter where this segment originates
- `source_section` (String): The specific section within the chapter
- `chunk_order` (Integer): Sequential order of this chunk within its section
- `vector_id` (String): Reference to the corresponding vector in Qdrant
- `created_at` (DateTime): Timestamp when the segment was created
- `updated_at` (DateTime): Timestamp of last update

### Validation Rules:
- Content must not exceed 400 tokens
- Source chapter and section must be valid book references
- ID must be unique across all segments

## Entity: ConversationSession

Contains a series of user interactions with the chatbot, stored securely with user context.

### Fields:
- `session_id` (String): Unique identifier for the conversation session
- `user_id` (String): Identifier for the user (if available)
- `mode` (String): Either "book-wide" or "selected-text" indicating the session mode
- `created_at` (DateTime): Timestamp when the session was created
- `updated_at` (DateTime): Timestamp of last activity
- `expires_at` (DateTime): Expiration timestamp for session cleanup
- `messages` (Array): List of message objects (user queries and system responses)

### Message Object Structure:
- `message_id` (String): Unique identifier for the message
- `role` (String): Either "user" or "assistant"
- `content` (String): The text content of the message
- `timestamp` (DateTime): When the message was created
- `context_sources` (Array): References to source segments used for responses (empty for user messages)

### Validation Rules:
- Mode must be either "book-wide" or "selected-text"
- Messages must be in chronological order
- Session must expire after 24 hours of inactivity

## Entity: BookSection

Represents a chapter or section of the book with metadata about its content and location in the book structure.

### Fields:
- `section_id` (String): Unique identifier for the section
- `title` (String): Title of the section/chapter
- `book_id` (String): Identifier for the book this section belongs to
- `parent_section_id` (String, Optional): Reference to parent section if hierarchical
- `section_level` (Integer): Hierarchical level (e.g., 1 for chapter, 2 for subsection)
- `start_page` (Integer): Starting page number of the section
- `end_page` (Integer): Ending page number of the section
- `word_count` (Integer): Total word count in the section
- `segment_count` (Integer): Number of text segments created from this section

### Validation Rules:
- Section level must be between 1 and 5
- Start page must be less than end page
- Title must not be empty

## Relationships:

1. BookSection (1) -> BookTextSegment (Many)
   - One book section contains many text segments
   
2. ConversationSession (1) -> Messages (Many)
   - One conversation session contains many messages
   
3. Message (Many) -> BookTextSegment (Many) [via context_sources]
   - One message can reference many text segments as context sources