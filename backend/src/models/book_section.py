from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, List
from src.models import Base

if TYPE_CHECKING:
    from .text_segment import BookTextSegment


class BookSection(Base):
    """
    Model representing a chapter or section of the book with metadata 
    about its content and location in the book structure.
    """
    __tablename__ = "book_sections"

    # Fields as defined in data-model.md
    section_id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    book_id = Column(String, nullable=False)
    parent_section_id = Column(String, nullable=True)  # For hierarchical structure
    
    # Hierarchical level (e.g., 1 for chapter, 2 for subsection)
    section_level = Column(Integer, nullable=False)
    
    # Page information
    start_page = Column(Integer, nullable=False)
    end_page = Column(Integer, nullable=False)
    
    # Content metrics
    word_count = Column(Integer, nullable=False, default=0)
    segment_count = Column(Integer, nullable=False, default=0)  # Number of text segments from this section
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<BookSection(id='{self.section_id}', title='{self.title}', level={self.section_level})>"