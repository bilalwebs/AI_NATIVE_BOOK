from typing import List, Dict, Any, Optional
import logging
from rag.processing.chunker import TextChunker
from rag.processing.embedding_client import CohereEmbeddingClient
from rag.processing.document_handler import DocumentHandler
from rag.data_models import DocumentChunk, EmbeddingVector
from rag.utils.metrics import ProgressTracker, ProcessingMetrics
from rag.config import Config


class ChunkingEmbeddingPipeline:
    """
    Pipeline that integrates chunking and embedding generation.
    """
    def __init__(
        self,
        chunker: TextChunker = None,
        embedding_client: CohereEmbeddingClient = None,
        document_handler: DocumentHandler = None,
        logger: logging.Logger = None
    ):
        """
        Initialize the chunking and embedding pipeline.

        Args:
            chunker: TextChunker instance (creates default if None)
            embedding_client: CohereEmbeddingClient instance (creates default if None)
            document_handler: DocumentHandler instance (creates default if None)
            logger: Logger instance for logging
        """
        self.chunker = chunker or TextChunker(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        self.embedding_client = embedding_client or CohereEmbeddingClient()
        self.document_handler = document_handler or DocumentHandler(self.chunker)
        self.logger = logger or logging.getLogger(__name__)
        self.progress_tracker = ProgressTracker(logger=self.logger)

    def process_single_document(
        self,
        content: str,
        source_url: str,
        page_title: str = "",
        chunk_method: str = "size"
    ) -> List[EmbeddingVector]:
        """
        Process a single document through the chunking and embedding pipeline.

        Args:
            content: Document content to process
            source_url: Source URL for the document
            page_title: Title of the source page
            chunk_method: Chunking method to use

        Returns:
            List of EmbeddingVector objects
        """
        if not content:
            if self.logger:
                self.logger.warning(f"No content to process for URL: {source_url}")
            return []

        try:
            # Step 1: Handle large documents and chunk them
            chunks = self.document_handler.handle_large_document(
                content,
                source_url,
                page_title,
                chunk_method
            )

            if not chunks:
                if self.logger:
                    self.logger.warning(f"No chunks generated for URL: {source_url}")
                return []

            # Step 2: Optimize chunks for embedding
            optimized_chunks = self.document_handler.optimize_chunks_for_embedding(chunks)

            if self.logger:
                self.logger.info(f"Generated {len(optimized_chunks)} optimized chunks for {source_url}")

            # Step 3: Generate embeddings for all chunks
            embedding_vectors = self.embedding_client.embed_document_chunks(optimized_chunks)

            if self.logger:
                self.logger.info(f"Generated embeddings for {len(embedding_vectors)} chunks from {source_url}")

            return embedding_vectors

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing document {source_url}: {str(e)}")
            raise

    def process_multiple_documents(
        self,
        documents: List[Dict[str, str]],
        chunk_method: str = "size",
        batch_size: Optional[int] = None
    ) -> List[EmbeddingVector]:
        """
        Process multiple documents through the chunking and embedding pipeline.

        Args:
            documents: List of documents, each with 'content', 'source_url', and 'page_title' keys
            chunk_method: Chunking method to use
            batch_size: Batch size for embedding generation

        Returns:
            List of EmbeddingVector objects from all documents
        """
        all_embedding_vectors = []
        total_docs = len(documents)

        self.progress_tracker.start_task('document_processing', total_items=total_docs)

        for i, doc in enumerate(documents):
            try:
                content = doc.get('content', '')
                source_url = doc.get('source_url', '')
                page_title = doc.get('page_title', '')

                if not content or not source_url:
                    if self.logger:
                        self.logger.warning(f"Skipping document {i} due to missing content or URL")
                    self.progress_tracker.update_progress('document_processing', successful=False)
                    continue

                # Process single document
                doc_embeddings = self.process_single_document(
                    content,
                    source_url,
                    page_title,
                    chunk_method
                )

                all_embedding_vectors.extend(doc_embeddings)

                if self.logger:
                    self.logger.info(f"Completed document {i+1}/{total_docs}: {len(doc_embeddings)} embeddings")

                self.progress_tracker.update_progress('document_processing', successful=True)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error processing document {i} ({doc.get('source_url', 'unknown')}): {str(e)}")
                self.progress_tracker.update_progress('document_processing', successful=False)

        self.progress_tracker.complete_task('document_processing')

        return all_embedding_vectors

    def process_raw_content_list(
        self,
        content_list: List[str],
        source_urls: List[str],
        page_titles: Optional[List[str]] = None,
        chunk_method: str = "size"
    ) -> List[EmbeddingVector]:
        """
        Process a list of raw content strings with corresponding metadata.

        Args:
            content_list: List of content strings to process
            source_urls: List of source URLs (must match content_list length)
            page_titles: List of page titles (optional, defaults to empty strings)
            chunk_method: Chunking method to use

        Returns:
            List of EmbeddingVector objects
        """
        if len(content_list) != len(source_urls):
            raise ValueError("content_list and source_urls must have the same length")

        if page_titles is None:
            page_titles = [""] * len(content_list)
        elif len(page_titles) != len(content_list):
            raise ValueError("If provided, page_titles must have the same length as content_list")

        # Create documents list
        documents = []
        for content, url, title in zip(content_list, source_urls, page_titles):
            documents.append({
                'content': content,
                'source_url': url,
                'page_title': title
            })

        return self.process_multiple_documents(documents, chunk_method)

    def get_pipeline_metrics(self) -> Dict[str, ProcessingMetrics]:
        """
        Get metrics for the pipeline execution.

        Returns:
            Dictionary with processing metrics
        """
        return self.progress_tracker.get_all_metrics()

    def validate_embeddings(
        self,
        embedding_vectors: List[EmbeddingVector],
        expected_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate the generated embeddings.

        Args:
            embedding_vectors: List of EmbeddingVector objects to validate
            expected_model: Expected model name (optional)

        Returns:
            Dictionary with validation results
        """
        if not embedding_vectors:
            return {
                'valid': False,
                'total_embeddings': 0,
                'valid_embeddings': 0,
                'invalid_embeddings': 0,
                'message': 'No embeddings to validate'
            }

        total_embeddings = len(embedding_vectors)
        valid_embeddings = 0
        invalid_details = []

        for i, emb in enumerate(embedding_vectors):
            is_valid = True
            issues = []

            # Check if vector is empty
            if not emb.vector:
                is_valid = False
                issues.append("Empty vector")

            # Check if vector has reasonable size
            if emb.vector and len(emb.vector) == 0:
                is_valid = False
                issues.append("Vector with zero length")

            # Check model matches expected
            if expected_model and emb.model != expected_model:
                issues.append(f"Model mismatch: expected {expected_model}, got {emb.model}")

            if is_valid:
                valid_embeddings += 1
            else:
                invalid_details.append({
                    'index': i,
                    'embedding_id': emb.embedding_id,
                    'issues': issues
                })

        valid_ratio = valid_embeddings / total_embeddings if total_embeddings > 0 else 0
        is_valid_overall = valid_ratio >= 0.99  # 99% threshold as per spec

        result = {
            'valid': is_valid_overall,
            'total_embeddings': total_embeddings,
            'valid_embeddings': valid_embeddings,
            'invalid_embeddings': total_embeddings - valid_embeddings,
            'valid_ratio': valid_ratio,
            'required_ratio': 0.99,
            'invalid_details': invalid_details,
            'message': f"Validation: {valid_embeddings}/{total_embeddings} embeddings valid ({valid_ratio:.2%})"
        }

        if self.logger:
            log_level = logging.INFO if result['valid'] else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result

    def run_complete_pipeline(
        self,
        documents: List[Dict[str, str]],
        chunk_method: str = "size",
        validate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete chunking and embedding pipeline.

        Args:
            documents: List of documents to process
            chunk_method: Chunking method to use
            validate_embeddings: Whether to validate embeddings after generation

        Returns:
            Dictionary with pipeline results and metrics
        """
        start_time = __import__('time').time()

        try:
            # Process all documents
            embedding_vectors = self.process_multiple_documents(documents, chunk_method)

            # Get pipeline metrics
            metrics = self.get_pipeline_metrics()

            # Validate embeddings if requested
            validation_result = None
            if validate_embeddings and embedding_vectors:
                validation_result = self.validate_embeddings(
                    embedding_vectors,
                    expected_model=self.embedding_client.model
                )

            total_time = __import__('time').time() - start_time

            result = {
                'embedding_vectors': embedding_vectors,
                'total_embeddings_generated': len(embedding_vectors),
                'pipeline_metrics': {k: v.__dict__ for k, v in metrics.items()},
                'validation_result': validation_result,
                'total_processing_time': total_time,
                'success': True
            }

            if self.logger:
                self.logger.info(
                    f"Pipeline completed: {len(embedding_vectors)} embeddings generated "
                    f"in {total_time:.2f} seconds"
                )

            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"Pipeline failed: {str(e)}")

            return {
                'embedding_vectors': [],
                'total_embeddings_generated': 0,
                'pipeline_metrics': {},
                'validation_result': None,
                'total_processing_time': __import__('time').time() - start_time,
                'success': False,
                'error': str(e)
            }