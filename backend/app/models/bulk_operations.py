# backend/app/models/bulk_operations.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class BulkOperation(Base):
    __tablename__ = "bulk_operations"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    total_items = Column(Integer, nullable=False)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    status = Column(String(20), default='pending', index=True)
    created_by = Column(Integer)  # Will reference users table when available
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    operation_metadata = Column(JSON)
    
    # Relationships
    items = relationship("BulkOperationItem", back_populates="bulk_operation", cascade="all, delete-orphan")

class BulkOperationItem(Base):
    __tablename__ = "bulk_operation_items"
    
    id = Column(Integer, primary_key=True, index=True)
    bulk_operation_id = Column(Integer, ForeignKey("bulk_operations.id"), nullable=False, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    status = Column(String(20), default='pending', index=True)
    error_message = Column(Text)
    processed_at = Column(DateTime(timezone=True))
    item_metadata = Column(JSON)
    
    # Relationships
    bulk_operation = relationship("BulkOperation", back_populates="items")
