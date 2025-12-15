import re
from typing import List, Dict, Any, Optional
from src.core.logging import get_logger
from src.core.exceptions import ValidationException
from src.core.constants import (
    INSUFFICIENT_CONTEXT_MESSAGE,
    FALLBACK_UNANSWERABLE_MESSAGE,
    MAX_SEGMENT_TOKENS,
    MIN_SEGMENT_TOKENS
)

logger = get_logger(__name__)


class ValidationService:
    """
    Service for performing validation checks including hallucination detection,
    context isolation verification, and other quality assurance measures.
    """
    
    def __init__(self):
        # Patterns for detecting potential hallucinations
        self.hallucination_patterns = [
            r'\b(apparently|possibly|maybe|might be)\b',  # Uncertain language
            r'\b(according to my knowledge|as far as i know)\b',  # Hesitant phrasing
            r'\b(i think|i believe)\b',  # Personal opinions
            r'\b(unknown|not specified|not mentioned)\b',  # Acknowledging gaps
        ]
    
    def validate_response_context_alignment(self, 
                                          response: str, 
                                          context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that the response is aligned with the provided context chunks.
        
        Args:
            response: The generated response to validate
            context_chunks: List of context chunks used to generate the response
            
        Returns:
            A dictionary containing validation results
        """
        logger.debug("Starting response context alignment validation")
        
        # Extract text content from context chunks
        context_texts = [chunk.get('payload', {}).get('content', '') for chunk in context_chunks if chunk.get('payload')]
        all_context = ' '.join(context_texts).lower()
        
        # Check for hallucinations by looking for information in response not in context
        response_lower = response.lower()
        
        # Tokenize response and context for comparison
        response_tokens = set(response_lower.split())
        context_tokens = set(all_context.split())
        
        # Find tokens in response that aren't in context
        unmatched_tokens = response_tokens - context_tokens
        
        # Calculate alignment score (simplified approach)
        if len(response_tokens) > 0:
            alignment_score = 1 - (len(unmatched_tokens) / len(response_tokens))
        else:
            alignment_score = 1.0  # No tokens in response
        
        # Flag potential hallucinations based on unmatched content and patterns
        potential_hallucinations = []
        for pattern in self.hallucination_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                potential_hallucinations.append(f"Pattern match: {pattern}")
        
        # Check if response mentions information not in context
        for token in unmatched_tokens:
            if len(token) > 3:  # Only consider tokens longer than 3 chars to avoid common words
                potential_hallucinations.append(f"Unmatched token: {token}")
        
        result = {
            "alignment_score": alignment_score,
            "is_aligned": alignment_score > 0.7,  # Threshold for acceptable alignment
            "potential_hallucinations": potential_hallucinations,
            "context_coverage": len(response_tokens - unmatched_tokens) / len(response_tokens) if response_tokens else 1.0
        }
        
        logger.debug(f"Response alignment validation complete: {result}")
        return result
    
    def validate_context_sufficiency(self, 
                                   query: str, 
                                   context_chunks: List[Dict[str, Any]], 
                                   response: str) -> Dict[str, Any]:
        """
        Validate whether the provided context was sufficient to answer the query.
        
        Args:
            query: The original query
            context_chunks: List of context chunks used to generate the response
            response: The generated response
            
        Returns:
            A dictionary containing sufficiency validation results
        """
        logger.debug("Starting context sufficiency validation")
        
        # Check if response is a fallback indicating insufficiency
        if INSUFFICIENT_CONTEXT_MESSAGE.lower() in response.lower() or \
           FALLBACK_UNANSWERABLE_MESSAGE.lower() in response.lower():
            return {
                "is_sufficient": False,
                "reason": "Response indicates insufficient context",
                "confidence": 1.0
            }
        
        # Analyze the relationship between query, context, and response
        query_tokens = set(query.lower().split())
        context_text = ' '.join([chunk.get('payload', {}).get('content', '') for chunk in context_chunks if chunk.get('payload')])
        context_tokens = set(context_text.lower().split())
        response_tokens = set(response.lower().split())
        
        # Calculate how much of the query is covered by context
        query_coverage = len(query_tokens.intersection(context_tokens)) / len(query_tokens) if query_tokens else 1.0
        
        # Calculate how much of the response is supported by context
        response_support = len(response_tokens.intersection(context_tokens)) / len(response_tokens) if response_tokens else 1.0
        
        # Determine sufficiency based on coverage thresholds
        is_sufficient = query_coverage > 0.5 and response_support > 0.7
        
        result = {
            "is_sufficient": is_sufficient,
            "query_coverage": query_coverage,
            "response_support": response_support,
            "confidence": min(query_coverage, response_support)
        }
        
        logger.debug(f"Context sufficiency validation: {result}")
        return result
    
    def validate_text_segment(self, text_segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a text segment according to the requirements.
        
        Args:
            text_segment: A dictionary representing the text segment to validate
            
        Returns:
            A dictionary containing validation results
        """
        logger.debug(f"Validating text segment: {text_segment.get('id', 'unknown')}")
        
        content = text_segment.get('content', '')
        source_chapter = text_segment.get('source_chapter', '')
        source_section = text_segment.get('source_section', '')
        content_tokens = len(content.split()) if content else 0
        
        validation_results = {
            "id_valid": bool(text_segment.get('id')),
            "content_valid": bool(content.strip()) and content_tokens <= MAX_SEGMENT_TOKENS,
            "source_chapter_valid": bool(source_chapter.strip()),
            "source_section_valid": bool(source_section.strip()),
            "token_count_valid": MIN_SEGMENT_TOKENS <= content_tokens <= MAX_SEGMENT_TOKENS,
            "is_valid": False
        }
        
        # Overall validation
        validation_results["is_valid"] = all([
            validation_results["id_valid"],
            validation_results["content_valid"], 
            validation_results["source_chapter_valid"],
            validation_results["source_section_valid"],
            validation_results["token_count_valid"]
        ])
        
        # Log validation issues if any
        if not validation_results["is_valid"]:
            invalid_fields = [field for field, is_valid in validation_results.items() 
                             if not is_valid and field != "is_valid"]
            logger.warning(f"Text segment {text_segment.get('id', 'unknown')} failed validation: {invalid_fields}")
        
        logger.debug(f"Text segment validation: {validation_results}")
        return validation_results
    
    def validate_selected_text_mode(self, query: str, selected_text: str, response: str) -> Dict[str, Any]:
        """
        Validate response in selected-text mode to ensure it only uses the selected text as context.
        
        Args:
            query: The original query
            selected_text: The text selected by the user
            response: The generated response
            
        Returns:
            A dictionary containing validation results for selected-text mode
        """
        logger.debug("Starting selected-text mode validation")
        
        # Check if response mentions information not present in selected text
        selected_tokens = set(selected_text.lower().split())
        response_tokens = set(response.lower().split())
        
        # Remove common words that don't indicate hallucination
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        unmatched_tokens = response_tokens - selected_tokens - common_words
        
        # If selected text is insufficient, verify the response reflects this
        if len(selected_text.strip()) < 10:  # Very short text is likely insufficient
            is_correct = INSUFFICIENT_CONTEXT_MESSAGE.lower() in response.lower()
            result = {
                "follows_policy": is_correct,
                "reason": f"Selected text was too short, response should indicate insufficiency: {is_correct}",
                "unmatched_tokens": list(unmatched_tokens)
            }
        else:
            # For adequate selected text, check if response stays within bounds
            alignment_ratio = 1 - (len(unmatched_tokens) / len(response_tokens)) if response_tokens else 1.0
            follows_policy = alignment_ratio > 0.8  # 80% of response should be supported by selected text
            
            result = {
                "follows_policy": follows_policy,
                "alignment_ratio": alignment_ratio,
                "unmatched_tokens": list(unmatched_tokens),
                "reason": f"Response alignment with selected text: {alignment_ratio:.2f}" if not follows_policy else "Response properly aligned with selected text"
            }
        
        logger.debug(f"Selected-text mode validation: {result}")
        return result
    
    def validate_book_wide_mode(self, query: str, response: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate response in book-wide mode to ensure it properly uses retrieved context.
        
        Args:
            query: The original query
            response: The generated response
            retrieved_chunks: The chunks retrieved from vector store
            
        Returns:
            A dictionary containing validation results for book-wide mode
        """
        logger.debug("Starting book-wide mode validation")
        
        # Combine content from all retrieved chunks
        retrieved_content = ' '.join([
            chunk.get('payload', {}).get('content', '') 
            for chunk in retrieved_chunks 
            if chunk.get('payload', {}).get('content')
        ]).lower()
        
        response_lower = response.lower()
        
        # Check how much of the response content comes from retrieved chunks
        response_tokens = set(response_lower.split())
        retrieved_tokens = set(retrieved_content.split())
        
        # Remove common words for more accurate comparison
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        relevant_response_tokens = response_tokens - common_words
        relevant_retrieved_tokens = retrieved_tokens - common_words
        
        if relevant_response_tokens:
            alignment_ratio = len(relevant_response_tokens.intersection(relevant_retrieved_tokens)) / len(relevant_response_tokens)
        else:
            alignment_ratio = 1.0  # No relevant tokens in response
        
        result = {
            "follows_policy": alignment_ratio > 0.6,  # At least 60% of response should be supported by retrieved context
            "alignment_ratio": alignment_ratio,
            "retrieved_chunks_count": len(retrieved_chunks),
            "reason": f"Response alignment with retrieved context: {alignment_ratio:.2f}"
        }
        
        logger.debug(f"Book-wide mode validation: {result}")
        return result


# Global instance for use throughout the application
validation_service = ValidationService()