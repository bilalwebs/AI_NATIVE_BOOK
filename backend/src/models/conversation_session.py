from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.models import Base
import uuid


class ConversationSession(Base):
    """
    Model containing a series of user interactions with the chatbot, 
    stored securely with user context.
    """
    __tablename__ = "conversation_sessions"

    # Fields as defined in data-model.md
    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, nullable=True)  # Identifier for the user (if available)
    mode = Column(String, nullable=False)  # Either "book-wide" or "selected-text"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # Expiration timestamp for session cleanup
    
    # Store messages as JSON as it's a complex nested structure
    messages = Column(JSON, nullable=False, default=list)  # List of message objects

    def __repr__(self):
        return f"<ConversationSession(id='{self.session_id}', user='{self.user_id}', mode='{self.mode}')>"