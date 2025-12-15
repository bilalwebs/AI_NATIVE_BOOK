from fastapi import APIRouter
from src.api.v1 import router as v1_router


# Main API router that includes all versioned routers
router = APIRouter()

# Include versioned routers
router.include_router(v1_router, prefix="/v1", tags=["v1"])