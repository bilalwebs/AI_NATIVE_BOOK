import cohere
from typing import List, Dict, Any, Optional
import logging
from rag.data_models import EmbeddingVector
import uuid
from rag.utils.retry_utils import retry_on_exception
from rag.config import Config


class CohereEmbeddingClient:
    """
    Cohere API client wrapper for embedding generation.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        logger: logging.Logger = None
    ):
        """
        Initialize the Cohere embedding client.

        Args:
            api_key: Cohere API key (defaults to using Config.COHERE_API_KEY)
            model: Cohere model to use (defaults to using Config.COHERE_MODEL)
            logger: Logger instance for logging
        """
        self.api_key = api_key or Config.COHERE_API_KEY
        self.model = model or Config.COHERE_MODEL
        self.logger = logger or logging.getLogger(__name__)

        if not self.api_key:
            raise ValueError("Cohere API key is required")

        self.client = cohere.Client(self.api_key)

    @retry_on_exception(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
        backoff_factor=2.0,
        exceptions=(Exception,),
        logger=None  # We'll handle logging ourselves
    )
    def _make_embedding_request(self, texts: List[str]) -> List[List[float]]:
        """
        Make a request to Cohere's embedding API with retry logic.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type="search_document"  # Appropriate for document search
            )

            if hasattr(response, 'embeddings') and response.embeddings:
                return response.embeddings
            else:
                raise Exception(f"Unexpected response format from Cohere API: {response}")

        except cohere.CohereAPIError as e:
            if self.logger:
                self.logger.error(f"Cohere API error: {str(e)}")
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def embed_texts_with_error_handling(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with comprehensive error handling.

        Args:
            texts: List of texts to embed
            batch_size: Maximum number of texts to process in one request (default from config)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        batch_size = batch_size or Config.BATCH_SIZE
        all_embeddings = []

        # Process in batches to respect API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                batch_embeddings = self._make_embedding_request(batch)
                all_embeddings.extend(batch_embeddings)

                if self.logger:
                    self.logger.info(f"Generated embeddings for batch {i//batch_size + 1}: {len(batch)} texts")

            except cohere.CohereAPIError as e:
                if self.logger:
                    self.logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1} due to Cohere API error: {str(e)}")

                # Depending on the error type, we might want to handle differently
                # For rate limit errors, we might want to slow down
                if "rate limit" in str(e).lower():
                    import time
                    time.sleep(5)  # Wait before retrying

                raise
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1}: {str(e)}")

                # Re-raise the exception to maintain the retry behavior
                raise

        return all_embeddings

    def embed_texts(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed
            batch_size: Maximum number of texts to process in one request (default from config)

        Returns:
            List of embedding vectors
        """
        # Use the error handling version
        return self.embed_texts_with_error_handling(texts, batch_size)

    def embed_single_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []

    def embed_document_chunks(
        self,
        chunks: List['DocumentChunk'],  # Forward reference as string
        batch_size: Optional[int] = None
    ) -> List[EmbeddingVector]:
        """
        Generate embeddings for a list of DocumentChunk objects.

        Args:
            chunks: List of DocumentChunk objects to embed
            batch_size: Maximum number of chunks to process in one request

        Returns:
            List of EmbeddingVector objects
        """
        if not chunks:
            return []

        # Extract text content from chunks
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings
        embeddings = self.embed_texts(texts, batch_size)

        # Create EmbeddingVector objects
        embedding_vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_vector = EmbeddingVector(
                embedding_id=f"emb_{chunk.chunk_id}_{uuid.uuid4().hex[:8]}",
                chunk_id=chunk.chunk_id,
                vector=embedding,
                model=self.model
            )
            embedding_vectors.append(embedding_vector)

        return embedding_vectors

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current embedding model.

        Returns:
            Dictionary with model information
        """
        # Note: Cohere API doesn't have a direct method to get model info
        # This is a placeholder that returns configured model info
        return {
            'model': self.model,
            'api_key_set': bool(self.api_key),
            'expected_vector_size': self._get_expected_vector_size()
        }

    def _get_expected_vector_size(self) -> Optional[int]:
        """
        Get the expected vector size for the current model.
        This is a simplified approach - in practice, you'd need to check Cohere's documentation
        or make a test call to determine the vector size.

        Returns:
            Expected vector size or None if unknown
        """
        # Common Cohere model vector sizes
        model_sizes = {
            'embed-english-v3.0': 1024,
            'embed-multilingual-v3.0': 1024,
            'embed-english-v2.0': 4096,
            'embed-multilingual-v2.0': 768
        }

        return model_sizes.get(self.model)

    def validate_api_key(self) -> bool:
        """
        Validate that the API key is working by making a simple request.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Test with a simple embedding request
            test_embedding = self.embed_single_text("test")
            return len(test_embedding) > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"API key validation failed: {str(e)}")
            return False

    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get usage information for the Cohere API.
        Note: This is a placeholder as the Cohere API doesn't directly provide usage info through the client.

        Returns:
            Dictionary with usage information
        """
        return {
            'model': self.model,
            'api_endpoint': 'https://api.cohere.ai/v1/embed',
            'note': 'Actual usage info needs to be obtained from Cohere dashboard'
        }