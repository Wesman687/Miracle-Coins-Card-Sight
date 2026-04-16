from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    shopify_collection_id = Column(String(50), nullable=True, unique=True)
    
    # Collection metadata
    color = Column(String(7), default="#3b82f6")  # Default blue color
    icon = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)  # Single image URL
    # is_active = Column(Boolean, default=True)  # Not in database
    
    # Temporary: Keep these columns until migration is run
    sort_order = Column(Integer, default=0)
    default_markup = Column(Numeric(6, 3), default=1.3)
    
    # Rich text support - column may not exist in database yet
    description_html = Column(Text, nullable=True)  # Rich text description
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # coins = relationship("Coin", back_populates="collection_rel")  # Temporarily disabled
    metadata_fields = relationship("CollectionMetadata", back_populates="collection", cascade="all, delete-orphan")
    images = relationship("CollectionImage", back_populates="collection", cascade="all, delete-orphan")
    
    @property
    def coin_count(self):
        """Get the count of coins in this collection"""
        # Note: coins relationship is disabled due to circular import issues
        # Return 0 for now, can be calculated via direct query if needed
        return 0
    
    @property
    def total_value(self):
        """Calculate total value of coins in this collection"""
        # Note: coins relationship is disabled due to circular import issues
        # Return 0 for now, can be calculated via direct query if needed
        return 0
    
    @property
    def featured_image(self):
        """Get the featured image for this collection"""
        if not self.images:
            return None
        featured = next((img for img in self.images if img.is_featured), None)
        if featured:
            return featured
        # If no featured image, return the first image
        return self.images[0] if self.images else None
    
    @property
    def average_price(self):
        """Calculate average price of coins in this collection"""
        # Note: coins relationship is disabled due to circular import issues
        # Return 0 for now, can be calculated via direct query if needed
        return 0
