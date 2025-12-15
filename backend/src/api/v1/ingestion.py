from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
from src.api.dependencies import get_api_key_header
from src.services.chunking_service import chunking_service
from src.services.embedding_service import embedding_service
from src.core.vector_store import vector_store
from src.core.database import SessionLocal
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class IngestionRequest(BaseModel):
    book_content: List[Dict[str, Any]]
    book_id: str


class IngestionResponse(BaseModel):
    status: str
    chunks_processed: int
    book_id: str
    timestamp: str


@router.post("/ingest", response_model=IngestionResponse)
async def ingestion_endpoint(
    request: IngestionRequest,
    api_key: str = Depends(get_api_key_header())
):
    """
    Ingest book content for RAG functionality.
    
    Args:
        request: Ingestion request with book content
        api_key: API key for authentication
        
    Returns:
        IngestionResponse with processing status
    """
    logger.info(f"Received ingestion request for book ID: {request.book_id} with {len(request.book_content)} content items")
    
    try:
        total_chunks_processed = 0
        
        # Process each content item
        for item in request.book_content:
            chapter = item.get("chapter", "")
            section = item.get("section", "")
            content = item.get("content", "")
            
            if not content.strip():
                logger.warning(f"Skipping empty content for chapter {chapter}, section {section}")
                continue
            
            # Chunk the content
            chunks = chunking_service.chunk_text(
                text=content,
                source_chapter=chapter,
                source_section=section,
                book_id=request.book_id
            )
            
            # Process each chunk
            for chunk in chunks:
                # Generate embedding for the chunk content
                embedding = embedding_service.generate_embedding(chunk["content"])
                
                # Prepare metadata for vector store
                metadata = {
                    "source_chapter": chunk["source_chapter"],
                    "source_section": chunk["source_section"],
                    "book_id": request.book_id,
                    "chunk_order": chunk["chunk_order"],
                    "content_preview": chunk["content"][:100]  # Store first 100 chars as preview
                }
                
                # Store embedding and metadata in vector store
                success = vector_store.store_embedding(
                    text_id=chunk["id"],
                    embedding=embedding,
                    metadata=metadata
                )
                
                if not success:
                    logger.error(f"Failed to store embedding for chunk ID: {chunk['id']}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={
                            "error": {
                                "code": "STORAGE_ERROR",
                                "message": f"Failed to store embedding for chunk ID: {chunk['id']}"
                            }
                        }
                    )
                
                total_chunks_processed += 1
        
        logger.info(f"Ingestion completed for book ID: {request.book_id}, processed {total_chunks_processed} chunks")
        
        # Import datetime here to avoid conflicts
        from datetime import datetime
        
        return IngestionResponse(
            status="success",
            chunks_processed=total_chunks_processed,
            book_id=request.book_id,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing ingestion request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred while processing the ingestion request"
                }
            }
        )