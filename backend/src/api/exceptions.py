from typing import Optional
from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: dict


class RAGException(Exception):
    """Base exception for RAG-related errors"""
    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InsufficientContextException(RAGException):
    """Exception raised when there's insufficient context to answer a question"""
    def __init__(self, message: str = "Query cannot be answered with available context", details: Optional[dict] = None):
        super().__init__("INSUFFICIENT_CONTEXT", message, details)


class InvalidModeException(RAGException):
    """Exception raised when an invalid mode is specified"""
    def __init__(self, mode: str, details: Optional[dict] = None):
        super().__init__("INVALID_MODE", f"Invalid mode: {mode}", details)


class ValidationException(RAGException):
    """Exception raised when validation fails"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__("VALIDATION_ERROR", message, details)


def handle_rag_exception(exc: RAGException):
    """Convert RAGException to HTTPException"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


# Custom HTTP exceptions for specific cases
def raise_insufficient_context_error(message: str = "Query cannot be answered with available context"):
    """Raise an insufficient context HTTP exception"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": {
                "code": "INSUFFICIENT_CONTEXT",
                "message": message
            }
        }
    )


def raise_invalid_mode_error(mode: str):
    """Raise an invalid mode HTTP exception"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": {
                "code": "INVALID_MODE",
                "message": f"Invalid mode: {mode}"
            }
        }
    )