from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime
import asyncio
from rag.crawling.url_crawler import URLCrawler
from rag.crawling.content_extractor import ContentExtractor
from rag.processing.chunker import TextChunker
from rag.processing.embedding_client import CohereEmbeddingClient
from rag.storage.qdrant_storage import QdrantStorage
from rag.storage.qdrant_schema import QdrantSchema
from rag.config.config import Config
from rag.utils.metrics import ProgressTracker
from rag.data_models import DocumentChunk, EmbeddingVector
from qdrant_client import QdrantClient


class PipelineOrchestrator:
    """
    Main orchestrator that connects crawling → chunking → embedding → storage
    """
    def __init__(self, config: Config = None, logger: logging.Logger = None):
        """
        Initialize the pipeline orchestrator with all required components.

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config or Config()
        self.logger = logger or logging.getLogger(__name__)
        self.progress_tracker = ProgressTracker(logger=self.logger)

        # Initialize components
        self.crawler = URLCrawler(
            delay=self.config.REQUEST_DELAY,
            timeout=self.config.REQUEST_TIMEOUT,
            max_retries=self.config.MAX_RETRIES,
            logger=self.logger
        )
        self.content_extractor = ContentExtractor(logger=self.logger)
        self.chunker = TextChunker(
            chunk_size=self.config.CHUNK_SIZE,
            overlap=self.config.CHUNK_OVERLAP,
            logger=self.logger
        )
        self.embedding_client = CohereEmbeddingClient(
            api_key=self.config.COHERE_API_KEY,
            model_name=self.config.COHERE_MODEL,
            logger=self.logger
        )

        # Initialize Qdrant client and storage
        self.qdrant_client = QdrantClient(
            url=self.config.QDRANT_URL,
            api_key=self.config.QDRANT_API_KEY,
            timeout=30
        )
        self.schema = QdrantSchema()
        self.storage = QdrantStorage(
            client=self.qdrant_client,
            schema=self.schema,
            collection_name="book_embeddings",
            logger=self.logger
        )

    def run_pipeline(
        self,
        urls: List[str],
        collection_name: str = "book_embeddings",
        recreate_collection: bool = False
    ) -> Dict[str, Any]:
        """
        Execute the complete pipeline from crawling to storage.

        Args:
            urls: List of URLs to process
            collection_name: Name of the Qdrant collection
            recreate_collection: Whether to recreate the collection

        Returns:
            Dictionary with pipeline execution results
        """
        start_time = time.time()
        self.logger.info(f"Starting pipeline execution for {len(urls)} URLs")

        try:
            # Update storage collection name
            self.storage.collection_name = collection_name

            # Step 1: Crawl and extract content
            self.logger.info("Step 1: Crawling and extracting content...")
            crawled_data = self._crawl_urls(urls)

            if not crawled_data:
                self.logger.error("No content was successfully crawled")
                return {
                    'success': False,
                    'message': 'No content crawled successfully',
                    'total_urls': len(urls),
                    'crawled_count': 0,
                    'processed_count': 0,
                    'execution_time': time.time() - start_time
                }

            # Step 2: Process content (chunking)
            self.logger.info("Step 2: Processing content (chunking)...")
            chunks = self._process_content(crawled_data)

            if not chunks:
                self.logger.error("No content was successfully processed into chunks")
                return {
                    'success': False,
                    'message': 'No content processed into chunks successfully',
                    'total_urls': len(urls),
                    'crawled_count': len(crawled_data),
                    'processed_count': 0,
                    'execution_time': time.time() - start_time
                }

            # Step 3: Generate embeddings
            self.logger.info("Step 3: Generating embeddings...")
            embeddings, metadata_list = self._generate_embeddings(chunks)

            if not embeddings:
                self.logger.error("No embeddings were successfully generated")
                return {
                    'success': False,
                    'message': 'No embeddings generated successfully',
                    'total_urls': len(urls),
                    'crawled_count': len(crawled_data),
                    'processed_count': len(chunks),
                    'embedded_count': 0,
                    'execution_time': time.time() - start_time
                }

            # Step 4: Store embeddings
            self.logger.info("Step 4: Storing embeddings...")
            storage_result = self._store_embeddings(
                embeddings,
                metadata_list,
                recreate_collection=recreate_collection
            )

            total_time = time.time() - start_time
            self.logger.info(f"Pipeline completed in {total_time:.2f} seconds")

            return {
                'success': True,
                'total_urls': len(urls),
                'crawled_count': len(crawled_data),
                'processed_count': len(chunks),
                'embedded_count': len(embeddings),
                'storage_result': storage_result,
                'execution_time': total_time,
                'message': f'Successfully processed {len(embeddings)} embeddings from {len(urls)} URLs'
            }

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time,
                'message': f'Pipeline execution failed: {str(e)}'
            }

    def _crawl_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Crawl the provided URLs and extract content.

        Args:
            urls: List of URLs to crawl

        Returns:
            List of crawled data dictionaries
        """
        crawled_data = []
        total_urls = len(urls)

        self.progress_tracker.start_task('crawling', total_items=total_urls)

        for i, url in enumerate(urls):
            try:
                self.logger.info(f"Crawling URL {i+1}/{total_urls}: {url}")

                # Crawl the URL
                crawl_result = self.crawler.crawl_url(url)

                if crawl_result and crawl_result.get('success'):
                    # Extract content from the crawled HTML
                    content_result = self.content_extractor.extract_content(
                        html_content=crawl_result['html'],
                        source_url=url
                    )

                    if content_result and content_result.get('success'):
                        crawled_item = {
                            'url': url,
                            'title': content_result.get('title', ''),
                            'content': content_result.get('content', ''),
                            'metadata': content_result.get('metadata', {}),
                            'crawled_at': datetime.now().isoformat()
                        }
                        crawled_data.append(crawled_item)
                        self.progress_tracker.update_progress('crawling', successful=True)

                        self.logger.info(f"Successfully crawled and extracted content from {url}")
                    else:
                        self.logger.warning(f"Failed to extract content from {url}")
                        self.progress_tracker.update_progress('crawling', successful=False)
                else:
                    self.logger.warning(f"Failed to crawl {url}")
                    self.progress_tracker.update_progress('crawling', successful=False)

            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {str(e)}")
                self.progress_tracker.update_progress('crawling', successful=False)

        self.progress_tracker.complete_task('crawling')
        self.logger.info(f"Crawling completed: {len(crawled_data)}/{total_urls} URLs processed successfully")

        return crawled_data

    def _process_content(self, crawled_data: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """
        Process crawled content by chunking it.

        Args:
            crawled_data: List of crawled data dictionaries

        Returns:
            List of DocumentChunk objects
        """
        all_chunks = []
        total_items = len(crawled_data)

        self.progress_tracker.start_task('chunking', total_items=total_items)

        for i, data in enumerate(crawled_data):
            try:
                self.logger.info(f"Processing content {i+1}/{total_items} from {data['url']}")

                # Create document chunks from the content
                content = data['content']
                source_url = data['url']
                title = data.get('title', '')

                chunks = self.chunker.chunk_text(
                    text=content,
                    source_url=source_url,
                    title=title
                )

                if chunks:
                    all_chunks.extend(chunks)
                    self.progress_tracker.update_progress('chunking', successful=True, increment=len(chunks))

                    self.logger.info(f"Created {len(chunks)} chunks from {source_url}")
                else:
                    self.logger.warning(f"No chunks created from {source_url}")
                    self.progress_tracker.update_progress('chunking', successful=False)

            except Exception as e:
                self.logger.error(f"Error processing content from {data['url']}: {str(e)}")
                self.progress_tracker.update_progress('chunking', successful=False)

        self.progress_tracker.complete_task('chunking')
        self.logger.info(f"Chunking completed: {len(all_chunks)} chunks created from {total_items} documents")

        return all_chunks

    def _generate_embeddings(self, chunks: List[DocumentChunk]) -> tuple[List[EmbeddingVector], List[Dict[str, Any]]]:
        """
        Generate embeddings for the provided chunks.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            Tuple of (embedding_vectors, metadata_list)
        """
        embedding_vectors = []
        metadata_list = []
        total_chunks = len(chunks)

        self.progress_tracker.start_task('embedding', total_items=total_chunks)

        # Process in batches to be more efficient
        batch_size = 32  # Cohere's recommended batch size

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            self.logger.info(f"Processing embedding batch {i//batch_size + 1}/{(total_chunks-1)//batch_size + 1}")

            try:
                # Extract text content from chunks for embedding
                texts = [chunk.content for chunk in batch]

                # Generate embeddings for the batch
                embeddings = self.embedding_client.embed_texts(texts)

                if embeddings and len(embeddings) == len(batch):
                    # Create EmbeddingVector objects and metadata
                    for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                        embedding_vector = EmbeddingVector(
                            vector=embedding,
                            chunk_id=chunk.chunk_id,
                            source_url=chunk.source_url,
                            title=chunk.title
                        )
                        embedding_vectors.append(embedding_vector)

                        # Create metadata for storage
                        metadata = {
                            'content': chunk.content,
                            'source_url': chunk.source_url,
                            'page_title': chunk.title,
                            'chunk_order': chunk.chunk_order,
                            'chunk_id': chunk.chunk_id,
                            'created_at': chunk.created_at
                        }
                        metadata_list.append(metadata)

                    self.progress_tracker.update_progress('embedding', successful=True, increment=len(batch))
                    self.logger.info(f"Generated embeddings for batch of {len(batch)} chunks")
                else:
                    self.logger.warning(f"Embedding generation failed for batch starting at {i}")
                    self.progress_tracker.update_progress('embedding', successful=False, increment=len(batch))

            except Exception as e:
                self.logger.error(f"Error generating embeddings for batch starting at {i}: {str(e)}")
                self.progress_tracker.update_progress('embedding', successful=False, increment=len(batch))

        self.progress_tracker.complete_task('embedding')
        self.logger.info(f"Embedding generation completed: {len(embedding_vectors)}/{total_chunks} chunks processed")

        return embedding_vectors, metadata_list

    def _store_embeddings(
        self,
        embedding_vectors: List[EmbeddingVector],
        metadata_list: List[Dict[str, Any]],
        recreate_collection: bool = False
    ) -> Dict[str, Any]:
        """
        Store embeddings in Qdrant Cloud.

        Args:
            embedding_vectors: List of EmbeddingVector objects
            metadata_list: List of metadata dictionaries
            recreate_collection: Whether to recreate the collection

        Returns:
            Storage result dictionary
        """
        # Ensure the collection exists
        if embedding_vectors:
            vector_size = len(embedding_vectors[0].vector)
            self.storage.ensure_collection_exists(
                vector_size=vector_size,
                recreate=recreate_collection
            )

        # Store the embeddings
        storage_result = self.storage.store_embeddings(
            embedding_vectors=embedding_vectors,
            metadata_list=metadata_list
        )

        return storage_result

    def validate_pipeline(self, test_urls: List[str]) -> Dict[str, Any]:
        """
        Validate the complete pipeline with test URLs.

        Args:
            test_urls: List of test URLs to validate the pipeline

        Returns:
            Dictionary with validation results
        """
        self.logger.info(f"Validating pipeline with {len(test_urls)} test URLs")

        # Run the pipeline
        result = self.run_pipeline(test_urls)

        # Additional validation checks
        validation_results = {
            'pipeline_result': result,
            'validation_passed': result.get('success', False),
            'validation_details': {}
        }

        # Check if we have reasonable success rates
        if result.get('success'):
            total_urls = result.get('total_urls', 0)
            crawled_count = result.get('crawled_count', 0)
            embedded_count = result.get('embedded_count', 0)

            if total_urls > 0:
                crawl_success_rate = crawled_count / total_urls
                validation_results['validation_details']['crawl_success_rate'] = crawl_success_rate

                if crawl_success_rate >= 0.95:  # 95% success rate as per spec
                    validation_results['validation_details']['crawl_success_passed'] = True
                else:
                    validation_results['validation_details']['crawl_success_passed'] = False

            # Check embedding success
            if crawled_count > 0:
                embedding_success_rate = embedded_count / crawled_count
                validation_results['validation_details']['embedding_success_rate'] = embedding_success_rate

                if embedding_success_rate >= 0.99:  # 99% success rate as per spec
                    validation_results['validation_details']['embedding_success_passed'] = True
                else:
                    validation_results['validation_details']['embedding_success_passed'] = False

        self.logger.info(f"Pipeline validation completed: {'PASSED' if validation_results['validation_passed'] else 'FAILED'}")

        return validation_results

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the pipeline execution.

        Returns:
            Dictionary with pipeline statistics
        """
        return {
            'components': {
                'crawler': self.crawler.__class__.__name__,
                'content_extractor': self.content_extractor.__class__.__name__,
                'chunker': self.chunker.__class__.__name__,
                'embedding_client': self.embedding_client.__class__.__name__,
                'storage': self.storage.__class__.__name__
            },
            'config': {
                'chunk_size': self.config.CHUNK_SIZE,
                'chunk_overlap': self.config.CHUNK_OVERLAP,
                'cohere_model': self.config.COHERE_MODEL,
                'collection_name': self.storage.collection_name
            },
            'progress_tracker': self.progress_tracker.get_all_stats()
        }