from typing import List, Dict, Any, Optional
import logging
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from rag.data_models import EmbeddingVector, StorageRecord
from rag.storage.qdrant_schema import QdrantSchema
from rag.utils.metrics import ProgressTracker
from rag.utils.retry_utils import retry_on_exception, is_retryable_http_status
import requests


class QdrantStorage:
    """
    Class to handle storage of embeddings in Qdrant Cloud with metadata.
    """
    def __init__(
        self,
        client: QdrantClient,
        schema: QdrantSchema = None,
        collection_name: str = "book_embeddings",
        logger: logging.Logger = None
    ):
        """
        Initialize the Qdrant storage handler.

        Args:
            client: Qdrant client instance
            schema: Qdrant schema manager (creates default if None)
            collection_name: Name of the collection to use
            logger: Logger instance for logging
        """
        self.client = client
        self.schema = schema or QdrantSchema()
        self.collection_name = collection_name
        self.logger = logger or logging.getLogger(__name__)
        self.progress_tracker = ProgressTracker(logger=self.logger)

    def ensure_collection_exists(
        self,
        vector_size: int,
        distance: str = "Cosine",
        recreate: bool = False
    ) -> bool:
        """
        Ensure the collection exists with the correct configuration.

        Args:
            vector_size: Size of the embedding vectors
            distance: Distance metric for similarity search
            recreate: Whether to recreate the collection if it exists

        Returns:
            True if collection exists (or was created successfully)
        """
        try:
            success = self.schema.create_book_embeddings_collection(
                self.client,
                self.collection_name,
                vector_size,
                distance,
                recreate
            )

            if success and self.logger:
                self.logger.info(f"Collection '{self.collection_name}' is ready for use")

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to ensure collection exists: {str(e)}")
            return False

    @retry_on_exception(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
        backoff_factor=2.0,
        exceptions=(Exception,),
        logger=None
    )
    def _store_batch(
        self,
        points: List[models.PointStruct]
    ) -> bool:
        """
        Store a batch of points in Qdrant with retry logic.

        Args:
            points: List of PointStruct objects to store

        Returns:
            True if storage was successful
        """
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to store batch of {len(points)} points: {str(e)}")
            raise

    def store_embeddings(
        self,
        embedding_vectors: List[EmbeddingVector],
        metadata_list: List[Dict[str, Any]],
        batch_size: int = 64,
        validate_payloads: bool = True
    ) -> Dict[str, Any]:
        """
        Store embedding vectors with their associated metadata in Qdrant.

        Args:
            embedding_vectors: List of EmbeddingVector objects to store
            metadata_list: List of metadata dictionaries corresponding to embeddings
            batch_size: Number of embeddings to store in each batch
            validate_payloads: Whether to validate payloads before storing

        Returns:
            Dictionary with storage results and metrics
        """
        if not embedding_vectors or not metadata_list:
            if self.logger:
                self.logger.warning("No embeddings or metadata provided for storage")
            return {
                'success': False,
                'total_embeddings': 0,
                'stored_count': 0,
                'failed_count': 0,
                'message': 'No embeddings or metadata provided'
            }

        if len(embedding_vectors) != len(metadata_list):
            raise ValueError("embedding_vectors and metadata_list must have the same length")

        # Ensure collection exists
        first_vector = embedding_vectors[0]
        if not self.ensure_collection_exists(len(first_vector.vector)):
            return {
                'success': False,
                'total_embeddings': len(embedding_vectors),
                'stored_count': 0,
                'failed_count': len(embedding_vectors),
                'message': 'Failed to ensure collection exists'
            }

        # Prepare points for storage
        points = []
        validation_errors = []

        for i, (emb_vector, metadata) in enumerate(zip(embedding_vectors, metadata_list)):
            try:
                # Create payload
                payload = self.schema.create_payload(
                    content=metadata.get('content', ''),
                    source_url=metadata.get('source_url', ''),
                    page_title=metadata.get('page_title', ''),
                    chunk_order=metadata.get('chunk_order', 0),
                    chunk_id=metadata.get('chunk_id', emb_vector.chunk_id),
                    **{k: v for k, v in metadata.items()
                       if k not in ['content', 'source_url', 'page_title', 'chunk_order', 'chunk_id']}
                )

                # Validate payload if requested
                if validate_payloads and not self.schema.validate_payload(payload):
                    validation_errors.append(f"Payload validation failed for embedding {i}")
                    continue

                # Create point
                point = models.PointStruct(
                    id=str(uuid4()),  # Generate unique ID for this storage record
                    vector=emb_vector.vector,
                    payload=payload
                )

                points.append(point)

            except Exception as e:
                validation_errors.append(f"Error preparing embedding {i}: {str(e)}")
                continue

        if validation_errors and self.logger:
            self.logger.warning(f"Validation errors encountered: {len(validation_errors)}")
            for error in validation_errors[:5]:  # Log first 5 errors
                self.logger.warning(error)

        if not points:
            return {
                'success': False,
                'total_embeddings': len(embedding_vectors),
                'stored_count': 0,
                'failed_count': len(embedding_vectors),
                'validation_errors': validation_errors,
                'message': 'No valid points to store after validation'
            }

        # Track progress
        total_points = len(points)
        self.progress_tracker.start_task('storage', total_items=total_points)

        # Store in batches
        stored_count = 0
        failed_batches = 0

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]

            try:
                success = self._store_batch(batch)
                if success:
                    batch_count = len(batch)
                    stored_count += batch_count
                    self.progress_tracker.update_progress('storage', successful=True, increment=batch_count)

                    if self.logger and i % (batch_size * 5) == 0:  # Log every 5 batches
                        self.logger.info(f"Stored {stored_count}/{total_points} embeddings")
                else:
                    failed_batches += 1
                    batch_count = len(batch)
                    self.progress_tracker.update_progress('storage', successful=False, increment=batch_count)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to store batch starting at index {i}: {str(e)}")
                failed_batches += 1
                batch_count = len(batch)
                self.progress_tracker.update_progress('storage', successful=False, increment=batch_count)

        self.progress_tracker.complete_task('storage')

        success = stored_count == total_points
        message = f"Stored {stored_count}/{total_points} embeddings successfully"

        if self.logger:
            log_level = logging.INFO if success else logging.WARNING
            self.logger.log(log_level, message)

        return {
            'success': success,
            'total_embeddings': len(embedding_vectors),
            'total_points': total_points,
            'stored_count': stored_count,
            'failed_count': total_points - stored_count,
            'failed_batches': failed_batches,
            'validation_errors': validation_errors,
            'message': message
        }

    def store_single_embedding(
        self,
        embedding_vector: EmbeddingVector,
        metadata: Dict[str, Any]
    ) -> StorageRecord:
        """
        Store a single embedding vector with metadata.

        Args:
            embedding_vector: EmbeddingVector to store
            metadata: Metadata dictionary for the embedding

        Returns:
            StorageRecord representing the stored record
        """
        result = self.store_embeddings([embedding_vector], [metadata], batch_size=1)

        if result['success'] and result['stored_count'] > 0:
            # Generate a storage record ID
            record_id = str(uuid4())
            storage_record = StorageRecord(
                record_id=record_id,
                embedding_id=embedding_vector.embedding_id,
                payload=metadata,
                vector_size=len(embedding_vector.vector)
            )
            return storage_record

        raise Exception(f"Failed to store single embedding: {result.get('message', 'Unknown error')}")

    def count_points(self) -> int:
        """
        Count the number of points in the collection.

        Returns:
            Number of points in the collection
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.points_count
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error counting points in collection: {str(e)}")
            return 0

    def delete_collection(self) -> bool:
        """
        Delete the entire collection.

        Returns:
            True if deletion was successful
        """
        try:
            self.client.delete_collection(self.collection_name)
            if self.logger:
                self.logger.info(f"Deleted collection '{self.collection_name}'")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting collection: {str(e)}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the storage collection.

        Returns:
            Dictionary with storage statistics
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                'collection_name': self.collection_name,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance,
                'point_count': collection_info.points_count,
                'indexed_vectors_count': collection_info.indexed_vectors_count,
                'state': collection_info.status
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting storage stats: {str(e)}")
            return {'error': str(e)}

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[models.Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in the collection.

        Args:
            query_vector: Vector to search for similarity
            top_k: Number of top results to return
            filters: Optional filters to apply to the search

        Returns:
            List of similar results with payload and similarity scores
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filters
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload,
                    'vector': result.vector
                })

            return formatted_results

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error searching for similar embeddings: {str(e)}")
            return []

    def get_points_by_ids(
        self,
        point_ids: List[str]
    ) -> List[models.Record]:
        """
        Retrieve points by their IDs.

        Args:
            point_ids: List of point IDs to retrieve

        Returns:
            List of Record objects
        """
        try:
            records = self.client.retrieve(
                collection_name=self.collection_name,
                ids=point_ids
            )
            return records
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error retrieving points by IDs: {str(e)}")
            return []

    def _handle_qdrant_error(self, error: Exception, operation: str = "unknown") -> Dict[str, Any]:
        """
        Handle Qdrant-specific errors and categorize them.

        Args:
            error: The exception that occurred
            operation: The operation during which the error occurred

        Returns:
            Dictionary with error details and classification
        """
        error_info = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'is_retryable': False,
            'should_abort': False,
            'suggested_action': 'retry'
        }

        # Categorize the error
        if isinstance(error, requests.exceptions.ConnectionError):
            error_info.update({
                'is_retryable': True,
                'suggested_action': 'retry_after_delay'
            })
        elif isinstance(error, requests.exceptions.Timeout):
            error_info.update({
                'is_retryable': True,
                'suggested_action': 'retry_with_backoff'
            })
        elif isinstance(error, UnexpectedResponse):
            # Check the status code to determine retryability
            if hasattr(error, 'status_code'):
                if is_retryable_http_status(error.status_code):
                    error_info.update({
                        'is_retryable': True,
                        'status_code': error.status_code,
                        'suggested_action': 'retry_after_delay'
                    })
                else:
                    error_info.update({
                        'is_retryable': False,
                        'status_code': error.status_code,
                        'should_abort': True,
                        'suggested_action': 'abort_and_investigate'
                    })
        elif "connection" in str(error).lower() or "network" in str(error).lower():
            error_info.update({
                'is_retryable': True,
                'suggested_action': 'retry_after_delay'
            })
        elif "timeout" in str(error).lower():
            error_info.update({
                'is_retryable': True,
                'suggested_action': 'retry_with_backoff'
            })
        elif "rate limit" in str(error).lower() or "429" in str(error):
            error_info.update({
                'is_retryable': True,
                'suggested_action': 'retry_after_longer_delay'
            })

        if self.logger:
            self.logger.error(
                f"Qdrant error during {operation}: {error_info['error_type']} - {error_info['error_message']}. "
                f"Suggested action: {error_info['suggested_action']}"
            )

        return error_info

    def test_connection(self) -> bool:
        """
        Test the connection to Qdrant Cloud.

        Returns:
            True if connection is successful
        """
        try:
            # Try to get collection info as a simple connection test
            self.client.get_collection(self.collection_name)
            if self.logger:
                self.logger.info("Qdrant connection test successful")
            return True
        except Exception as e:
            error_info = self._handle_qdrant_error(e, "connection_test")
            if self.logger:
                self.logger.error(f"Qdrant connection test failed: {error_info['error_message']}")
            return False

    def handle_storage_error(
        self,
        error: Exception,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Handle storage-specific errors with appropriate responses.

        Args:
            error: The storage error that occurred
            context: Additional context about where the error occurred

        Returns:
            Dictionary with error handling information
        """
        error_info = self._handle_qdrant_error(error, f"storage_{context}")

        # For storage operations, we might want to implement specific handling
        if error_info['suggested_action'] == 'abort_and_investigate':
            # For critical storage errors, we might want to trigger additional actions
            if self.logger:
                self.logger.critical(f"Critical storage error in {context}. Consider checking Qdrant Cloud status.")

        return error_info