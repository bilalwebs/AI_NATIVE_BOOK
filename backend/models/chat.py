from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """
    Model representing a chat message.
    """
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """
    Model for chat request payload.
    """
    message: str = Field(..., description="User's message to the chatbot")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Chat history")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for response generation")
    max_tokens: Optional[int] = Field(default=500, ge=1, le=2000, description="Maximum tokens in response")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of similar documents to retrieve")
    score_threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score threshold")


class ChatResponse(BaseModel):
    """
    Model for chat response payload.
    """
    response: str = Field(..., description="Chatbot's response")
    sources: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Sources used for the response")
    retrieved_chunks: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Retrieved chunks from vector store")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """
    Model for health check response.
    """
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")