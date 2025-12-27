from fastapi import APIRouter, HTTPException, status, Request
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
    Only responds if Cohere client is properly initialized.
    """
    # Check if Cohere client is properly initialized
    if not rag_service.cohere_client:
        return ChatResponse(
            response="Error: Cohere client not initialized. Please check API key and server configuration.",
            sources=[],
            retrieved_chunks=[]
        )

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

    except ValueError as e:  # Catch ValueError specifically for Cohere client not initialized
        logger.error(f"Error in chat endpoint: {str(e)}")
        if "Cohere client not initialized" in str(e):
            return ChatResponse(
                response="Error: Cohere client not initialized. Please check API key and server configuration.",
                sources=[],
                retrieved_chunks=[]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing chat request: {str(e)}"
            )
    except Exception as e:  # Handle other exceptions
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )


# Remove other endpoints to comply with the rule of only accepting POST requests at /chat
# The following endpoints are removed to ensure compliance with the rules:
# - /chat/stream (POST)
# - /chat/models (GET)
# - Any other endpoints that are not POST /chat


# Error handler for non-POST requests to enforce the rule
@router.get("/chat")
async def chat_get_method(request: Request):
    """
    GET method handler for /chat endpoint.
    Responds with method not allowed message as per rules.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Please use a POST request with JSON body containing your query and response_type."
    )


@router.put("/chat")
async def chat_put_method(request: Request):
    """
    PUT method handler for /chat endpoint.
    Responds with method not allowed message as per rules.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Please use a POST request with JSON body containing your query and response_type."
    )


@router.delete("/chat")
async def chat_delete_method(request: Request):
    """
    DELETE method handler for /chat endpoint.
    Responds with method not allowed message as per rules.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Please use a POST request with JSON body containing your query and response_type."
    )


@router.patch("/chat")
async def chat_patch_method(request: Request):
    """
    PATCH method handler for /chat endpoint.
    Responds with method not allowed message as per rules.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Please use a POST request with JSON body containing your query and response_type."
    )