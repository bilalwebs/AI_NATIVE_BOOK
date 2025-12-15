from typing import List, Dict, Any
from src.core.llm_client import llm_client
from src.core.logging import get_logger
from src.core.exceptions import RAGException

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using Cohere's embedding models.
    """
    
    def __init__(self):
        self.model_name = "embed-english-v3.0"  # Default model as configured in llm_client
        self.batch_size = 96  # Cohere's recommended batch size for embeddings
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a single embedding for the given text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            A list of floats representing the embedding vector
        """
        try:
            logger.debug(f"Generating embedding for text of length {len(text)}")
            embedding = llm_client.generate_embedding(text)
            
            if not embedding or len(embedding) == 0:
                raise RAGException(
                    "EMBEDDING_ERROR", 
                    f"Failed to generate embedding for text: {text[:50]}..."
                )
            
            logger.debug(f"Successfully generated embedding of dimension {len(embedding)}")
            return embedding
        except RAGException:
            # Re-raise RAG exceptions as they're already properly formatted
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_embedding: {str(e)}")
            raise RAGException("EMBEDDING_ERROR", f"Failed to generate embedding: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: A list of texts to generate embeddings for
            
        Returns:
            A list of embedding vectors, one for each input text
        """
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts in batches of {self.batch_size}")
            
            # Process in batches to respect API limits
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                logger.debug(f"Processing batch {i//self.batch_size + 1}/{(len(texts) - 1)//self.batch_size + 1}")
                
                batch_embeddings = llm_client.generate_embeddings_batch(batch)
                all_embeddings.extend(batch_embeddings)
            
            # Validate that we have the right number of embeddings
            if len(all_embeddings) != len(texts):
                raise RAGException(
                    "EMBEDDING_ERROR", 
                    f"Mismatch in embedding count: expected {len(texts)}, got {len(all_embeddings)}"
                )
            
            # Validate that all embeddings are properly formed
            for i, embedding in enumerate(all_embeddings):
                if not embedding or len(embedding) == 0:
                    raise RAGException(
                        "EMBEDDING_ERROR", 
                        f"Empty embedding at index {i} for text: {texts[i][:50]}..."
                    )
            
            logger.info(f"Successfully generated embeddings for {len(texts)} texts")
            return all_embeddings
        except RAGException:
            # Re-raise RAG exceptions as they're already properly formatted
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_embeddings_batch: {str(e)}")
            raise RAGException("EMBEDDING_ERROR", f"Failed to generate embeddings batch: {str(e)}")
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embedding vectors.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity value between -1 and 1
        """
        # Compute dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Compute magnitudes
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        # Handle zero magnitude case
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Compute cosine similarity
        cosine_similarity = dot_product / (magnitude1 * magnitude2)
        return cosine_similarity


# Global instance for use throughout the application
embedding_service = EmbeddingService()