from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

class CoinMetadataBase(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=200)
    field_value: Optional[str] = None
    field_type: str = Field(..., pattern="^(text|number|boolean|select|date)$")

class CoinMetadataCreate(CoinMetadataBase):
    coin_id: int

class CoinMetadataUpdate(BaseModel):
    field_value: Optional[str] = None

class CoinMetadata(CoinMetadataBase):
    id: int
    coin_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CoinMetadataBulkUpdate(BaseModel):
    coin_id: int
    metadata: Dict[str, Any] = Field(..., description="Field name to value mapping")

class CoinWithMetadata(BaseModel):
    id: int
    sku: str
    title: str
    year: Optional[int] = None
    denomination: Optional[str] = None
    mint_mark: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    condition_notes: Optional[str] = None
    is_silver: bool = False
    silver_percent: Optional[Decimal] = None
    silver_content_oz: Optional[Decimal] = None
    paid_price: Optional[Decimal] = None
    price_strategy: str = "spot_multiplier"
    price_multiplier: Decimal = Decimal('1.300')
    base_from_entry: bool = True
    entry_spot: Optional[Decimal] = None
    entry_melt: Optional[Decimal] = None
    override_price: bool = False
    override_value: Optional[Decimal] = None
    computed_price: Optional[Decimal] = None
    quantity: int = 1
    status: str = "active"
    created_by: Optional[str] = None
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Dynamic metadata
    metadata: List[CoinMetadata] = []
    
    # Category information
    category_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class CoinCreateWithMetadata(BaseModel):
    # Basic coin fields
    sku: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    year: Optional[int] = None
    denomination: Optional[str] = None
    mint_mark: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    condition_notes: Optional[str] = None
    is_silver: bool = False
    silver_percent: Optional[Decimal] = None
    silver_content_oz: Optional[Decimal] = None
    paid_price: Optional[Decimal] = None
    price_strategy: str = "spot_multiplier"
    price_multiplier: Decimal = Decimal('1.300')
    base_from_entry: bool = True
    entry_spot: Optional[Decimal] = None
    entry_melt: Optional[Decimal] = None
    override_price: bool = False
    override_value: Optional[Decimal] = None
    computed_price: Optional[Decimal] = None
    quantity: int = 1
    status: str = "active"
    created_by: Optional[str] = None
    category_id: Optional[int] = None
    
    # Dynamic metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Field name to value mapping")

class CoinUpdateWithMetadata(BaseModel):
    # Basic coin fields (all optional for updates)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    year: Optional[int] = None
    denomination: Optional[str] = None
    mint_mark: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    condition_notes: Optional[str] = None
    is_silver: Optional[bool] = None
    silver_percent: Optional[Decimal] = None
    silver_content_oz: Optional[Decimal] = None
    paid_price: Optional[Decimal] = None
    price_strategy: Optional[str] = None
    price_multiplier: Optional[Decimal] = None
    base_from_entry: Optional[bool] = None
    entry_spot: Optional[Decimal] = None
    entry_melt: Optional[Decimal] = None
    override_price: Optional[bool] = None
    override_value: Optional[Decimal] = None
    computed_price: Optional[Decimal] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
    
    # Dynamic metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Field name to value mapping")

class CoinListResponse(BaseModel):
    coins: List[CoinWithMetadata]
    total: int
    page: int
    per_page: int
    total_pages: int

class CategoryMetadataTemplate(BaseModel):
    """Template for category metadata fields"""
    field_name: str
    field_type: str
    field_label: str
    field_description: Optional[str] = None
    is_required: bool = False
    default_value: Optional[str] = None
    select_options: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None
