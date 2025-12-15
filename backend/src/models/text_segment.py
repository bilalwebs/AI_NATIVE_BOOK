from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from src.models import Base

if TYPE_CHECKING:
    from .book_section import BookSection


class BookTextSegment(Base):
    """
    Model representing a segment of book content with stable ID, 
    source chapter/section reference, and text content.
    """
    __tablename__ = "book_text_segments"

    # Fields as defined in data-model.md
    id = Column(String, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    source_chapter = Column(String, nullable=False)
    source_section = Column(String, nullable=False)
    chunk_order = Column(Integer, nullable=False)
    
    # Reference to corresponding vector in Qdrant
    vector_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<BookTextSegment(id='{self.id}', chapter='{self.source_chapter}', section='{self.source_section}')>"