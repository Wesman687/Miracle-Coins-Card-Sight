from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class CoinMetadata(Base):
    """Dynamic metadata fields for coins based on their category"""
    __tablename__ = "coin_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(200), nullable=False)  # e.g., "coins.year", "coins.grade"
    field_value = Column(Text)  # Store as text, can be converted based on field type
    field_type = Column(String(50), nullable=False)  # text, number, boolean, select, date
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # coin = relationship("Coin", back_populates="metadata")  # Temporarily disabled
    
    def __repr__(self):
        return f"<CoinMetadata(coin_id={self.coin_id}, field={self.field_name}, value={self.field_value})>"
