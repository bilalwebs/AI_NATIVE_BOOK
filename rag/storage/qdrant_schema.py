from typing import Dict, Any, Optional
from qdrant_client.http import models
import logging


class QdrantSchema:
    """
    Class to define and manage Qdrant collection schemas for book embeddings.
    """
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def get_default_collection_config(
        self,
        vector_size: int,
        distance: str = "Cosine",
        hnsw_config: Optional[Dict[str, Any]] = None,
        optimizers_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get default configuration for a Qdrant collection.

        Args:
            vector_size: Size of the embedding vectors
            distance: Distance metric for similarity search (Cosine, Euclid, Dot)
            hnsw_config: Configuration for HNSW index
            optimizers_config: Configuration for collection optimizers

        Returns:
            Dictionary with collection configuration
        """
        config = {
            "vectors": {
                "size": vector_size,
                "distance": distance.upper()
            }
        }

        if hnsw_config:
            config["hnsw_config"] = hnsw_config

        if optimizers_config:
            config["optimizers_config"] = optimizers_config

        return config

    def get_book_embeddings_payload_schema(self) -> Dict[str, Any]:
        """
        Get the payload schema for book embeddings.

        Returns:
            Dictionary defining the expected payload structure
        """
        return {
            "content": "text",  # The actual content chunk
            "source_url": "keyword",  # URL where the content came from
            "page_title": "text",  # Title of the source page
            "chunk_order": "integer",  # Order of the chunk in the document
            "chunk_id": "keyword",  # Unique identifier for the chunk
            "created_at": "datetime",  # Timestamp of when the embedding was created
            "document_metadata": "keyword",  # Additional metadata about the document
        }

    def create_book_embeddings_collection(
        self,
        client,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine",
        recreate: bool = False
    ) -> bool:
        """
        Create a collection for book embeddings with appropriate schema.

        Args:
            client: Qdrant client instance
            collection_name: Name of the collection to create
            vector_size: Size of the embedding vectors
            distance: Distance metric for similarity search
            recreate: Whether to recreate the collection if it exists

        Returns:
            True if collection was created successfully
        """
        try:
            # Check if collection exists
            collection_exists = False
            try:
                client.get_collection(collection_name)
                collection_exists = True
            except:
                collection_exists = False

            if collection_exists and not recreate:
                if self.logger:
                    self.logger.info(f"Collection '{collection_name}' already exists")
                return True

            if collection_exists and recreate:
                if self.logger:
                    self.logger.info(f"Recreating collection '{collection_name}'")
                client.delete_collection(collection_name)

            # Create collection with specified configuration
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance[distance.upper()]
                )
            )

            if self.logger:
                self.logger.info(
                    f"Created collection '{collection_name}' with vector size {vector_size} "
                    f"and {distance} distance metric"
                )

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create collection '{collection_name}': {str(e)}")
            return False

    def get_default_hnsw_config(self) -> Dict[str, Any]:
        """
        Get default HNSW configuration for optimized similarity search.

        Returns:
            Dictionary with HNSW configuration
        """
        return {
            "m": 16,  # Number of edges per vertex
            "ef_construct": 100,  # Size of the dynamic list for the nearest neighbors
            "full_scan_threshold": 10000,  # Use plain index if less than this points
        }

    def get_default_optimizers_config(self) -> Dict[str, Any]:
        """
        Get default optimizers configuration for collection performance.

        Returns:
            Dictionary with optimizers configuration
        """
        return {
            "deleted_threshold": 0.2,  # Clean up deleted points when they reach 20% of collection
            "vacuum_min_vector_number": 1000,  # Minimum number of vectors to trigger vacuum
            "default_segment_number": 2,  # Number of segments to create
            "max_segment_size": 100000,  # Maximum size of a single segment
            "memmap_threshold": 10000,  # Memory map segments larger than this threshold
            "indexing_threshold": 20000,  # Index segments larger than this threshold
        }

    def validate_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate that a payload matches the expected schema.

        Args:
            payload: Payload to validate

        Returns:
            True if payload is valid, False otherwise
        """
        required_fields = ['content', 'source_url', 'page_title', 'chunk_order', 'chunk_id']

        for field in required_fields:
            if field not in payload:
                if self.logger:
                    self.logger.warning(f"Missing required field '{field}' in payload")
                return False

        # Validate field types
        if not isinstance(payload['content'], str):
            if self.logger:
                self.logger.warning("Content field must be a string")
            return False

        if not isinstance(payload['source_url'], str):
            if self.logger:
                self.logger.warning("Source URL field must be a string")
            return False

        if not isinstance(payload['page_title'], str):
            if self.logger:
                self.logger.warning("Page title field must be a string")
            return False

        if not isinstance(payload['chunk_order'], int):
            if self.logger:
                self.logger.warning("Chunk order field must be an integer")
            return False

        if not isinstance(payload['chunk_id'], str):
            if self.logger:
                self.logger.warning("Chunk ID field must be a string")
            return False

        return True

    def create_payload(
        self,
        content: str,
        source_url: str,
        page_title: str,
        chunk_order: int,
        chunk_id: str,
        **additional_metadata
    ) -> Dict[str, Any]:
        """
        Create a properly formatted payload for storage in Qdrant.

        Args:
            content: Content text
            source_url: Source URL
            page_title: Page title
            chunk_order: Order of chunk in document
            chunk_id: Unique chunk identifier
            **additional_metadata: Additional metadata to include

        Returns:
            Dictionary formatted as Qdrant payload
        """
        payload = {
            "content": content,
            "source_url": source_url,
            "page_title": page_title,
            "chunk_order": chunk_order,
            "chunk_id": chunk_id,
            "created_at": __import__('datetime').datetime.utcnow().isoformat()
        }

        # Add any additional metadata
        payload.update(additional_metadata)

        return payload

    def get_collection_recommendations(
        self,
        expected_size: int,
        distance: str = "Cosine"
    ) -> Dict[str, Any]:
        """
        Get recommendations for collection configuration based on expected size.

        Args:
            expected_size: Expected number of vectors in the collection
            distance: Distance metric for similarity search

        Returns:
            Dictionary with configuration recommendations
        """
        recommendations = {
            "vector_size": 1024,  # Default for Cohere embeddings
            "distance": distance,
            "hnsw_config": self.get_default_hnsw_config(),
            "optimizers_config": self.get_default_optimizers_config()
        }

        # Adjust configuration based on expected size
        if expected_size > 100000:  # Large collection
            recommendations["hnsw_config"]["m"] = 32
            recommendations["hnsw_config"]["ef_construct"] = 200
            recommendations["optimizers_config"]["max_segment_size"] = 200000
            recommendations["optimizers_config"]["indexing_threshold"] = 50000
        elif expected_size > 10000:  # Medium collection
            recommendations["hnsw_config"]["m"] = 24
            recommendations["hnsw_config"]["ef_construct"] = 150
            recommendations["optimizers_config"]["max_segment_size"] = 150000
            recommendations["optimizers_config"]["indexing_threshold"] = 30000

        return recommendations