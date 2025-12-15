from fastapi import FastAPI
from src.api.v1 import router as v1_router
from src.core.config import settings
from src.core.logging import setup_logging

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
)

# Include API routes
app.include_router(v1_router, prefix="/api/v1", tags=["api-v1"])


@app.get("/")
def read_root():
    return {"message": "RAG Chatbot Backend API"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2025-01-15T10:30:00Z"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )