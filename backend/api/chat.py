from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from backend.models.chat import ChatRequest, ChatResponse
from backend.services.rag_service import rag_service
from backend.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """
    Main chat endpoint for the RAG chatbot.
    """
    try:
        logger.info(f"Received chat request: {chat_request.message[:50]}...")

        # Search for similar content in the vector database
        similar_chunks = rag_service.search_similar_content(
            query=chat_request.message,
            top_k=chat_request.top_k,
            score_threshold=chat_request.score_threshold
        )

        # Combine the retrieved chunks into context
        context = rag_service.get_context_from_chunks(
            chunks=similar_chunks,
            max_length=settings.RAG_MAX_CONTEXT_LENGTH
        )

        # Generate response using the LLM with the context
        response = rag_service.generate_response(
            query=chat_request.message,
            context=context,
            history=[{"role": msg.role, "content": msg.content} for msg in chat_request.history] if chat_request.history else None
        )

        # Prepare response
        chat_response = ChatResponse(
            response=response,
            sources=[{
                'url': chunk['source_url'],
                'title': chunk['page_title'],
                'score': chunk['score']
            } for chunk in similar_chunks],
            retrieved_chunks=similar_chunks
        )

        logger.info(f"Successfully generated response for query: {chat_request.message[:30]}...")
        return chat_response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream_endpoint(chat_request: ChatRequest):
    """
    Streaming chat endpoint for the RAG chatbot.
    """
    try:
        logger.info(f"Received streaming chat request: {chat_request.message[:50]}...")

        # Search for similar content in the vector database
        similar_chunks = rag_service.search_similar_content(
            query=chat_request.message,
            top_k=chat_request.top_k,
            score_threshold=chat_request.score_threshold
        )

        # Combine the retrieved chunks into context
        context = rag_service.get_context_from_chunks(
            chunks=similar_chunks,
            max_length=settings.RAG_MAX_CONTEXT_LENGTH
        )

        # For streaming, we would implement a generator function
        # For now, we'll return the same response as the regular chat endpoint
        response = rag_service.generate_response(
            query=chat_request.message,
            context=context,
            history=[{"role": msg.role, "content": msg.content} for msg in chat_request.history] if chat_request.history else None
        )

        # In a real streaming implementation, we would yield tokens as they're generated
        # For now, returning the full response
        chat_response = ChatResponse(
            response=response,
            sources=[{
                'url': chunk['source_url'],
                'title': chunk['page_title'],
                'score': chunk['score']
            } for chunk in similar_chunks],
            retrieved_chunks=similar_chunks
        )

        logger.info(f"Successfully generated streaming response for query: {chat_request.message[:30]}...")
        return chat_response

    except Exception as e:
        logger.error(f"Error in streaming chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing streaming chat request: {str(e)}"
        )


@router.get("/chat/models")
async def get_available_models():
    """
    Get available models for the chatbot.
    """
    try:
        # In a real implementation, this would fetch from OpenRouter
        # For now, returning a default list
        available_models = [
            "openai/gpt-3.5-turbo",
            "openai/gpt-4",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet"
        ]

        return {"models": available_models}
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available models: {str(e)}"
        )