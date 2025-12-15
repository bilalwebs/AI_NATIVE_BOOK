from typing import List, Dict, Any, Optional
from src.core.vector_store import vector_store
from src.core.embedding_service import embedding_service
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import RAGException

logger = get_logger(__name__)


class RetrievalService:
    """
    Service for performing vector search and retrieval operations.
    """

    def __init__(self):
        self.top_k = settings.top_k_retrieval
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def retrieve_relevant_chunks(self,
                                query: str,
                                top_k: Optional[int] = None,
                                filters: Optional[Dict[str, Any]] = None,
                                mode: str = "book-wide") -> List[Dict[str, Any]]:
        """
        Retrieve relevant text chunks based on a query.

        Args:
            query: The query text to search for
            top_k: Number of top results to return (defaults to config value)
            filters: Optional filters to apply to the search
            mode: Either "book-wide" for vector search or "selected-text" to bypass search

        Returns:
            A list of relevant chunks with their metadata
        """
        if not query.strip():
            raise RAGException("RETRIEVAL_ERROR", "Query cannot be empty")

        try:
            logger.debug(f"Starting retrieval for query in mode: {mode}, query: {query[:50]}...")

            # If in selected-text mode, bypass vector search and return empty results
            # The context will be provided separately from the selected text
            if mode == "selected-text":
                logger.info("Bypassing vector search in selected-text mode")
                return []

            # Generate embedding for the query (for book-wide mode)
            query_embedding = self.embedding_service.generate_embedding(query)

            # Perform vector search
            top_k = top_k or self.top_k
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters
            )

            logger.info(f"Retrieved {len(results)} relevant chunks for query in book-wide mode")
            return results

        except RAGException:
            # Re-raise RAG exceptions as they're already properly formatted
            raise
        except Exception as e:
            logger.error(f"Unexpected error in retrieve_relevant_chunks: {str(e)}")
            raise RAGException("RETRIEVAL_ERROR", f"Failed to retrieve relevant chunks: {str(e)}")

    def retrieve_by_chapter_section(self,
                                   chapter: str,
                                   section: str,
                                   top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve chunks specifically from a given chapter and section.

        Args:
            chapter: The chapter to search in
            section: The section to search in
            top_k: Number of top results to return (defaults to config value)

        Returns:
            A list of chunks from the specified chapter and section
        """
        try:
            logger.debug(f"Retrieving chunks for chapter: {chapter}, section: {section}")

            # Create filters for the specific chapter and section
            filters = {
                "source_chapter": chapter,
                "source_section": section
            }

            # Perform vector search with filters
            top_k = top_k or self.top_k
            results = self.vector_store.search_similar(
                query_embedding=None,  # We'll need to pass a dummy embedding since the search function requires it
                top_k=top_k,
                filters=filters
            )

            logger.info(f"Retrieved {len(results)} chunks from chapter {chapter}, section {section}")
            return results

        except RAGException:
            # Re-raise RAG exceptions as they're already properly formatted
            raise
        except Exception as e:
            logger.error(f"Unexpected error in retrieve_by_chapter_section: {str(e)}")
            raise RAGException("RETRIEVAL_ERROR", f"Failed to retrieve chunks by chapter/section: {str(e)}")

    def retrieve_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve specific chunks by their IDs.

        Args:
            ids: List of chunk IDs to retrieve

        Returns:
            A list of chunks corresponding to the specified IDs
        """
        try:
            logger.debug(f"Retrieving chunks by IDs: {ids}")

            # This would require a different approach since our vector store doesn't support direct ID lookup
            # For now, we'll just return an empty list and implement this properly if needed
            # This could be implemented by storing chunk IDs in metadata and searching by that
            results = []

            # In a real implementation, we would retrieve these from the vector store and/or database
            logger.warning("Direct ID retrieval not fully implemented in this version")

            return results
        except Exception as e:
            logger.error(f"Unexpected error in retrieve_by_ids: {str(e)}")
            raise RAGException("RETRIEVAL_ERROR", f"Failed to retrieve chunks by IDs: {str(e)}")

    def get_all_chunks_for_section(self, section_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a specific section.

        Args:
            section_id: The section ID to retrieve chunks for

        Returns:
            A list of all chunks for the specified section
        """
        try:
            logger.debug(f"Retrieving all chunks for section ID: {section_id}")

            # This would require implementation in the vector store to support
            # metadata-based filtering for all items in a section
            results = []

            logger.info(f"Retrieved {len(results)} chunks for section {section_id}")
            return results
        except Exception as e:
            logger.error(f"Unexpected error in get_all_chunks_for_section: {str(e)}")
            raise RAGException("RETRIEVAL_ERROR", f"Failed to retrieve all chunks for section: {str(e)}")


# Global instance for use throughout the application
retrieval_service = RetrievalService()