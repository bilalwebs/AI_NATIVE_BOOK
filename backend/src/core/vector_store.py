from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    Class to handle vector storage operations using Qdrant.
    """
    
    def __init__(self):
        # Initialize Qdrant client
        if settings.qdrant_url and settings.qdrant_api_key:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                prefer_grpc=True  # Use gRPC for better performance if available
            )
        else:
            # For development/testing without credentials
            self.client = QdrantClient(":memory:")  # In-memory storage for testing
        
        self.collection_name = "book_content"
        self._create_collection_if_not_exists()
    
    def _create_collection_if_not_exists(self):
        """Create the collection if it doesn't exist."""
        try:
            # Try to get collection info to see if it exists
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except:
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
            )
            logger.info(f"Created collection '{self.collection_name}'")
    
    def store_embedding(self, 
                       text_id: str, 
                       embedding: List[float], 
                       metadata: Dict[str, Any]) -> bool:
        """
        Store an embedding with its metadata in the vector store.
        
        Args:
            text_id: Unique identifier for the text
            embedding: The vector embedding
            metadata: Metadata associated with the text (source chapter, section, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            points = [PointStruct(
                id=text_id,
                vector=embedding,
                payload=metadata
            )]
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.debug(f"Stored embedding for text ID: {text_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing embedding for text ID {text_id}: {str(e)}")
            return False
    
    def search_similar(self, 
                      query_embedding: List[float], 
                      top_k: int = 5, 
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in the vector store.
        
        Args:
            query_embedding: The query embedding to search with
            top_k: Number of top similar results to return
            filters: Optional filters to apply to the search
            
        Returns:
            List of dictionaries containing similar content and metadata
        """
        try:
            # Convert filters to Qdrant's filter format if provided
            qdrant_filters = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                
                if filter_conditions:
                    qdrant_filters = models.Filter(must=filter_conditions)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
                filter=qdrant_filters
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.debug(f"Found {len(formatted_results)} similar results")
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching for similar embeddings: {str(e)}")
            return []
    
    def delete_by_id(self, text_id: str) -> bool:
        """
        Delete an embedding by its ID.
        
        Args:
            text_id: The ID of the text to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[text_id])
            )
            
            logger.debug(f"Deleted embedding for text ID: {text_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting embedding for text ID {text_id}: {str(e)}")
            return False
    
    def update_embedding(self, 
                        text_id: str, 
                        embedding: List[float], 
                        metadata: Dict[str, Any]) -> bool:
        """
        Update an existing embedding with new data.
        
        Args:
            text_id: The ID of the text to update
            embedding: The new vector embedding
            metadata: The new metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First delete the old point
            self.delete_by_id(text_id)
            
            # Then add the new one
            return self.store_embedding(text_id, embedding, metadata)
        except Exception as e:
            logger.error(f"Error updating embedding for text ID {text_id}: {str(e)}")
            return False


# Global instance for use throughout the application
vector_store = VectorStore()