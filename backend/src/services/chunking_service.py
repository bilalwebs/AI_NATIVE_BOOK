import re
from typing import List, Tuple, Dict, Any
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import ValidationException

logger = get_logger(__name__)


class ChunkingService:
    """
    Service for splitting book content into text segments with sentence-aware logic
    and deterministic chunking to ensure stable chunk IDs.
    """
    
    def __init__(self):
        self.chunk_size = settings.chunk_size  # tokens
        self.chunk_overlap = settings.chunk_overlap  # tokens
        self.max_tokens_per_chunk = settings.max_tokens_per_chunk
    
    def chunk_text(self, 
                   text: str, 
                   source_chapter: str, 
                   source_section: str,
                   book_id: str = "default_book") -> List[Dict[str, Any]]:
        """
        Split text into chunks with sentence awareness to prevent breaking sentences.
        
        Args:
            text: The text to be chunked
            source_chapter: The chapter where this text originates
            source_section: The specific section within the chapter
            book_id: Identifier for the book
            
        Returns:
            A list of dictionaries containing chunk information
        """
        logger.info(f"Starting to chunk text from {source_chapter} - {source_section}")
        
        # First, split the text into sentences
        sentences = self._split_into_sentences(text)
        
        # Then, group sentences into chunks of approximately the target size
        chunks = self._group_sentences_into_chunks(
            sentences, 
            source_chapter, 
            source_section, 
            book_id
        )
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex patterns.
        
        Args:
            text: The text to split into sentences
            
        Returns:
            A list of sentences
        """
        # This pattern looks for sentence endings (., !, ?) followed by whitespace and capital letter
        # It handles common abbreviations and exceptions
        sentence_endings = r'(?<!\w\.\w.)(?<![A-Z][a-z].)(?<=\.|\!|\?)\s+(?=[A-Z])'
        sentences = re.split(sentence_endings, text)
        
        # Clean up the sentences, removing empty strings
        cleaned_sentences = [s.strip() for s in sentences if s.strip()]
        
        return cleaned_sentences
    
    def _group_sentences_into_chunks(self, 
                                    sentences: List[str], 
                                    source_chapter: str, 
                                    source_section: str, 
                                    book_id: str) -> List[Dict[str, Any]]:
        """
        Group sentences into chunks of approximately the target size.
        
        Args:
            sentences: List of sentences to group
            source_chapter: The chapter where this text originates
            source_section: The specific section within the chapter
            book_id: Identifier for the book
            
        Returns:
            A list of dictionaries containing chunk information
        """
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_order = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_length = len(sentence.split())  # Approximate token count using words
            
            # Check if adding this sentence would exceed the maximum chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Finalize the current chunk
                chunk_text = " ".join(current_chunk)
                
                # Create a stable ID based on source info and chunk order
                chunk_id = f"{book_id}:{source_chapter}:{source_section}:{chunk_order:04d}"
                
                chunks.append({
                    "id": chunk_id,
                    "content": chunk_text,
                    "source_chapter": source_chapter,
                    "source_section": source_section,
                    "chunk_order": chunk_order
                })
                
                # Start new chunk with overlap if possible
                chunk_order += 1
                
                # Add overlap by including some previous sentences
                overlap_sentences = []
                if self.chunk_overlap > 0:
                    # Calculate how many sentences we need for overlap
                    overlap_length = 0
                    overlap_start_idx = len(current_chunk) - 1
                    
                    # Work backwards to collect sentences up to the overlap size
                    while overlap_start_idx > 0 and overlap_length < self.chunk_overlap:
                        sentence_len = len(current_chunk[overlap_start_idx].split())
                        if overlap_length + sentence_len <= self.chunk_overlap:
                            overlap_sentences.insert(0, current_chunk[overlap_start_idx])
                            overlap_length += sentence_len
                            overlap_start_idx -= 1
                        else:
                            break
                
                # Start new chunk with overlap sentences
                current_chunk = overlap_sentences if overlap_sentences else []
                current_length = sum(len(s.split()) for s in current_chunk)
                
                # Now try to add the current sentence to the new chunk
                continue  # Continue with the same sentence, don't increment i
            
            # Add the current sentence to the chunk
            current_chunk.append(sentence)
            current_length += sentence_length
            i += 1
        
        # Add the final chunk if it has content
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            
            # Create a stable ID based on source info and chunk order
            chunk_id = f"{book_id}:{source_chapter}:{source_section}:{chunk_order:04d}"
            
            chunks.append({
                "id": chunk_id,
                "content": chunk_text,
                "source_chapter": source_chapter,
                "source_section": source_section,
                "chunk_order": chunk_order
            })
        
        return chunks
    
    def validate_chunk(self, chunk: Dict[str, Any]) -> bool:
        """
        Validate a chunk meets the requirements.
        
        Args:
            chunk: A chunk dictionary to validate
            
        Returns:
            True if the chunk is valid, raises exception if not
        """
        content = chunk.get("content", "")
        source_chapter = chunk.get("source_chapter", "")
        source_section = chunk.get("source_section", "")
        
        # Check if content is too long
        tokens = len(content.split())
        if tokens > self.max_tokens_per_chunk:
            raise ValidationException(
                f"Chunk content exceeds maximum token count ({self.max_tokens_per_chunk})",
                {"chunk_id": chunk.get("id"), "token_count": tokens}
            )
        
        # Check if source chapter and section are valid
        if not source_chapter.strip():
            raise ValidationException(
                "Source chapter is required and cannot be empty",
                {"chunk_id": chunk.get("id")}
            )
        
        if not source_section.strip():
            raise ValidationException(
                "Source section is required and cannot be empty",
                {"chunk_id": chunk.get("id")}
            )
        
        return True


# Global instance for use throughout the application
chunking_service = ChunkingService()