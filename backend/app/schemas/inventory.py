from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    location_type: str = Field("store", pattern="^(store|warehouse|vault)$")
    settings: Optional[Dict[str, Any]] = None

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InventoryItemBase(BaseModel):
    coin_id: int
    location_id: int
    quantity: int = Field(..., ge=1)
    reserved_quantity: int = Field(0, ge=0)
    notes: Optional[str] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: int
    available_quantity: int
    last_counted: Optional[datetime]
    last_moved: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InventoryMovementBase(BaseModel):
    coin_id: int
    from_location_id: Optional[int] = None
    to_location_id: int
    quantity: int = Field(..., ge=1)
    movement_type: str = Field(..., pattern="^(transfer|sale|adjustment|count)$")
    reason: Optional[str] = None
    reference_id: Optional[str] = None

class InventoryMovementCreate(InventoryMovementBase):
    pass

class InventoryMovementResponse(InventoryMovementBase):
    id: int
    moved_by: str
    moved_at: datetime
    
    class Config:
        from_attributes = True

class DeadStockAnalysisResponse(BaseModel):
    id: int
    coin_id: int
    days_since_last_sale: Optional[int]
    days_since_added: Optional[int]
    profit_margin: Optional[Decimal]
    category: str
    analysis_date: datetime
    criteria_used: Dict[str, Any]
    
    # Coin details
    coin_title: str
    coin_value: Decimal
    coin_category: str
    
    class Config:
        from_attributes = True

class LocationInventory(BaseModel):
    location_id: int
    location_name: str
    coin_count: int
    total_value: Decimal
    profit_margin: Decimal
    last_updated: datetime

class MarginAnalysis(BaseModel):
    category: str
    average_margin: Decimal
    min_margin: Decimal
    max_margin: Decimal
    coin_count: int
    total_value: Decimal

class TurnoverAnalysisResponse(BaseModel):
    id: int
    coin_id: int
    analysis_period_start: datetime
    analysis_period_end: datetime
    days_since_last_sale: Optional[int]
    days_since_added: Optional[int]
    sales_count: int
    total_revenue: Decimal
    turnover_category: str
    sales_velocity: Decimal
    profit_margin: Decimal
    analysis_date: datetime
    
    # Coin details
    coin_title: str
    coin_value: Decimal
    
    class Config:
        from_attributes = True

class InventoryMetricsResponse(BaseModel):
    period_type: str
    period_start: datetime
    period_end: datetime
    total_coins: int
    total_value: Decimal
    dead_stock_count: int
    dead_stock_value: Decimal
    turnover_rate: Decimal
    location_breakdown: List[LocationInventory]
    category_breakdown: List[Dict[str, Any]]
    profit_margin_analysis: List[MarginAnalysis]
    average_value_per_coin: Decimal
    dead_stock_percentage: Decimal
    calculated_at: datetime
    
    class Config:
        from_attributes = True

class InventoryMetricsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    location_filter: Optional[str] = None
    category_filter: Optional[str] = None
    period_type: str = Field("daily", pattern="^(daily|weekly|monthly)$")

class BulkOperationRequest(BaseModel):
    operation_type: str = Field(..., pattern="^(price_update|category_change|status_change|location_transfer)$")
    selected_coins: List[int]
    operation_data: Dict[str, Any]
    individual_tracking: bool = True

class BulkOperationPreview(BaseModel):
    coin_id: int
    coin_title: str
    current_value: Any
    new_value: Any
    change_description: str

class BulkOperationResponse(BaseModel):
    operation_id: str
    operation_type: str
    coins_affected: int
    preview_changes: List[BulkOperationPreview]
    estimated_time: str
    warnings: List[str] = []

class InventoryAlertRule(BaseModel):
    id: int
    name: str
    alert_type: str = Field(..., pattern="^(low_inventory|dead_stock|turnover_threshold)$")
    conditions: Dict[str, Any]
    product_specific: bool = False
    product_id: Optional[int] = None
    enabled: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

class InventoryAlertRuleCreate(BaseModel):
    name: str
    alert_type: str = Field(..., pattern="^(low_inventory|dead_stock|turnover_threshold)$")
    conditions: Dict[str, Any]
    product_specific: bool = False
    product_id: Optional[int] = None


