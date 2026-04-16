# backend/app/schemas/bulk_operations.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BulkOperationType(str, Enum):
    PURCHASE = "purchase"
    TRANSFER = "transfer"
    PRICE_UPDATE = "price_update"
    STATUS_CHANGE = "status_change"

class BulkOperationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BulkItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Request schemas
class CoinData(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50, description="SKU for the coin")
    name: str = Field(..., min_length=1, max_length=255, description="Coin name")
    year: int = Field(..., ge=1800, le=2030, description="Year of the coin")
    denomination: Optional[str] = Field(None, max_length=50)
    mint_mark: Optional[str] = Field(None, max_length=10)
    grade: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)
    condition_notes: Optional[str] = Field(None)
    is_silver: bool = Field(False)
    silver_percent: Optional[float] = Field(None, ge=0, le=100)
    silver_content_oz: Optional[float] = Field(None, ge=0)
    paid_price: float = Field(..., ge=0, le=1000000, description="Paid price for the coin")
    price_strategy: str = Field("fixed_price", description="Pricing strategy")
    quantity: int = Field(1, ge=1, le=10000, description="Quantity of this coin")
    status: str = Field("active", description="Status of the coin")

class BulkOperationCreate(BaseModel):
    operation_type: BulkOperationType
    description: str = Field(..., min_length=1, max_length=500)
    coins: List[CoinData] = Field(..., min_items=1, max_items=10000000)  # 10M max
    created_by: Optional[int] = Field(1)  # Default user ID
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('coins')
    def validate_coins(cls, v):
        if len(v) > 10000000:
            raise ValueError('Maximum 10,000,000 coins per bulk operation')
        return v

class BulkTransferRequest(BaseModel):
    operation_type: BulkOperationType = BulkOperationType.TRANSFER
    description: str = Field(..., min_length=1, max_length=500)
    coin_ids: List[int] = Field(..., min_items=1, max_items=10000000)
    from_location: Optional[str] = Field(None)
    to_location: str = Field(..., min_length=1, max_length=100)
    created_by: Optional[int] = Field(1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class BulkPriceUpdateRequest(BaseModel):
    operation_type: BulkOperationType = BulkOperationType.PRICE_UPDATE
    description: str = Field(..., min_length=1, max_length=500)
    coin_ids: List[int] = Field(..., min_items=1, max_items=10000000)
    price_strategy: str = Field(..., description="New pricing strategy")
    price_multiplier: Optional[float] = Field(None, ge=0.1, le=10)
    fixed_price: Optional[float] = Field(None, ge=0, le=1000000)
    created_by: Optional[int] = Field(1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class BulkStatusChangeRequest(BaseModel):
    operation_type: BulkOperationType = BulkOperationType.STATUS_CHANGE
    description: str = Field(..., min_length=1, max_length=500)
    coin_ids: List[int] = Field(..., min_items=1, max_items=10000000)
    new_status: str = Field(..., min_length=1, max_length=50)
    created_by: Optional[int] = Field(1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

# Response schemas
class BulkOperationItemResponse(BaseModel):
    id: int
    bulk_operation_id: int
    coin_id: int
    status: BulkItemStatus
    error_message: Optional[str]
    processed_at: Optional[datetime]
    item_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class BulkOperationResponse(BaseModel):
    id: int
    operation_type: BulkOperationType
    description: str
    total_items: int
    processed_items: int
    failed_items: int
    status: BulkOperationStatus
    created_by: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    operation_metadata: Optional[Dict[str, Any]] = None
    items: Optional[List[BulkOperationItemResponse]] = None

    class Config:
        from_attributes = True

class BulkOperationStatusResponse(BaseModel):
    id: int
    status: BulkOperationStatus
    total_items: int
    processed_items: int
    failed_items: int
    progress_percentage: float
    estimated_completion: Optional[datetime]
    errors: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True

class BulkOperationListResponse(BaseModel):
    operations: List[BulkOperationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class BulkOperationStatsResponse(BaseModel):
    total_operations: int
    completed_operations: int
    failed_operations: int
    pending_operations: int
    total_coins_processed: int
    average_operation_size: float
    success_rate: float
    last_operation_date: Optional[datetime]
