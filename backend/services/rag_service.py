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
        try:
            self.cohere_client = cohere.Client(api_key=settings.COHERE_API_KEY) if settings.COHERE_API_KEY else None
        except Exception as e:
            logger.error(f"Failed to initialize Cohere client: {str(e)}")
            self.cohere_client = None

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
        # Check if Cohere client is properly initialized
        if not self.cohere_client:
            logger.error("Cohere client not initialized")
            raise ValueError("Cohere client not initialized. Please check API key and server configuration.")

        try:
            # Embed the query using Cohere
            response = self.cohere_client.embed(
                texts=[query],
                model=settings.RAG_EMBEDDING_MODEL,  # Using the configured embedding model
                input_type="search_query"  # Required parameter for Cohere API
            )
            query_embedding = response.embeddings[0]

            # Search in Qdrant using query_points method
            search_results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                score_threshold=score_threshold
            ).points

            # Format results with book content validation
            formatted_results = []
            for result in search_results:
                source_url = result.payload.get('source_url', '')

                # Validate that the content is from the book domain
                book_domain = settings.BOOK_START_URL.split("//")[1].split("/")[0]  # Extract domain from URL
                if book_domain in source_url or source_url.startswith(settings.BOOK_START_URL):
                    formatted_results.append({
                        'id': result.id,
                        'score': result.score,
                        'content': result.payload.get('content', ''),
                        'source_url': result.payload.get('source_url', ''),
                        'page_title': result.payload.get('page_title', ''),
                        'chunk_order': result.payload.get('chunk_order', 0),
                        'metadata': result.payload
                    })
                else:
                    logger.warning(f"Filtered out non-book content from URL: {source_url}")

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

            import httpx
            # Set up OpenAI client with OpenRouter base URL, avoiding proxy issues
            timeout = httpx.Timeout(timeout=60.0, connect=10.0)
            http_client = httpx.Client(timeout=timeout)
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                http_client=http_client
            )

            # Check if context is empty or has no relevant content
            if not context.strip():
                return "This information is not available in the book content."

            # Prepare the prompt with context and strict book-only instructions
            system_message = f"""
            You are a knowledgeable assistant that answers questions based ONLY on the provided book content.
            You must follow these rules strictly:
            1. Answer only using information from the provided context
            2. If the context doesn't contain relevant information, explicitly state that the answer is not in the book
            3. Never make up information or provide external knowledge
            4. Always cite the book content as your source
            5. Reference specific parts of the book content when possible
            6. If asked about topics not covered in the book context, say: "This information is not available in the book content."

            Book Content Context:
            {context}

            Remember: You are a book content expert. Only provide answers based on the book content above.
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

            # Validate that the response is based on the provided context
            generated_response = response.choices[0].message.content
            validated_response = self.validate_response_based_on_context(generated_response, context)
            return validated_response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def validate_response_based_on_context(self, response: str, context: str) -> str:
        """
        Validate that the response is based on the provided context and not external knowledge.

        Args:
            response: The generated response from the LLM
            context: The context provided to the LLM

        Returns:
            Validated response or modified response that adheres to context-only rules
        """
        # Check if the response contains phrases indicating lack of information in context
        if "not covered in the provided book content" in response.lower() or \
           "not in the book" in response.lower() or \
           "cannot answer" in response.lower() or \
           "no information" in response.lower() or \
           "not mentioned" in response.lower():
            # Return the exact required message
            if "not available in the book content" in response.lower():
                return response  # Already has the exact message
            else:
                return "This information is not available in the book content."

        # In a more sophisticated implementation, we could add additional validation
        # to ensure the response is factually consistent with the context
        # For now, we rely on the system prompt to enforce book-only responses
        return response

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