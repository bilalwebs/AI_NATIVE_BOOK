from typing import List, Dict, Any, Optional
from src.core.llm_client import llm_client
from src.core.validation_service import validation_service
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import RAGException
from src.core.constants import INSUFFICIENT_CONTEXT_MESSAGE

logger = get_logger(__name__)


class GenerationService:
    """
    Service for generating answers using Cohere's language models based on context.
    """
    
    def __init__(self):
        self.model_name = "command-r-plus"  # Default model as configured in llm_client
        self.temperature = 0.3  # Low temperature for factual responses
        self.max_tokens = 500  # Limit response length
    
    def generate_answer(self, 
                       query: str, 
                       context_chunks: List[Dict[str, Any]], 
                       mode: str = "book-wide") -> Dict[str, Any]:
        """
        Generate an answer to a query based on the provided context chunks.
        
        Args:
            query: The user's question
            context_chunks: List of context chunks relevant to the query
            mode: Either "book-wide" or "selected-text" determining response behavior
            
        Returns:
            A dictionary containing the response, sources, and metadata
        """
        try:
            logger.debug(f"Generating answer for query: {query[:50]}..., in mode: {mode}")
            
            # Format context from chunks
            formatted_context = self._format_context(context_chunks, mode)
            
            # Determine if context is sufficient
            if not formatted_context.strip() and mode == "selected-text":
                return {
                    "response": INSUFFICIENT_CONTEXT_MESSAGE,
                    "sources": [],
                    "mode_used": mode,
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            
            # Generate the response using the LLM
            if context_chunks:
                prompt = self._construct_prompt(query, formatted_context, mode)
                response_text = llm_client.generate_text(
                    prompt=prompt,
                    context=formatted_context if mode == "book-wide" else None,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            else:
                # No context available, return appropriate message
                if mode == "selected-text":
                    response_text = INSUFFICIENT_CONTEXT_MESSAGE
                else:
                    response_text = "I cannot answer that question as it's not covered in the book content."
            
            # Validate the response for hallucinations and context alignment
            validation_result = validation_service.validate_response_context_alignment(
                response_text, 
                context_chunks
            )
            
            # Extract sources/citations from context chunks
            sources = []
            if context_chunks:
                for chunk in context_chunks:
                    payload = chunk.get('payload', {})
                    sources.append({
                        "chapter": payload.get('source_chapter', ''),
                        "section": payload.get('source_section', ''),
                        "text": payload.get('content', '')[:200] + "..." if len(payload.get('content', '')) > 200 else payload.get('content', '')
                    })
            
            result = {
                "response": response_text,
                "sources": sources,
                "mode_used": mode,
                "timestamp": "2025-01-15T10:30:00Z",
                "validation_result": validation_result
            }
            
            logger.info(f"Generated answer with {len(sources)} sources for mode {mode}")
            return result
            
        except RAGException:
            # Re-raise RAG exceptions as they're already properly formatted
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_answer: {str(e)}")
            raise RAGException("GENERATION_ERROR", f"Failed to generate answer: {str(e)}")
    
    def _construct_prompt(self, query: str, context: str, mode: str) -> str:
        """
        Construct the appropriate prompt based on the mode and context.
        
        Args:
            query: The user's question
            context: Formatted context for the query
            mode: Either "book-wide" or "selected-text"
            
        Returns:
            A formatted prompt string
        """
        if mode == "selected-text":
            # For selected text mode, only allow responses based on the provided context
            prompt = f"""
            ONLY use the following selected text to answer the question. Do not use any knowledge beyond this text.
            If the question cannot be answered with the provided text, respond with: "{INSUFFICIENT_CONTEXT_MESSAGE}"

            Selected Text: {context}

            Question: {query}

            Answer:
            """
        else:
            # For book-wide mode, use context to form the response
            prompt = f"""
            Using ONLY the following information from the book, answer the question. 
            Do not use any external knowledge or general world knowledge.
            If the question cannot be answered with the provided information, respond with: "I cannot answer that question as it's not covered in the book content."

            Context: {context}

            Question: {query}

            Answer (be concise and cite chapter/section if possible):
            """
        
        return prompt
    
    def _format_context(self, context_chunks: List[Dict[str, Any]], mode: str) -> str:
        """
        Format context chunks for use in the prompt.
        
        Args:
            context_chunks: List of context chunks to format
            mode: Either "book-wide" or "selected-text"
            
        Returns:
            A formatted context string
        """
        if not context_chunks:
            return ""
        
        formatted_parts = []
        for i, chunk in enumerate(context_chunks):
            payload = chunk.get('payload', {})
            content = payload.get('content', '')
            source_chapter = payload.get('source_chapter', 'Unknown')
            source_section = payload.get('source_section', 'Unknown')
            
            if mode == "selected-text":
                # In selected text mode, we only care about the content
                formatted_parts.append(f"{content}")
            else:
                # In book-wide mode, include source information
                formatted_parts.append(f"[Source: {source_chapter} - {source_section}] {content}")
        
        return "\n\n".join(formatted_parts)
    
    def validate_and_generate_fallback(self, 
                                      query: str, 
                                      context_chunks: List[Dict[str, Any]], 
                                      mode: str = "book-wide") -> Dict[str, Any]:
        """
        Generate an answer and validate it, returning a fallback if needed.
        
        Args:
            query: The user's question
            context_chunks: List of context chunks to use for response
            mode: Either "book-wide" or "selected-text"
            
        Returns:
            A validated response dictionary
        """
        # Generate initial response
        response_data = self.generate_answer(query, context_chunks, mode)
        
        # Perform validation checks
        if mode == "selected-text" and context_chunks:
            # Validate selected-text mode constraints
            validation_result = validation_service.validate_selected_text_mode(
                query, 
                context_chunks[0].get('payload', {}).get('content', ''), 
                response_data["response"]
            )
            
            if not validation_result["follows_policy"]:
                logger.warning(f"Response did not follow selected-text policy: {validation_result.get('reason', 'Unknown reason')}")
                
                # Return fallback if validation fails
                if len(context_chunks[0].get('payload', {}).get('content', '').strip()) < 10:
                    response_data["response"] = INSUFFICIENT_CONTEXT_MESSAGE
                else:
                    # For book-wide mode, validate differently
                    if mode == "book-wide":
                        book_wide_validation = validation_service.validate_book_wide_mode(
                            query,
                            response_data["response"],
                            context_chunks
                        )
                        
                        if not book_wide_validation["follows_policy"]:
                            logger.warning(f"Response did not follow book-wide policy: {book_wide_validation.get('reason', 'Unknown reason')}")
        
        return response_data


# Global instance for use throughout the application
generation_service = GenerationService()