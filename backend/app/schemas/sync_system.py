"""
Real-Time Sync System Schemas
Multi-channel synchronization with conflict resolution
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    SHOPIFY = "SHOPIFY"
    EBAY = "EBAY"
    ETSY = "ETSY"
    IN_STORE = "IN_STORE"
    AUCTION = "AUCTION"
    DIRECT = "DIRECT"

class SyncType(str, Enum):
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"
    PRODUCTS = "PRODUCTS"
    INVENTORY = "INVENTORY"
    ORDERS = "ORDERS"

class SyncStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ConflictType(str, Enum):
    PRICE_MISMATCH = "PRICE_MISMATCH"
    INVENTORY_MISMATCH = "INVENTORY_MISMATCH"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    DUPLICATE_SKU = "DUPLICATE_SKU"
    DATA_MISMATCH = "DATA_MISMATCH"

class ResolutionStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"
    ESCALATED = "ESCALATED"

class QueueOperation(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SYNC = "SYNC"

class QueueStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Sync Channel Schemas
class SyncChannelBase(BaseModel):
    channel_name: str = Field(..., max_length=50)
    channel_type: ChannelType
    is_active: bool = True
    sync_frequency_minutes: int = Field(60, ge=1, le=10080)  # 1 minute to 1 week
    sync_config: Optional[Dict[str, Any]] = None

class SyncChannelCreate(SyncChannelBase):
    pass

class SyncChannelUpdate(BaseModel):
    channel_name: Optional[str] = Field(None, max_length=50)
    channel_type: Optional[ChannelType] = None
    is_active: Optional[bool] = None
    sync_frequency_minutes: Optional[int] = Field(None, ge=1, le=10080)
    sync_config: Optional[Dict[str, Any]] = None

class SyncChannelResponse(SyncChannelBase):
    id: int
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Sync Log Schemas
class SyncLogBase(BaseModel):
    channel_id: int
    sync_type: SyncType
    status: SyncStatus
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    error_message: Optional[str] = None
    sync_data: Optional[Dict[str, Any]] = None

class SyncLogCreate(SyncLogBase):
    pass

class SyncLogUpdate(BaseModel):
    status: Optional[SyncStatus] = None
    completed_at: Optional[datetime] = None
    items_processed: Optional[int] = None
    items_successful: Optional[int] = None
    items_failed: Optional[int] = None
    error_message: Optional[str] = None
    sync_data: Optional[Dict[str, Any]] = None

class SyncLogResponse(SyncLogBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Sync Conflict Schemas
class SyncConflictBase(BaseModel):
    channel_id: int
    conflict_type: ConflictType
    resource_type: str = Field(..., max_length=50)
    resource_id: str = Field(..., max_length=100)
    local_data: Optional[Dict[str, Any]] = None
    remote_data: Optional[Dict[str, Any]] = None
    conflict_details: Optional[Dict[str, Any]] = None
    resolution_status: ResolutionStatus = ResolutionStatus.PENDING
    resolved_by: Optional[str] = Field(None, max_length=100)
    resolution_notes: Optional[str] = None

class SyncConflictCreate(SyncConflictBase):
    pass

class SyncConflictUpdate(BaseModel):
    resolution_status: Optional[ResolutionStatus] = None
    resolved_by: Optional[str] = Field(None, max_length=100)
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class SyncConflictResponse(SyncConflictBase):
    id: int
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Sync Queue Schemas
class SyncQueueBase(BaseModel):
    channel_id: int
    operation: QueueOperation
    resource_type: str = Field(..., max_length=50)
    resource_id: str = Field(..., max_length=100)
    resource_data: Optional[Dict[str, Any]] = None
    priority: int = Field(5, ge=1, le=10)  # 1=highest, 10=lowest
    max_retries: int = Field(3, ge=0, le=10)

class SyncQueueCreate(SyncQueueBase):
    pass

class SyncQueueUpdate(BaseModel):
    status: Optional[QueueStatus] = None
    retry_count: Optional[int] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SyncQueueResponse(SyncQueueBase):
    id: int
    status: QueueStatus
    retry_count: int
    scheduled_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Sync Status Schemas
class SyncStatusResponse(BaseModel):
    id: int
    channel_id: int
    last_full_sync: Optional[datetime] = None
    last_incremental_sync: Optional[datetime] = None
    last_product_sync: Optional[datetime] = None
    last_inventory_sync: Optional[datetime] = None
    last_order_sync: Optional[datetime] = None
    sync_in_progress: bool
    current_sync_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard and Statistics Schemas
class SyncDashboardStats(BaseModel):
    total_channels: int
    active_channels: int
    syncs_in_progress: int
    pending_conflicts: int
    queue_items_pending: int
    recent_syncs: List[Dict[str, Any]]
    recent_conflicts: List[Dict[str, Any]]
    channel_status: List[Dict[str, Any]]

class SyncRequest(BaseModel):
    channel_id: int
    sync_type: SyncType
    force_full_sync: bool = False
    sync_config: Optional[Dict[str, Any]] = None

class ConflictResolutionRequest(BaseModel):
    conflict_id: int
    resolution: str = Field(..., pattern="^(USE_LOCAL|USE_REMOTE|MANUAL|IGNORE)$")
    resolved_by: str = Field(..., max_length=100)
    resolution_notes: Optional[str] = None

class QueueProcessRequest(BaseModel):
    max_items: int = Field(100, ge=1, le=1000)
    priority_filter: Optional[int] = Field(None, ge=1, le=10)
