from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging
import numpy as np
from rag.processing.embedding_client import CohereEmbeddingClient


class QdrantSearch:
    """
    Class to implement similarity search in Qdrant Cloud.
    """
    def __init__(
        self,
        client: QdrantClient,
        embedding_client: CohereEmbeddingClient,
        collection_name: str = "book_embeddings",
        logger: logging.Logger = None
    ):
        """
        Initialize the Qdrant search handler.

        Args:
            client: Qdrant client instance
            embedding_client: Embedding client for generating query embeddings
            collection_name: Name of the collection to search in
            logger: Logger instance for logging
        """
        self.client = client
        self.embedding_client = embedding_client
        self.collection_name = collection_name
        self.logger = logger or logging.getLogger(__name__)

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a query string using the embedding client.

        Args:
            query: Query string to embed

        Returns:
            Embedding vector for the query
        """
        return self.embedding_client.embed_single_text(query)

    def search_by_text(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[models.Filter] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using a text query.

        Args:
            query: Text query to search for
            top_k: Number of top results to return
            filters: Optional filters to apply to the search
            with_payload: Whether to include payload in results
            with_vectors: Whether to include vectors in results

        Returns:
            List of search results with payload and similarity scores
        """
        # Embed the query text
        try:
            query_vector = self.embed_query(query)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error embedding query: {str(e)}")
            return []

        # Perform the search
        return self.search_by_vector(
            query_vector,
            top_k=top_k,
            filters=filters,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

    def search_by_vector(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[models.Filter] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using a vector query.

        Args:
            query_vector: Vector to search for similarity
            top_k: Number of top results to return
            filters: Optional filters to apply to the search
            with_payload: Whether to include payload in results
            with_vectors: Whether to include vectors in results

        Returns:
            List of search results with payload and similarity scores
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filters,
                with_payload=with_payload,
                with_vectors=with_vectors
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                }

                if with_vectors:
                    formatted_result['vector'] = result.vector

                formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error performing vector search: {str(e)}")
            return []

    def search_with_filters(
        self,
        query: str,
        source_url: Optional[str] = None,
        min_score: Optional[float] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search with additional filtering options.

        Args:
            query: Text query to search for
            source_url: Filter results by source URL
            min_score: Minimum similarity score threshold
            top_k: Number of top results to return

        Returns:
            List of filtered search results
        """
        # Build filters
        filter_conditions = []

        if source_url:
            filter_conditions.append(
                models.FieldCondition(
                    key="source_url",
                    match=models.MatchValue(value=source_url)
                )
            )

        final_filter = None
        if filter_conditions:
            final_filter = models.Filter(must=filter_conditions)

        # Perform search
        results = self.search_by_text(query, top_k=top_k, filters=final_filter)

        # Apply score threshold
        if min_score is not None:
            results = [r for r in results if r['score'] >= min_score]

        return results

    def find_similar_to_content(
        self,
        content: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find content similar to the provided content.

        Args:
            content: Content to find similar content to
            top_k: Number of top results to return

        Returns:
            List of similar content results
        """
        return self.search_by_text(content, top_k=top_k)

    def batch_search(
        self,
        queries: List[str],
        top_k: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        Perform multiple searches in batch.

        Args:
            queries: List of query strings
            top_k: Number of top results to return for each query

        Returns:
            List of result lists (one for each query)
        """
        results = []
        for query in queries:
            query_results = self.search_by_text(query, top_k=top_k)
            results.append(query_results)
        return results

    def get_relevant_content(
        self,
        query: str,
        top_k: int = 10,
        min_score: Optional[float] = 0.1,
        return_content_only: bool = False
    ) -> Union[List[str], List[Dict[str, Any]]]:
        """
        Get relevant content for a query, optionally filtering by score.

        Args:
            query: Query string to search for
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold
            return_content_only: Whether to return only content strings

        Returns:
            List of relevant content (either as strings or full result dicts)
        """
        results = self.search_by_text(query, top_k=top_k)

        # Apply score threshold
        if min_score is not None:
            results = [r for r in results if r['score'] >= min_score]

        if return_content_only:
            return [r['payload']['content'] for r in results if 'content' in r['payload']]

        return results

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search with optional metadata filters.

        Args:
            query: Query string for semantic search
            top_k: Number of top results to return
            filters: Dictionary of metadata filters to apply

        Returns:
            List of semantic search results
        """
        # Build filters from dictionary
        qdrant_filters = None
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                elif isinstance(value, (list, tuple)):
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=list(value))
                        )
                    )
                # Add more filter types as needed

            if filter_conditions:
                qdrant_filters = models.Filter(must=filter_conditions)

        return self.search_by_text(query, top_k=top_k, filters=qdrant_filters)

    def find_content_by_source(
        self,
        query: str,
        source_url: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find content similar to the query but only from a specific source URL.

        Args:
            query: Query string to search for
            source_url: Source URL to filter by
            top_k: Number of top results to return

        Returns:
            List of search results from the specific source
        """
        return self.search_with_filters(
            query=query,
            source_url=source_url,
            top_k=top_k
        )

    def get_search_statistics(
        self,
        query: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Get statistics about a search query (e.g., score distribution).

        Args:
            query: Query string to analyze
            top_k: Number of top results to analyze

        Returns:
            Dictionary with search statistics
        """
        results = self.search_by_text(query, top_k=top_k)

        if not results:
            return {
                'query': query,
                'result_count': 0,
                'avg_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0,
                'score_std_dev': 0.0
            }

        scores = [r['score'] for r in results]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        # Calculate standard deviation
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5

        return {
            'query': query,
            'result_count': len(results),
            'avg_score': avg_score,
            'min_score': min_score,
            'max_score': max_score,
            'score_std_dev': std_dev,
            'scores': scores
        }

    def validate_search_results(
        self,
        results: List[Dict[str, Any]],
        min_content_length: int = 10
    ) -> Dict[str, Any]:
        """
        Validate search results for quality.

        Args:
            results: List of search results to validate
            min_content_length: Minimum content length to be considered valid

        Returns:
            Dictionary with validation results
        """
        if not results:
            return {
                'valid': True,
                'total_results': 0,
                'valid_results': 0,
                'invalid_results': 0,
                'message': 'No results to validate'
            }

        total_results = len(results)
        valid_results = 0
        invalid_reasons = []

        for i, result in enumerate(results):
            try:
                payload = result.get('payload', {})
                content = payload.get('content', '')

                if len(content) >= min_content_length:
                    valid_results += 1
                else:
                    invalid_reasons.append(f"Result {i}: content too short ({len(content)} chars)")

            except Exception as e:
                invalid_reasons.append(f"Result {i}: validation error - {str(e)}")

        valid_ratio = valid_results / total_results
        is_valid = valid_ratio >= 0.8  # At least 80% should be valid

        return {
            'valid': is_valid,
            'total_results': total_results,
            'valid_results': valid_results,
            'invalid_results': total_results - valid_results,
            'valid_ratio': valid_ratio,
            'min_content_length': min_content_length,
            'invalid_reasons': invalid_reasons,
            'message': f"Validation: {valid_results}/{total_results} results valid ({valid_ratio:.2%})"
        }