from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
import cohere
import asyncio
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service class for Retrieval-Augmented Generation functionality.
    """
    def __init__(self):
        """
        Initialize the RAG service with Qdrant client and Cohere client.
        """
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME

        # Initialize Cohere client for embedding (to match the existing pipeline)
        self.cohere_client = cohere.Client(api_key=settings.COHERE_API_KEY) if settings.COHERE_API_KEY else None

    def search_similar_content(self, query: str, top_k: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search for similar content in the vector database.

        Args:
            query: Query string to search for
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List of similar content chunks with metadata
        """
        try:
            # Embed the query using Cohere
            if not self.cohere_client:
                raise ValueError("Cohere client not initialized")

            response = self.cohere_client.embed(
                texts=[query],
                model="embed-english-v3.0"  # Using the same model as the pipeline
            )
            query_embedding = response.embeddings[0]

            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold
            )

            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    'id': result.id,
                    'score': result.score,
                    'content': result.payload.get('content', ''),
                    'source_url': result.payload.get('source_url', ''),
                    'page_title': result.payload.get('page_title', ''),
                    'chunk_order': result.payload.get('chunk_order', 0),
                    'metadata': result.payload
                })

            logger.info(f"Found {len(formatted_results)} similar results for query: {query[:50]}...")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching for similar content: {str(e)}")
            raise

    def generate_response(self, query: str, context: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response using OpenRouter with the provided context.

        Args:
            query: User's query
            context: Retrieved context from vector store
            history: Chat history

        Returns:
            Generated response from the LLM
        """
        try:
            import openai

            # Set up OpenAI client with OpenRouter base URL
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY
            )

            # Prepare the prompt with context
            system_message = f"""
            You are a helpful assistant that answers questions based on the provided context.
            Use only the information in the context to answer the user's question.
            If the context doesn't contain enough information, say so.

            Context:
            {context}
            """

            # Prepare messages
            messages = [{"role": "system", "content": system_message}]

            # Add history if available
            if history:
                for msg in history:
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

            # Add current query
            messages.append({"role": "user", "content": query})

            # Call OpenRouter API through OpenAI-compatible interface
            response = client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def get_context_from_chunks(self, chunks: List[Dict[str, Any]], max_length: int = 2000) -> str:
        """
        Combine retrieved chunks into a context string, respecting max length.

        Args:
            chunks: List of retrieved chunks
            max_length: Maximum length of the context

        Returns:
            Combined context string
        """
        context_parts = []
        current_length = 0

        for chunk in chunks:
            chunk_text = chunk.get('content', '')
            chunk_length = len(chunk_text)

            if current_length + chunk_length > max_length:
                break

            context_parts.append(chunk_text)
            current_length += chunk_length

        return "\n\n".join(context_parts)


# Global instance
rag_service = RAGService()