from fastapi import APIRouter
from src.api.v1 import chat, ingestion, health


router = APIRouter()

# Include all v1 API routes
router.include_router(chat.router, prefix="", tags=["chat"])
router.include_router(ingestion.router, prefix="", tags=["ingestion"])
router.include_router(health.router, prefix="", tags=["health"])