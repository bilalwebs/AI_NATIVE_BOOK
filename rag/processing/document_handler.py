from typing import List, Dict, Any, Optional
from rag.processing.chunker import TextChunker
from rag.data_models import DocumentChunk
import logging


class DocumentHandler:
    """
    Class to handle large documents that may exceed model limits.
    """
    def __init__(
        self,
        chunker: TextChunker,
        max_content_length: int = 20000,  # Approximate max for most embedding models
        logger: logging.Logger = None
    ):
        """
        Initialize the document handler.

        Args:
            chunker: TextChunker instance to use for chunking
            max_content_length: Maximum content length before pre-processing
            logger: Logger instance for logging
        """
        self.chunker = chunker
        self.max_content_length = max_content_length
        self.logger = logger or logging.getLogger(__name__)

    def preprocess_large_content(
        self,
        content: str,
        max_length: Optional[int] = None
    ) -> str:
        """
        Preprocess large content to make it more suitable for chunking.
        This might involve summarization, cleaning, or other techniques.

        Args:
            content: Content to preprocess
            max_length: Maximum length to aim for (defaults to self.max_content_length)

        Returns:
            Preprocessed content
        """
        if max_length is None:
            max_length = self.max_content_length

        if len(content) <= max_length:
            return content

        # For now, we'll just truncate content with a marker
        # In a more sophisticated implementation, you might:
        # - Use summarization techniques
        # - Remove repetitive content
        # - Extract key sections only
        truncated_content = content[:max_length]

        if self.logger:
            self.logger.warning(
                f"Content truncated from {len(content)} to {len(truncated_content)} characters. "
                f"Original content exceeded maximum length of {max_length}."
            )

        return truncated_content

    def handle_large_document(
        self,
        content: str,
        source_url: str,
        page_title: str = "",
        chunk_method: str = "size"
    ) -> List[DocumentChunk]:
        """
        Handle a potentially large document by preprocessing and chunking.

        Args:
            content: Document content to process
            source_url: Source URL for the document
            page_title: Title of the source page
            chunk_method: Chunking method to use

        Returns:
            List of DocumentChunk objects
        """
        if not content:
            return []

        # Preprocess if content is too large
        processed_content = self.preprocess_large_content(content)

        # Chunk the processed content
        chunks = self.chunker.chunk_text(
            processed_content,
            source_url,
            page_title,
            method=chunk_method
        )

        if self.logger and len(content) > len(processed_content):
            self.logger.info(
                f"Large document ({len(content)} chars) processed into {len(chunks)} chunks. "
                f"Content was truncated to {len(processed_content)} chars."
            )

        return chunks

    def handle_multiple_documents(
        self,
        documents: List[Dict[str, str]],
        chunk_method: str = "size"
    ) -> List[DocumentChunk]:
        """
        Handle multiple documents at once.

        Args:
            documents: List of documents, each with 'content', 'source_url', and 'page_title' keys
            chunk_method: Chunking method to use

        Returns:
            List of DocumentChunk objects from all documents
        """
        all_chunks = []

        for i, doc in enumerate(documents):
            content = doc.get('content', '')
            source_url = doc.get('source_url', '')
            page_title = doc.get('page_title', '')

            if not content:
                if self.logger:
                    self.logger.warning(f"Document {i} has no content, skipping")
                continue

            if not source_url:
                if self.logger:
                    self.logger.warning(f"Document {i} has no source_url, skipping")
                continue

            try:
                doc_chunks = self.handle_large_document(
                    content,
                    source_url,
                    page_title,
                    chunk_method
                )
                all_chunks.extend(doc_chunks)

                if self.logger:
                    self.logger.info(f"Processed document {i}: {len(doc_chunks)} chunks generated from {len(content)} chars")

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error processing document {i} ({source_url}): {str(e)}")
                continue  # Continue with other documents

        return all_chunks

    def validate_document_chunks(
        self,
        chunks: List[DocumentChunk],
        max_chunk_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate that document chunks meet requirements.

        Args:
            chunks: List of DocumentChunk objects to validate
            max_chunk_size: Maximum allowed chunk size (defaults to chunker's size)

        Returns:
            Dictionary with validation results
        """
        if max_chunk_size is None:
            max_chunk_size = self.chunker.chunk_size

        results = {
            'total_chunks': len(chunks),
            'valid_chunks': 0,
            'invalid_chunks': 0,
            'chunks_with_issues': [],
            'size_issues': [],
            'content_issues': []
        }

        for i, chunk in enumerate(chunks):
            is_valid = True
            chunk_issues = []

            # Check content size
            content_size = len(chunk.content)
            if content_size > max_chunk_size:
                is_valid = False
                issue = f"Chunk {i} exceeds max size: {content_size} > {max_chunk_size}"
                results['size_issues'].append(issue)
                chunk_issues.append(issue)

            # Check for empty content
            if not chunk.content or not chunk.content.strip():
                is_valid = False
                issue = f"Chunk {i} has empty content"
                results['content_issues'].append(issue)
                chunk_issues.append(issue)

            # Add to appropriate counter
            if is_valid:
                results['valid_chunks'] += 1
            else:
                results['invalid_chunks'] += 1
                results['chunks_with_issues'].append({
                    'chunk_id': chunk.chunk_id,
                    'index': i,
                    'issues': chunk_issues
                })

        results['validation_passed'] = results['invalid_chunks'] == 0
        results['valid_ratio'] = results['valid_chunks'] / len(chunks) if chunks else 0

        return results

    def optimize_chunks_for_embedding(
        self,
        chunks: List[DocumentChunk],
        target_size: Optional[int] = None
    ) -> List[DocumentChunk]:
        """
        Optimize chunks for embedding generation by adjusting sizes if needed.

        Args:
            chunks: List of DocumentChunk objects to optimize
            target_size: Target chunk size for embeddings

        Returns:
            List of optimized DocumentChunk objects
        """
        if target_size is None:
            target_size = self.chunker.chunk_size

        # For now, we'll just return the chunks as they are
        # In a more sophisticated implementation, you might:
        # - Merge very small chunks
        # - Re-chunk oversized chunks
        # - Adjust for specific model requirements

        # However, let's implement basic optimization by merging small chunks
        optimized_chunks = self.chunker.merge_small_chunks(chunks, target_size)

        if self.logger:
            self.logger.info(
                f"Optimized chunks from {len(chunks)} to {len(optimized_chunks)} "
                f"for embedding (target size: {target_size})"
            )

        return optimized_chunks

    def get_document_statistics(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Get statistics about processed documents.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            Dictionary with document statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_documents': 0,
                'unique_sources': 0,
                'avg_chunk_size': 0,
                'total_content_chars': 0
            }

        # Count unique source documents
        unique_sources = set(chunk.source_url for chunk in chunks)

        # Calculate statistics
        content_lengths = [len(chunk.content) for chunk in chunks]
        total_content = sum(content_lengths)

        return {
            'total_chunks': len(chunks),
            'total_documents': len(unique_sources),  # Approximation based on unique URLs
            'unique_sources': len(unique_sources),
            'avg_chunk_size': total_content / len(chunks) if chunks else 0,
            'total_content_chars': total_content,
            'min_chunk_size': min(content_lengths) if content_lengths else 0,
            'max_chunk_size': max(content_lengths) if content_lengths else 0
        }