import cohere
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import RAGException

logger = get_logger(__name__)


class LLMClient:
    """
    Client for interacting with Cohere's language model and embedding services.
    """
    
    def __init__(self):
        if not settings.cohere_api_key:
            raise ValueError("Cohere API key is required but not provided in settings")
        
        self.client = cohere.Client(api_key=settings.cohere_api_key)
        self.embed_model = "embed-english-v3.0"  # Default embedding model
        self.generate_model = "command-r-plus"  # Default generation model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text using Cohere.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            A list of floats representing the embedding vector
        """
        try:
            response = self.client.embed(
                texts=[text],
                model=self.embed_model,
                input_type="search_document"  # Using search_document as it's optimized for document retrieval
            )
            
            if response.embeddings and len(response.embeddings) > 0:
                embedding = response.embeddings[0]
                logger.debug(f"Generated embedding for text of length {len(text)}")
                return embedding
            else:
                logger.error("No embeddings returned from Cohere API")
                raise RAGException("EMBEDDING_ERROR", "No embeddings returned from API")
                
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise RAGException("EMBEDDING_ERROR", f"Failed to generate embedding: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: A list of texts to generate embeddings for
            
        Returns:
            A list of embedding vectors
        """
        try:
            # Cohere has limits on batch size, usually around 96 texts per request
            batch_size = min(96, len(texts))
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self.client.embed(
                    texts=batch,
                    model=self.embed_model,
                    input_type="search_document"
                )
                
                if response.embeddings:
                    all_embeddings.extend(response.embeddings)
                else:
                    logger.error(f"No embeddings returned from Cohere API for batch {i//batch_size + 1}")
                    # Add empty embeddings for the failed batch to maintain order
                    all_embeddings.extend([[]] * len(batch))
            
            logger.debug(f"Generated embeddings for {len(texts)} texts in {len(range(0, len(texts), batch_size))} batch(es)")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {str(e)}")
            raise RAGException("EMBEDDING_ERROR", f"Failed to generate embeddings batch: {str(e)}")
    
    def generate_text(self, 
                     prompt: str, 
                     context: Optional[str] = None, 
                     max_tokens: Optional[int] = 300,
                     temperature: Optional[float] = 0.3) -> str:
        """
        Generate text using Cohere's language model.
        
        Args:
            prompt: The prompt to send to the model
            context: Additional context to include in the generation
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness in generation (0.0 to 1.0)
            
        Returns:
            Generated text
        """
        try:
            # Construct the full prompt with context if provided
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
            
            response = self.client.generate(
                model=self.generate_model,
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                # Ensure the response only contains information from the provided context
                stop_sequences=["Question:", "Context:"],
                return_likelihoods="NONE"
            )
            
            if response.generations and len(response.generations) > 0:
                generated_text = response.generations[0].text.strip()
                logger.debug(f"Generated text of length {len(generated_text)} for prompt")
                return generated_text
            else:
                logger.error("No generations returned from Cohere API")
                raise RAGException("GENERATION_ERROR", "No text generated by API")
                
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise RAGException("GENERATION_ERROR", f"Failed to generate text: {str(e)}")


# Global instance for use throughout the application
llm_client = LLMClient()