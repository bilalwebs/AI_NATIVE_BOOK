from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from rag.utils.retry_utils import retry_on_exception
import time


T = TypeVar('T')
R = TypeVar('R')


class BatchProcessor(Generic[T, R]):
    """
    Generic batch processor for handling large amounts of data efficiently.
    """
    def __init__(
        self,
        process_function: Callable[[List[T]], List[R]],
        batch_size: int = 10,
        max_workers: int = 4,
        logger: logging.Logger = None
    ):
        """
        Initialize the batch processor.

        Args:
            process_function: Function that takes a batch of items and returns processed results
            batch_size: Size of each batch
            max_workers: Maximum number of worker threads
            logger: Logger instance for logging
        """
        self.process_function = process_function
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.logger = logger or logging.getLogger(__name__)

    def create_batches(self, items: List[T]) -> List[List[T]]:
        """
        Split a list of items into batches.

        Args:
            items: List of items to batch

        Returns:
            List of batches (each batch is a list of items)
        """
        batches = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batches.append(batch)
        return batches

    def process_sequentially(self, items: List[T]) -> List[R]:
        """
        Process all items sequentially in batches.

        Args:
            items: List of items to process

        Returns:
            List of processed results
        """
        batches = self.create_batches(items)
        all_results = []

        for i, batch in enumerate(batches):
            if self.logger:
                self.logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} items")

            try:
                batch_results = self.process_function(batch)
                all_results.extend(batch_results)

                if self.logger:
                    self.logger.info(f"Completed batch {i+1}, got {len(batch_results)} results")

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error processing batch {i+1}: {str(e)}")
                raise

        return all_results

    def process_in_parallel(self, items: List[T]) -> List[R]:
        """
        Process all items in parallel batches.

        Args:
            items: List of items to process

        Returns:
            List of processed results
        """
        batches = self.create_batches(items)
        all_results = [None] * len(batches)  # Pre-allocate for thread-safe assignment

        def process_batch_with_index(batch_idx_batch_tuple):
            batch_idx, batch = batch_idx_batch_tuple
            if self.logger:
                self.logger.info(f"Processing batch {batch_idx+1}/{len(batches)} with {len(batch)} items (parallel)")

            try:
                batch_results = self.process_function(batch)
                if self.logger:
                    self.logger.info(f"Completed parallel batch {batch_idx+1}, got {len(batch_results)} results")
                return batch_idx, batch_results
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error processing parallel batch {batch_idx+1}: {str(e)}")
                raise

        # Create tuples of (index, batch) for tracking
        indexed_batches = [(i, batch) for i, batch in enumerate(batches)]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(process_batch_with_index, indexed_batch): indexed_batch[0]
                for indexed_batch in indexed_batches
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_idx, batch_results = future.result()
                all_results[batch_idx] = batch_results

        # Flatten the results
        flattened_results = []
        for batch_results in all_results:
            if batch_results is not None:
                flattened_results.extend(batch_results)

        return flattened_results

    def process(self, items: List[T], parallel: bool = False) -> List[R]:
        """
        Process items using either sequential or parallel processing.

        Args:
            items: List of items to process
            parallel: Whether to process in parallel

        Returns:
            List of processed results
        """
        if not items:
            return []

        if parallel and len(items) > self.batch_size:
            return self.process_in_parallel(items)
        else:
            return self.process_sequentially(items)


class EmbeddingBatchProcessor:
    """
    Specialized batch processor for embedding operations.
    """
    def __init__(
        self,
        embedding_client,
        batch_size: int = 10,
        max_workers: int = 4,
        logger: logging.Logger = None
    ):
        """
        Initialize the embedding batch processor.

        Args:
            embedding_client: Embedding client to use for processing
            batch_size: Size of each batch
            max_workers: Maximum number of worker threads
            logger: Logger instance for logging
        """
        self.embedding_client = embedding_client
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.logger = logger or logging.getLogger(__name__)

    @retry_on_exception(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
        backoff_factor=2.0,
        exceptions=(Exception,),
        logger=None
    )
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts with retry logic.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embedding_client.embed_texts(texts, batch_size=len(texts))

    def embed_texts_in_batches(
        self,
        texts: List[str],
        parallel: bool = False
    ) -> List[List[float]]:
        """
        Embed a list of texts using batch processing.

        Args:
            texts: List of texts to embed
            parallel: Whether to process batches in parallel

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Create a batch processor for embeddings
        processor = BatchProcessor(
            process_function=self._embed_batch,
            batch_size=self.batch_size,
            max_workers=self.max_workers,
            logger=self.logger
        )

        return processor.process(texts, parallel=parallel)

    def embed_documents_in_batches(
        self,
        documents: List[Dict[str, Any]],
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Embed a list of documents (with metadata) using batch processing.

        Args:
            documents: List of documents with content and metadata
            parallel: Whether to process batches in parallel

        Returns:
            List of documents with embeddings added
        """
        if not documents:
            return []

        # Extract texts while preserving document structure
        texts = [doc.get('content', '') for doc in documents]

        # Embed the texts
        embeddings = self.embed_texts_in_batches(texts, parallel=parallel)

        # Combine embeddings with original documents
        result = []
        for doc, embedding in zip(documents, embeddings):
            doc_copy = doc.copy()
            doc_copy['embedding'] = embedding
            result.append(doc_copy)

        return result

    def get_batch_stats(self, items_count: int) -> Dict[str, Any]:
        """
        Get statistics about batch processing for a given number of items.

        Args:
            items_count: Number of items to process

        Returns:
            Dictionary with batch processing statistics
        """
        if items_count <= 0:
            return {
                'items_count': 0,
                'batch_size': self.batch_size,
                'num_batches': 0,
                'last_batch_size': 0
            }

        num_batches = (items_count + self.batch_size - 1) // self.batch_size  # Ceiling division
        last_batch_size = items_count % self.batch_size
        if last_batch_size == 0 and items_count > 0:
            last_batch_size = self.batch_size

        return {
            'items_count': items_count,
            'batch_size': self.batch_size,
            'num_batches': num_batches,
            'last_batch_size': last_batch_size,
            'estimated_requests': num_batches
        }


def create_optimized_batch_processor(
    embedding_client,
    preferred_batch_size: int = 10,
    max_workers: int = 4,
    logger: logging.Logger = None
) -> EmbeddingBatchProcessor:
    """
    Create an optimized batch processor with recommended settings.

    Args:
        embedding_client: Embedding client to use
        preferred_batch_size: Preferred batch size (will be adjusted based on API limits)
        max_workers: Maximum number of worker threads
        logger: Logger instance for logging

    Returns:
        Configured EmbeddingBatchProcessor
    """
    # Adjust batch size based on API limits (for Cohere, the max is typically 96)
    max_api_batch_size = 96  # Common limit for Cohere API
    adjusted_batch_size = min(preferred_batch_size, max_api_batch_size)

    return EmbeddingBatchProcessor(
        embedding_client=embedding_client,
        batch_size=adjusted_batch_size,
        max_workers=max_workers,
        logger=logger
    )