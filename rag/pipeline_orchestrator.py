from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime
from rag.crawling.url_crawler import URLCrawler
from rag.crawling.content_extractor import ContentExtractor
from rag.processing.pipeline import ChunkingEmbeddingPipeline
from rag.storage.qdrant_storage import QdrantStorage
from rag.storage.qdrant_search import QdrantSearch
from rag.config.config import Config
from rag.utils.metrics import ProgressTracker
from rag.storage.validation import validate_complete_storage_criteria


class BookEmbeddingPipeline:
    """
    Main orchestrator that connects crawling → chunking → embedding → storage.
    """

    def __init__(
        self,
        crawler: URLCrawler = None,
        content_extractor: ContentExtractor = None,
        chunking_pipeline: ChunkingEmbeddingPipeline = None,
        storage: QdrantStorage = None,
        search: QdrantSearch = None,
        logger: logging.Logger = None
    ):
        """
        Initialize the complete book embedding pipeline.

        Args:
            crawler: URLCrawler instance (creates default if None)
            content_extractor: ContentExtractor instance (creates default if None)
            chunking_pipeline: ChunkingEmbeddingPipeline instance (creates default if None)
            storage: QdrantStorage instance (creates default if None)
            search: QdrantSearch instance (creates default if None)
            logger: Logger instance for logging
        """
        self.crawler = crawler or URLCrawler()
        self.content_extractor = content_extractor or ContentExtractor()
        self.chunking_pipeline = chunking_pipeline or ChunkingEmbeddingPipeline()
        self.storage = storage
        self.search = search
        self.logger = logger or logging.getLogger(__name__)
        self.progress_tracker = ProgressTracker(logger=self.logger)

        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")

    def _initialize_storage_components(self):
        """Initialize storage components if not provided."""
        if self.storage is None:
            from qdrant_client import QdrantClient
            from rag.storage.qdrant_schema import QdrantSchema
            from rag.processing.embedding_client import CohereEmbeddingClient

            # Initialize Qdrant client
            client = QdrantClient(
                url=Config.QDRANT_URL,
                api_key=Config.QDRANT_API_KEY,
                prefer_grpc=True
            )

            # Initialize schema
            schema = QdrantSchema()

            # Initialize storage
            self.storage = QdrantStorage(
                client=client,
                schema=schema,
                logger=self.logger
            )

        if self.search is None:
            from rag.processing.embedding_client import CohereEmbeddingClient

            # Initialize embedding client for search
            embedding_client = CohereEmbeddingClient()

            # Initialize search
            self.search = QdrantSearch(
                client=self.storage.client,
                embedding_client=embedding_client,
                logger=self.logger
            )

    def run_crawling_stage(
        self,
        urls: List[str],
        max_concurrent: int = 5,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Run the crawling stage to extract content from URLs.

        Args:
            urls: List of URLs to crawl
            max_concurrent: Maximum number of concurrent requests
            timeout: Request timeout in seconds

        Returns:
            List of crawling results
        """
        self.logger.info(f"Starting crawling stage for {len(urls)} URLs")
        self.progress_tracker.start_task('crawling', total_items=len(urls))

        try:
            # Crawl all URLs
            crawl_results = self.crawler.crawl_urls(
                urls,
                max_concurrent=max_concurrent,
                timeout=timeout
            )

            # Extract content from crawled pages
            extracted_contents = []
            for result in crawl_results:
                if result.get('success', False):
                    content = self.content_extractor.extract_content(
                        result.get('html', ''),
                        result.get('url', ''),
                        result.get('title', '')
                    )
                    extracted_contents.append({
                        'url': result.get('url', ''),
                        'title': result.get('title', ''),
                        'content': content.get('content', ''),
                        'success': True
                    })
                else:
                    extracted_contents.append({
                        'url': result.get('url', ''),
                        'title': result.get('title', ''),
                        'content': '',
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    })

            successful_crawls = sum(1 for r in extracted_contents if r.get('success', False))
            self.logger.info(f"Crawling stage completed: {successful_crawls}/{len(urls)} successful")

            self.progress_tracker.complete_task('crawling')
            return extracted_contents

        except Exception as e:
            self.logger.error(f"Error in crawling stage: {str(e)}")
            self.progress_tracker.complete_task('crawling')
            raise

    def run_chunking_embedding_stage(
        self,
        crawled_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run the chunking and embedding stage.

        Args:
            crawled_results: Results from crawling stage

        Returns:
            List of embedding results
        """
        self.logger.info(f"Starting chunking and embedding stage for {len(crawled_results)} documents")
        self.progress_tracker.start_task('chunking_embedding', total_items=len(crawled_results))

        try:
            # Filter successful crawling results
            successful_docs = [
                {
                    'content': r['content'],
                    'source_url': r['url'],
                    'page_title': r['title']
                }
                for r in crawled_results
                if r.get('success', False) and r.get('content', '').strip()
            ]

            if not successful_docs:
                self.logger.warning("No successful crawling results to process")
                return []

            # Run the complete pipeline
            pipeline_result = self.chunking_pipeline.run_complete_pipeline(
                documents=successful_docs,
                validate_embeddings=True
            )

            if not pipeline_result.get('success', False):
                self.logger.error(f"Chunking and embedding pipeline failed: {pipeline_result.get('error', 'Unknown error')}")
                return []

            embedding_vectors = pipeline_result.get('embedding_vectors', [])
            self.logger.info(f"Chunking and embedding stage completed: {len(embedding_vectors)} vectors generated")

            self.progress_tracker.complete_task('chunking_embedding')
            return embedding_vectors

        except Exception as e:
            self.logger.error(f"Error in chunking and embedding stage: {str(e)}")
            self.progress_tracker.complete_task('chunking_embedding')
            raise

    def run_storage_stage(
        self,
        embedding_vectors: List[Any],
        metadata_list: List[Dict[str, Any]],
        batch_size: int = 64
    ) -> List[Dict[str, Any]]:
        """
        Run the storage stage to store embeddings in Qdrant.

        Args:
            embedding_vectors: List of embedding vectors to store
            metadata_list: Corresponding metadata for each embedding
            batch_size: Batch size for storage operations

        Returns:
            List of storage results
        """
        self.logger.info(f"Starting storage stage for {len(embedding_vectors)} embeddings")
        self.progress_tracker.start_task('storage', total_items=len(embedding_vectors))

        try:
            # Initialize storage components if not done already
            self._initialize_storage_components()

            # Ensure collection exists
            if len(embedding_vectors) > 0:
                first_vector = embedding_vectors[0]
                vector_size = len(first_vector.vector) if hasattr(first_vector, 'vector') else len(first_vector)
                self.storage.ensure_collection_exists(vector_size=vector_size)

            # Store embeddings
            storage_result = self.storage.store_embeddings(
                embedding_vectors=embedding_vectors,
                metadata_list=metadata_list,
                batch_size=batch_size
            )

            storage_results = [storage_result]  # Wrap in list for consistency
            successful_stores = storage_result.get('stored_count', 0)

            self.logger.info(f"Storage stage completed: {successful_stores}/{len(embedding_vectors)} stored successfully")

            self.progress_tracker.complete_task('storage')
            return storage_results

        except Exception as e:
            self.logger.error(f"Error in storage stage: {str(e)}")
            self.progress_tracker.complete_task('storage')
            raise

    def run_complete_pipeline(
        self,
        urls: List[str],
        validate_results: bool = True,
        test_queries: Optional[List[str]] = None,
        max_concurrent_crawling: int = 5,
        storage_batch_size: int = 64
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline: crawling → chunking → embedding → storage.

        Args:
            urls: List of URLs to process
            validate_results: Whether to validate results against success criteria
            test_queries: Optional test queries for relevance validation
            max_concurrent_crawling: Max concurrent requests for crawling
            storage_batch_size: Batch size for storage operations

        Returns:
            Dictionary with complete pipeline results
        """
        start_time = time.time()
        self.logger.info(f"Starting complete book embedding pipeline for {len(urls)} URLs")

        try:
            # Stage 1: Crawling
            crawled_results = self.run_crawling_stage(
                urls,
                max_concurrent=max_concurrent_crawling
            )

            # Prepare metadata for successful crawls
            successful_crawls = [
                r for r in crawled_results
                if r.get('success', False) and r.get('content', '').strip()
            ]

            if not successful_crawls:
                self.logger.error("No successful crawls to process further")
                return {
                    'success': False,
                    'crawling_results': crawled_results,
                    'chunking_results': [],
                    'storage_results': [],
                    'total_time': time.time() - start_time,
                    'message': 'No successful crawls to process'
                }

            # Stage 2: Chunking and Embedding
            embedding_vectors = self.run_chunking_embedding_stage(crawled_results)

            if not embedding_vectors:
                self.logger.error("No embeddings generated to store")
                return {
                    'success': False,
                    'crawling_results': crawled_results,
                    'chunking_results': [],
                    'storage_results': [],
                    'total_time': time.time() - start_time,
                    'message': 'No embeddings generated'
                }

            # Prepare metadata for storage
            metadata_list = []
            for i, emb_vector in enumerate(embedding_vectors):
                # Find corresponding source content
                source_idx = i % len(successful_crawls)  # Simple mapping
                source_data = successful_crawls[source_idx]

                metadata = {
                    'content': source_data.get('content', '')[:500],  # Truncate for storage
                    'source_url': source_data.get('url', ''),
                    'page_title': source_data.get('title', ''),
                    'chunk_order': getattr(emb_vector, 'chunk_order', 0) if hasattr(emb_vector, 'chunk_order') else 0,
                    'chunk_id': getattr(emb_vector, 'chunk_id', f'chunk_{i}') if hasattr(emb_vector, 'chunk_id') else f'chunk_{i}',
                    'timestamp': datetime.utcnow().isoformat()
                }
                metadata_list.append(metadata)

            # Stage 3: Storage
            storage_results = self.run_storage_stage(
                embedding_vectors,
                metadata_list,
                batch_size=storage_batch_size
            )

            # Collect metrics
            pipeline_metrics = self.progress_tracker.get_all_metrics()

            # Prepare result
            result = {
                'success': True,
                'crawling_results': crawled_results,
                'chunking_results': embedding_vectors,
                'storage_results': storage_results,
                'total_time': time.time() - start_time,
                'pipeline_metrics': {k: v.__dict__ for k, v in pipeline_metrics.items()},
                'message': f'Pipeline completed successfully in {time.time() - start_time:.2f} seconds'
            }

            self.logger.info(result['message'])

            # Validate results if requested
            if validate_results and self.storage and len(embedding_vectors) > 0:
                self.logger.info("Starting validation of pipeline results...")

                validation_result = validate_complete_storage_criteria(
                    storage=self.storage,
                    search=self.search,
                    storage_results=storage_results,
                    test_queries=test_queries or ["test query", "sample search"],
                    expected_storage_count=len(embedding_vectors)
                )

                result['validation_result'] = validation_result
                self.logger.info(f"Validation result: {validation_result['message']}")

            return result

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"Pipeline failed after {error_time:.2f} seconds: {str(e)}")

            return {
                'success': False,
                'error': str(e),
                'total_time': error_time,
                'message': f'Pipeline failed: {str(e)}'
            }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the current status of the pipeline.

        Returns:
            Dictionary with pipeline status information
        """
        metrics = self.progress_tracker.get_all_metrics()

        return {
            'components_initialized': {
                'crawler': self.crawler is not None,
                'content_extractor': self.content_extractor is not None,
                'chunking_pipeline': self.chunking_pipeline is not None,
                'storage': self.storage is not None,
                'search': self.search is not None
            },
            'current_metrics': {k: v.__dict__ for k, v in metrics.items()},
            'config_validated': True  # Assuming config was validated in __init__
        }