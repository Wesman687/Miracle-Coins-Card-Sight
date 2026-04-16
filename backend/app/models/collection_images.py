from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class CollectionImage(Base):
    __tablename__ = "collection_images"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(200), nullable=True)
    caption = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False, index=True)
    sort_order = Column(Integer, default=0)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    width = Column(Integer, nullable=True)  # Image width in pixels
    height = Column(Integer, nullable=True)  # Image height in pixels
    mime_type = Column(String(100), nullable=True)  # MIME type of the image
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collection = relationship("Collection", back_populates="images")
    
    def __repr__(self):
        return f"<CollectionImage(id={self.id}, collection_id={self.collection_id}, is_featured={self.is_featured})>"
    
    @property
    def file_size_formatted(self):
        """Return formatted file size"""
        if not self.file_size:
            return None
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    @property
    def dimensions_formatted(self):
        """Return formatted dimensions"""
        if self.width and self.height:
            return f"{self.width} × {self.height}"
        return None

