from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import Optional, Dict, Any, List
import logging


class QdrantManager:
    """
    Utility class for managing Qdrant client connection and collection operations.
    """
    def __init__(
        self,
        url: str,
        api_key: str,
        timeout: int = 30,
        logger: logging.Logger = None
    ):
        """
        Initialize Qdrant manager with connection details.

        Args:
            url: Qdrant Cloud URL
            api_key: Qdrant Cloud API key
            timeout: Request timeout in seconds
            logger: Logger instance for logging
        """
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

        # Initialize client
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=self.timeout
        )

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists in Qdrant.

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if collection exists, False otherwise
        """
        try:
            self.client.get_collection(collection_name)
            return True
        except Exception:
            return False

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine",
        overwrite: bool = False
    ) -> bool:
        """
        Create a collection in Qdrant with specified parameters.

        Args:
            collection_name: Name of the collection to create
            vector_size: Size of the embedding vectors
            distance: Distance metric for similarity search (Cosine, Euclid, Dot)
            overwrite: Whether to overwrite if collection exists

        Returns:
            True if collection was created, False if it already existed
        """
        if self.collection_exists(collection_name):
            if overwrite:
                if self.logger:
                    self.logger.info(f"Overwriting existing collection: {collection_name}")
                self.client.delete_collection(collection_name)
            else:
                if self.logger:
                    self.logger.info(f"Collection already exists: {collection_name}")
                return False

        # Create collection
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance[distance.upper()]
            )
        )

        if self.logger:
            self.logger.info(f"Created collection: {collection_name} with vector size {vector_size}")

        return True

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from Qdrant.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True if collection was deleted, False if it didn't exist
        """
        try:
            self.client.delete_collection(collection_name)
            if self.logger:
                self.logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to delete collection {collection_name}: {str(e)}")
            return False

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection information or None if collection doesn't exist
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                'name': collection_info.config.params.vectors.size,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance,
                'point_count': collection_info.points_count
            }
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to get collection info for {collection_name}: {str(e)}")
            return None

    def recreate_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """
        Recreate a collection (delete and create again).

        Args:
            collection_name: Name of the collection to recreate
            vector_size: Size of the embedding vectors
            distance: Distance metric for similarity search

        Returns:
            True if collection was recreated
        """
        self.delete_collection(collection_name)
        return self.create_collection(
            collection_name=collection_name,
            vector_size=vector_size,
            distance=distance,
            overwrite=False  # We already deleted it
        )

    def health_check(self) -> bool:
        """
        Perform a health check on the Qdrant connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Try to list collections to verify connection
            self.client.get_collections()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Qdrant health check failed: {str(e)}")
            return False