"""
Two-Part SKU System Models
Format: [PREFIX]-[SEQUENCE] (e.g., ASE-001, MOR-002)
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SKUPrefix(Base):
    __tablename__ = "sku_prefixes"
    
    id = Column(Integer, primary_key=True, index=True)
    prefix = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(Text)
    auto_increment = Column(Boolean, default=True)
    current_sequence = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sequences = relationship("SKUSequence", back_populates="prefix_ref")

class SKUSequence(Base):
    __tablename__ = "sku_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    prefix = Column(String(20), ForeignKey("sku_prefixes.prefix"), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)
    used_at = Column(DateTime(timezone=True), server_default=func.now())
    coin_id = Column(Integer, ForeignKey("coins.id"))
    
    # Relationships
    prefix_ref = relationship("SKUPrefix", back_populates="sequences")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('prefix', 'sequence_number', name='uq_prefix_sequence'),
    )
