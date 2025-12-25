# AI Native Book

A comprehensive AI Native Book with Retrieval-Augmented Generation (RAG) capabilities.

## Tech Stack

- **Docusaurus** - Static site generator for documentation
- **React** - Component-based UI development
- **TypeScript** - Type-safe JavaScript development
- **OpenAI API** - AI-powered chatbot functionality
- **ChatKit UI** - Modern chat interface implementation

## Features

- Interactive AI assistant for book content with RAG capabilities
- Retrieval-Augmented Generation for accurate and context-aware responses
- Comprehensive coverage of AI Native concepts and implementations
- Modern chat interface with typing indicators
- Responsive design for desktop and mobile
- Clean, professional documentation layout

## Setup & Run Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ai-humanoid-book-rag
   ```

2. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm start
   ```

4. **Open your browser:**
   Visit `http://localhost:3000` to view the application

## Build for Production

```bash
cd frontend
npm run build
npm run serve
```

## Project Structure

- `frontend/` - Docusaurus documentation site with AI interface
- `frontend/src/` - Source code for components and pages
- `frontend/static/` - Static assets including images
- `docs/` - Documentation files
- `specs/` - Project specifications
- `rag/` - RAG system implementation
  - `rag/pipeline.py` - Main pipeline orchestrator
  - `rag/cli.py` - Command line interface
  - `rag/crawling/` - URL crawling and content extraction
  - `rag/processing/` - Text chunking and embedding generation
  - `rag/storage/` - Vector storage and search in Qdrant Cloud
  - `rag/config/` - Configuration management
  - `rag/utils/` - Utility functions
  - `rag/examples/` - Usage examples
  - `rag/tests/` - Unit tests
- `backend/` - FastAPI RAG chatbot backend
  - `backend/main.py` - FastAPI application entry point
  - `backend/api/` - API route definitions
  - `backend/models/` - Pydantic models
  - `backend/services/` - Business logic and external service integration
  - `backend/config/` - Configuration and settings
  - `backend/utils/` - Utility functions
- `data/` - Book content and research materials

## RAG Architecture

The Retrieval-Augmented Generation system combines:

- **Crawling Module**: For crawling Docusaurus book URLs and extracting clean text content
- **Processing Module**: For chunking text and generating embeddings using Cohere models
- **Vector Database**: For efficient storage and retrieval in Qdrant Cloud
- **Embedding Model**: To convert text to high-dimensional vectors using Cohere
- **Language Model**: To generate contextually relevant responses
- **Retrieval Module**: To fetch relevant information from the knowledge base through similarity search
- **Pipeline Orchestration**: To coordinate the complete workflow from URL ingestion to storage

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.