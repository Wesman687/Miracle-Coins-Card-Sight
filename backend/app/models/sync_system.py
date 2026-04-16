"""
Real-Time Sync System Models
Multi-channel synchronization with conflict resolution
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SyncChannel(Base):
    __tablename__ = "sync_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String(50), unique=True, nullable=False, index=True)
    channel_type = Column(String(20), nullable=False, index=True)  # SHOPIFY, EBAY, ETSY, IN_STORE, AUCTION, DIRECT
    is_active = Column(Boolean, default=True, index=True)
    sync_frequency_minutes = Column(Integer, default=60)
    last_sync_at = Column(DateTime(timezone=True))
    next_sync_at = Column(DateTime(timezone=True))
    sync_config = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sync_logs = relationship("SyncLog", back_populates="channel")
    sync_conflicts = relationship("SyncConflict", back_populates="channel")
    sync_queue = relationship("SyncQueue", back_populates="channel")
    sync_status = relationship("SyncStatus", back_populates="channel", uselist=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("channel_type IN ('SHOPIFY', 'EBAY', 'ETSY', 'IN_STORE', 'AUCTION', 'DIRECT')", name='check_channel_type_valid'),
    )

class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("sync_channels.id"), nullable=False, index=True)
    sync_type = Column(String(20), nullable=False)  # FULL, INCREMENTAL, PRODUCTS, INVENTORY, ORDERS
    status = Column(String(20), nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    items_processed = Column(Integer, default=0)
    items_successful = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_message = Column(String)
    sync_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    channel = relationship("SyncChannel", back_populates="sync_logs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("sync_type IN ('FULL', 'INCREMENTAL', 'PRODUCTS', 'INVENTORY', 'ORDERS')", name='check_sync_type_valid'),
        CheckConstraint("status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')", name='check_sync_status_valid'),
    )

class SyncConflict(Base):
    __tablename__ = "sync_conflicts"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("sync_channels.id"), nullable=False, index=True)
    conflict_type = Column(String(50), nullable=False, index=True)  # PRICE_MISMATCH, INVENTORY_MISMATCH, PRODUCT_NOT_FOUND, DUPLICATE_SKU
    resource_type = Column(String(50), nullable=False)  # PRODUCT, INVENTORY, ORDER
    resource_id = Column(String(100), nullable=False)
    local_data = Column(JSON)
    remote_data = Column(JSON)
    conflict_details = Column(JSON)
    resolution_status = Column(String(20), default='PENDING', index=True)  # PENDING, RESOLVED, IGNORED, ESCALATED
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    channel = relationship("SyncChannel", back_populates="sync_conflicts")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("conflict_type IN ('PRICE_MISMATCH', 'INVENTORY_MISMATCH', 'PRODUCT_NOT_FOUND', 'DUPLICATE_SKU', 'DATA_MISMATCH')", name='check_conflict_type_valid'),
        CheckConstraint("resolution_status IN ('PENDING', 'RESOLVED', 'IGNORED', 'ESCALATED')", name='check_resolution_status_valid'),
        Index('idx_sync_conflicts_resource', 'resource_type', 'resource_id'),
    )

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("sync_channels.id"), nullable=False, index=True)
    operation = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, SYNC
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    resource_data = Column(JSON)
    priority = Column(Integer, default=5, index=True)  # 1=highest, 10=lowest
    status = Column(String(20), default='PENDING', index=True)  # PENDING, PROCESSING, COMPLETED, FAILED
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True))
    error_message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    channel = relationship("SyncChannel", back_populates="sync_queue")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("operation IN ('CREATE', 'UPDATE', 'DELETE', 'SYNC')", name='check_operation_valid'),
        CheckConstraint("status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')", name='check_queue_status_valid'),
    )

class SyncStatus(Base):
    __tablename__ = "sync_status"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("sync_channels.id"), nullable=False, index=True)
    last_full_sync = Column(DateTime(timezone=True))
    last_incremental_sync = Column(DateTime(timezone=True))
    last_product_sync = Column(DateTime(timezone=True))
    last_inventory_sync = Column(DateTime(timezone=True))
    last_order_sync = Column(DateTime(timezone=True))
    sync_in_progress = Column(Boolean, default=False)
    current_sync_id = Column(Integer, ForeignKey("sync_logs.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    channel = relationship("SyncChannel", back_populates="sync_status")
    current_sync = relationship("SyncLog")
