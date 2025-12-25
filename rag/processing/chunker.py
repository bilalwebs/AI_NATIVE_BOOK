from typing import List, Dict, Any, Optional
import re
from rag.data_models import DocumentChunk
import uuid


class TextChunker:
    """
    Utility class for chunking text content into appropriately sized segments.
    """
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 10
    ):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Maximum size of each chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size of a chunk to be included
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_by_size(self, text: str, source_url: str, page_title: str = "") -> List[DocumentChunk]:
        """
        Chunk text by size with overlap.

        Args:
            text: Text to chunk
            source_url: Source URL for the text
            page_title: Title of the source page

        Returns:
            List of DocumentChunk objects
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            return []

        chunks = []
        start_idx = 0
        chunk_order = 0

        while start_idx < len(text):
            # Determine the end index for this chunk
            end_idx = start_idx + self.chunk_size

            # If this is not the last chunk, try to break at a sentence or paragraph boundary
            if end_idx < len(text):
                # Look for a good breaking point near the end of the chunk
                search_start = end_idx - self.chunk_overlap
                break_point = end_idx

                # Look for sentence endings
                for i in range(min(end_idx, len(text)) - 1, search_start, -1):
                    if text[i] in '.!?':
                        break_point = i + 1
                        break
                else:
                    # If no sentence ending found, look for paragraph breaks
                    for i in range(min(end_idx, len(text)) - 1, search_start, -1):
                        if text[i] == '\n' and i + 1 < len(text) and text[i + 1] == '\n':
                            break_point = i + 2
                            break
                    else:
                        # If no good break point found, just use the max chunk size
                        break_point = end_idx

                end_idx = break_point

            # Extract the chunk content
            chunk_content = text[start_idx:end_idx]

            # Create a DocumentChunk object
            chunk = DocumentChunk(
                chunk_id=f"{hash(source_url)}_{chunk_order}_{uuid.uuid4().hex[:8]}",
                content=chunk_content,
                source_url=source_url,
                page_title=page_title,
                chunk_order=chunk_order,
                metadata={
                    'original_length': len(text),
                    'chunk_start_idx': start_idx,
                    'chunk_end_idx': end_idx,
                    'chunk_size': len(chunk_content)
                }
            )

            # Only add chunk if it meets minimum size requirement
            if len(chunk_content) >= self.min_chunk_size:
                chunks.append(chunk)

            # Update start index for next chunk (with overlap)
            start_idx = end_idx - self.chunk_overlap if self.chunk_overlap < end_idx else end_idx
            chunk_order += 1

            # Prevent infinite loop
            if start_idx >= len(text):
                break

        return chunks

    def chunk_by_paragraph(self, text: str, source_url: str, page_title: str = "") -> List[DocumentChunk]:
        """
        Chunk text by paragraphs, falling back to size-based chunking if paragraphs are too large.

        Args:
            text: Text to chunk
            source_url: Source URL for the text
            page_title: Title of the source page

        Returns:
            List of DocumentChunk objects
        """
        if not text:
            return []

        # Split by paragraphs (multiple newlines)
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        chunk_order = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If paragraph is too large, chunk it by size
            if len(paragraph) > self.chunk_size:
                sub_chunks = self.chunk_by_size(paragraph, source_url, page_title)
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_order = chunk_order
                    sub_chunk.metadata.update({
                        'original_paragraph_size': len(paragraph),
                        'was_chunked_from_paragraph': True
                    })
                    chunks.append(sub_chunk)
                    chunk_order += 1
            else:
                chunk = DocumentChunk(
                    chunk_id=f"{hash(source_url)}_{chunk_order}_{uuid.uuid4().hex[:8]}",
                    content=paragraph,
                    source_url=source_url,
                    page_title=page_title,
                    chunk_order=chunk_order,
                    metadata={
                        'was_paragraph_chunk': True,
                        'paragraph_size': len(paragraph)
                    }
                )
                chunks.append(chunk)
                chunk_order += 1

        return chunks

    def chunk_by_headings(self, text: str, source_url: str, page_title: str = "") -> List[DocumentChunk]:
        """
        Chunk text by headings, creating chunks between headings.

        Args:
            text: Text to chunk
            source_url: Source URL for the text
            page_title: Title of the source page

        Returns:
            List of DocumentChunk objects
        """
        if not text:
            return []

        # Split text by common heading patterns
        # This regex looks for lines that look like headings
        heading_pattern = r'^(#{1,6}\s+.*?|.*?\n[-=]{3,}\n?)'
        parts = re.split(heading_pattern, text, flags=re.MULTILINE)

        chunks = []
        chunk_order = 0

        # Process the split parts
        i = 0
        while i < len(parts):
            part = parts[i].strip()
            if not part:
                i += 1
                continue

            # Check if this part is a heading
            if re.match(r'^(#{1,6}\s+.*?|.*?\n[-=]{3,}\n?)$', part, re.MULTILINE):
                # This is a heading, look for content that follows
                if i + 1 < len(parts):
                    content = parts[i + 1].strip()
                    full_content = part + "\n\n" + content if content else part
                else:
                    full_content = part
                    content = ""

                # If content is too large, fall back to size-based chunking
                if len(full_content) > self.chunk_size and content:
                    # Create chunks from the content part only
                    content_chunks = self.chunk_by_size(content, source_url, page_title)
                    for j, content_chunk in enumerate(content_chunks):
                        # Prepend the heading to the first chunk
                        if j == 0:
                            content_chunk.content = part + "\n\n" + content_chunk.content
                        content_chunk.chunk_order = chunk_order
                        content_chunk.metadata.update({
                            'heading': part,
                            'from_heading_chunking': True
                        })
                        chunks.append(content_chunk)
                        chunk_order += 1
                else:
                    chunk = DocumentChunk(
                        chunk_id=f"{hash(source_url)}_{chunk_order}_{uuid.uuid4().hex[:8]}",
                        content=full_content,
                        source_url=source_url,
                        page_title=page_title,
                        chunk_order=chunk_order,
                        metadata={
                            'heading': part,
                            'from_heading_chunking': True
                        }
                    )
                    chunks.append(chunk)
                    chunk_order += 1

                i += 2  # Skip the heading and the content
            else:
                # This is content without a heading, chunk it by size
                content_chunks = self.chunk_by_size(part, source_url, page_title)
                for content_chunk in content_chunks:
                    content_chunk.chunk_order = chunk_order
                    content_chunk.metadata.update({
                        'from_heading_chunking': True,
                        'no_heading': True
                    })
                    chunks.append(content_chunk)
                    chunk_order += 1
                i += 1

        return chunks

    def chunk_text(
        self,
        text: str,
        source_url: str,
        page_title: str = "",
        method: str = "size"
    ) -> List[DocumentChunk]:
        """
        Chunk text using the specified method.

        Args:
            text: Text to chunk
            source_url: Source URL for the text
            page_title: Title of the source page
            method: Chunking method ('size', 'paragraph', or 'heading')

        Returns:
            List of DocumentChunk objects
        """
        if method == "paragraph":
            return self.chunk_by_paragraph(text, source_url, page_title)
        elif method == "heading":
            return self.chunk_by_headings(text, source_url, page_title)
        else:  # default to size-based
            return self.chunk_by_size(text, source_url, page_title)

    def get_chunking_stats(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Get statistics about the chunking process.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            Dictionary with chunking statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_content_chars': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0
            }

        content_lengths = [len(chunk.content) for chunk in chunks]
        total_content = sum(content_lengths)

        return {
            'total_chunks': len(chunks),
            'total_content_chars': total_content,
            'avg_chunk_size': total_content / len(chunks) if chunks else 0,
            'min_chunk_size': min(content_lengths) if content_lengths else 0,
            'max_chunk_size': max(content_lengths) if content_lengths else 0,
            'size_variance': self._calculate_variance(content_lengths)
        }

    def _calculate_variance(self, values: List[int]) -> float:
        """Calculate variance of a list of values."""
        if not values:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def merge_small_chunks(
        self,
        chunks: List[DocumentChunk],
        max_combined_size: Optional[int] = None
    ) -> List[DocumentChunk]:
        """
        Merge small chunks together to avoid very small chunks.

        Args:
            chunks: List of DocumentChunk objects to potentially merge
            max_combined_size: Maximum size of combined chunks (defaults to self.chunk_size)

        Returns:
            List of DocumentChunk objects with small chunks merged
        """
        if not chunks or len(chunks) <= 1:
            return chunks

        if max_combined_size is None:
            max_combined_size = self.chunk_size

        merged_chunks = []
        i = 0

        while i < len(chunks):
            current_chunk = chunks[i]

            # If current chunk is already large enough, add it as is
            if len(current_chunk.content) >= self.min_chunk_size * 2:  # somewhat larger than min
                merged_chunks.append(current_chunk)
                i += 1
                continue

            # Try to combine with next chunks if they're small
            combined_content = current_chunk.content
            combined_metadata = current_chunk.metadata.copy()
            combined_metadata['merged_from'] = [current_chunk.chunk_id]

            j = i + 1
            while j < len(chunks):
                next_chunk = chunks[j]
                potential_size = len(combined_content) + len(next_chunk.content)

                # Only merge if the combined size is not too large and next chunk is small
                if (potential_size <= max_combined_size and
                    len(next_chunk.content) < self.min_chunk_size * 2):
                    combined_content += "\n\n" + next_chunk.content
                    combined_metadata['merged_from'].append(next_chunk.chunk_id)
                    j += 1
                else:
                    break

            # Create a new merged chunk
            merged_chunk = DocumentChunk(
                chunk_id=f"merged_{current_chunk.chunk_id[:16]}_{len(combined_metadata['merged_from'])}",
                content=combined_content,
                source_url=current_chunk.source_url,
                page_title=current_chunk.page_title,
                chunk_order=current_chunk.chunk_order,
                metadata=combined_metadata
            )

            merged_chunks.append(merged_chunk)
            i = j  # Move to the next unprocessed chunk

        # Update chunk order to be sequential
        for idx, chunk in enumerate(merged_chunks):
            chunk.chunk_order = idx

        return merged_chunks