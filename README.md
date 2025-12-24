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
- `data/` - Book content and research materials

## RAG Architecture

The Retrieval-Augmented Generation system combines:

- **Vector Database**: For efficient storage and retrieval of book content
- **Embedding Model**: To convert text to high-dimensional vectors
- **Language Model**: To generate contextually relevant responses
- **Retrieval Module**: To fetch relevant information from the knowledge base

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.