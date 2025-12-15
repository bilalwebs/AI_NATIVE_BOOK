from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.config import settings
from src.core.security import verify_api_key
from src.models import get_db


def get_api_key_header():
    """Dependency to get API key from header"""
    def api_key_dependency(x_api_key: str = None):
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is missing"
            )
        
        # In a real implementation, you'd verify this against a database or stored value
        # For now, we'll just verify it's present and not empty
        if not settings.cohere_api_key or not settings.cohere_api_key == x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return x_api_key
    return api_key_dependency


def get_current_user(api_key: str = Depends(get_api_key_header())):
    """Dependency to get current user based on API key"""
    # In a full implementation, this would fetch user details based on the API key
    # For now, we'll just return a placeholder
    return {"id": "placeholder_user_id", "api_key": api_key}


def get_db_session() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()