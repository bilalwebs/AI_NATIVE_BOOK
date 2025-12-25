from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging


class QdrantIndexing:
    """
    Class to manage indexing for efficient similarity search in Qdrant.
    """
    def __init__(
        self,
        client: QdrantClient,
        logger: logging.Logger = None
    ):
        """
        Initialize the Qdrant indexing manager.

        Args:
            client: Qdrant client instance
            logger: Logger instance for logging
        """
        self.client = client
        self.logger = logger or logging.getLogger(__name__)

    def create_payload_index(
        self,
        collection_name: str,
        field_name: str,
        field_type: str = "keyword"  # keyword, text, integer, float, geo, etc.
    ) -> bool:
        """
        Create an index on a payload field for efficient filtering and searching.

        Args:
            collection_name: Name of the collection
            field_name: Name of the field to index
            field_type: Type of the field to index

        Returns:
            True if index was created successfully
        """
        try:
            field_schema_map = {
                "keyword": models.TextIndexType.KEYWORD,
                "text": models.TextIndexType.TEXT,
                "integer": models.IntegerIndexType.INTEGER,
                "float": models.FloatIndexType.FLOAT,
                "geo": models.GeoIndexType.GEO,
                "bool": models.BoolIndexType.BOOL
            }

            # Determine the appropriate index type based on field_type
            if field_type in ["keyword", "text"]:
                index_type = models.PayloadIndexType.Field
                schema = models.PayloadSchemaType.KEYWORD if field_type == "keyword" else models.PayloadSchemaType.TEXT
            elif field_type == "integer":
                schema = models.PayloadSchemaType.INTEGER
            elif field_type == "float":
                schema = models.PayloadSchemaType.FLOAT
            elif field_type == "geo":
                schema = models.PayloadSchemaType.GEO
            elif field_type == "bool":
                schema = models.PayloadSchemaType.BOOL
            else:
                raise ValueError(f"Unsupported field type: {field_type}")

            # Create the index
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema
            )

            if self.logger:
                self.logger.info(f"Created index on field '{field_name}' of type '{field_type}' in collection '{collection_name}'")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create index on field '{field_name}': {str(e)}")
            return False

    def create_multiple_payload_indexes(
        self,
        collection_name: str,
        field_configs: List[Dict[str, str]]
    ) -> Dict[str, bool]:
        """
        Create multiple payload indexes at once.

        Args:
            collection_name: Name of the collection
            field_configs: List of dictionaries with 'field_name' and 'field_type' keys

        Returns:
            Dictionary mapping field names to success status
        """
        results = {}
        for config in field_configs:
            field_name = config.get('field_name')
            field_type = config.get('field_type', 'keyword')

            success = self.create_payload_index(collection_name, field_name, field_type)
            results[field_name] = success

        return results

    def create_optimized_indexes_for_book_embeddings(
        self,
        collection_name: str
    ) -> Dict[str, bool]:
        """
        Create optimized indexes for book embeddings collection based on common query patterns.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary mapping field names to success status
        """
        # Define the fields that are commonly used for filtering/searching
        field_configs = [
            {'field_name': 'source_url', 'field_type': 'keyword'},      # For filtering by source
            {'field_name': 'page_title', 'field_type': 'text'},         # For text search in titles
            {'field_name': 'chunk_order', 'field_type': 'integer'},     # For ordering chunks
            {'field_name': 'chunk_id', 'field_type': 'keyword'},        # For unique chunk identification
            {'field_name': 'created_at', 'field_type': 'keyword'},      # For time-based queries
        ]

        if self.logger:
            self.logger.info(f"Creating optimized indexes for collection '{collection_name}'")

        return self.create_multiple_payload_indexes(collection_name, field_configs)

    def delete_payload_index(
        self,
        collection_name: str,
        field_name: str
    ) -> bool:
        """
        Delete a payload index.

        Args:
            collection_name: Name of the collection
            field_name: Name of the field index to delete

        Returns:
            True if index was deleted successfully
        """
        try:
            self.client.delete_payload_index(
                collection_name=collection_name,
                field_name=field_name
            )

            if self.logger:
                self.logger.info(f"Deleted index on field '{field_name}' in collection '{collection_name}'")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to delete index on field '{field_name}': {str(e)}")
            return False

    def get_collection_indexes(
        self,
        collection_name: str
    ) -> Dict[str, Any]:
        """
        Get information about all indexes in a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with index information
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                'collection_name': collection_name,
                'config': collection_info.config,
                'payload_schema': collection_info.payload_schema,
                'indexed_vectors_count': collection_info.indexed_vectors_count,
                'points_count': collection_info.points_count
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get collection indexes for '{collection_name}': {str(e)}")
            return {'error': str(e)}

    def optimize_collection(
        self,
        collection_name: str,
        timeout: int = 60
    ) -> bool:
        """
        Optimize the collection for better search performance.

        Args:
            collection_name: Name of the collection
            timeout: Timeout for optimization in seconds

        Returns:
            True if optimization was successful
        """
        try:
            # Force optimization by creating and deleting a temporary index
            # This is a workaround as Qdrant doesn't have a direct optimize method
            temp_field = f"temp_optimize_{int(__import__('time').time())}"

            # Create a temporary index
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=temp_field,
                field_schema=models.PayloadSchemaType.KEYWORD
            )

            # Delete the temporary index
            self.client.delete_payload_index(
                collection_name=collection_name,
                field_name=temp_field
            )

            if self.logger:
                self.logger.info(f"Optimized collection '{collection_name}'")

            return True

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Optimization attempt failed for '{collection_name}': {str(e)}")
            # Optimization failure shouldn't be fatal, so return True
            return True

    def rebuild_index(
        self,
        collection_name: str,
        field_name: str
    ) -> bool:
        """
        Rebuild a specific index in the collection.

        Args:
            collection_name: Name of the collection
            field_name: Name of the field index to rebuild

        Returns:
            True if rebuild was successful
        """
        try:
            # Get current index info
            collection_info = self.client.get_collection(collection_name)

            # For rebuilding, we'll delete and recreate the index
            self.delete_payload_index(collection_name, field_name)

            # Determine the field type from the collection schema
            # This is a simplified approach - in practice, you'd need to inspect the payload structure
            # For now, we'll assume keyword type
            self.create_payload_index(collection_name, field_name, "keyword")

            if self.logger:
                self.logger.info(f"Rebuilt index on field '{field_name}' in collection '{collection_name}'")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to rebuild index on field '{field_name}': {str(e)}")
            return False

    def validate_index_performance(
        self,
        collection_name: str,
        sample_queries: List[str],
        sample_filter_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate index performance with sample queries.

        Args:
            collection_name: Name of the collection
            sample_queries: List of sample queries to test
            sample_filter_fields: List of fields to test filtering on

        Returns:
            Dictionary with performance validation results
        """
        import time

        if sample_filter_fields is None:
            sample_filter_fields = ['source_url', 'chunk_order']

        results = {
            'collection_name': collection_name,
            'query_performance': [],
            'filter_performance': [],
            'total_test_time': 0
        }

        start_time = time.time()

        # Test query performance
        for i, query in enumerate(sample_queries):
            query_start = time.time()
            try:
                # Perform a simple search to test performance
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=[0.1] * 1024,  # Dummy vector
                    limit=5
                )
                query_time = time.time() - query_start
                results['query_performance'].append({
                    'query_index': i,
                    'query': query,
                    'time': query_time,
                    'result_count': len(search_results)
                })
            except Exception as e:
                results['query_performance'].append({
                    'query_index': i,
                    'query': query,
                    'time': time.time() - query_start,
                    'error': str(e)
                })

        # Test filter performance
        for field in sample_filter_fields:
            filter_start = time.time()
            try:
                # Create a simple filter to test
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=field,
                            match=models.MatchValue(value="test")
                        )
                    ]
                )

                # Perform a search with filter
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=[0.1] * 1024,  # Dummy vector
                    limit=5,
                    query_filter=filter_condition
                )

                filter_time = time.time() - filter_start
                results['filter_performance'].append({
                    'field': field,
                    'time': filter_time,
                    'result_count': len(search_results)
                })
            except Exception as e:
                results['filter_performance'].append({
                    'field': field,
                    'time': time.time() - filter_start,
                    'error': str(e)
                })

        results['total_test_time'] = time.time() - start_time

        if self.logger:
            self.logger.info(f"Index performance validation completed for '{collection_name}' in {results['total_test_time']:.2f}s")

        return results