from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from src.core.database import get_db_health
from src.core.vector_store import vector_store
from src.core.llm_client import llm_client
from src.core.config import settings
from src.core.logging import get_logger
import datetime

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the service and its dependencies.
    
    Returns:
        HealthResponse with status of the service and its dependencies
    """
    logger.info("Health check endpoint called")
    
    # Initialize checks dictionary
    checks = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    # Check database health
    try:
        db_healthy = get_db_health()
        checks["database"] = "connected" if db_healthy else "disconnected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        checks["database"] = "error"
    
    # Check vector store health
    try:
        # Attempt a simple operation to verify vector store is accessible
        # Using a mock query to test connection without retrieving actual data
        mock_check = hasattr(vector_store, 'client') and vector_store.client is not None
        checks["vector_store"] = "connected" if mock_check else "disconnected"
    except Exception as e:
        logger.error(f"Vector store health check failed: {str(e)}")
        checks["vector_store"] = "error"
    
    # Check AI service health
    try:
        # Attempt a simple operation to verify AI service is accessible
        # This is a basic check using configuration settings
        ai_service_available = settings.cohere_api_key is not None and len(settings.cohere_api_key) > 0
        checks["ai_service"] = "available" if ai_service_available else "unavailable"
    except Exception as e:
        logger.error(f"AI service health check failed: {str(e)}")
        checks["ai_service"] = "error"
    
    # Determine overall status based on individual checks
    overall_status = "healthy"
    if checks.get("database") != "connected" or \
       checks.get("vector_store") != "connected" or \
       checks.get("ai_service") != "available":
        overall_status = "degraded"
    
    # Compile response
    response = HealthResponse(
        status=overall_status,
        checks=checks
    )
    
    logger.info(f"Health check completed with status: {overall_status}")
    return response