from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class CoinBase(BaseModel):
    sku: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    year: Optional[int] = Field(None, ge=1800, le=2030)
    denomination: Optional[str] = Field(None, max_length=50)
    mint_mark: Optional[str] = Field(None, max_length=10)
    grade: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    condition_notes: Optional[str] = None
    is_silver: bool = Field(default=False)
    silver_percent: Optional[float] = Field(None, ge=0, le=100)
    silver_content_oz: Optional[float] = Field(None, ge=0)
    paid_price: Optional[float] = Field(None, ge=0)
    # Note: Some fields removed to match actual database schema
    quantity: int = Field(default=1, ge=1)
    status: str = Field(default="active", pattern="^(active|sold|inactive|pending)$")
    tags: Optional[List[str]] = Field(default=[], description="Tags for categorization")
    shopify_metadata: Optional[Dict[str, Any]] = Field(default={}, description="Shopify product metadata")
    collection_ids: Optional[List[int]] = Field(default=[], description="Collection IDs this coin belongs to")

class CoinCreate(CoinBase):
    pass

class CoinUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    year: Optional[int] = Field(None, ge=1800, le=2030)
    denomination: Optional[str] = Field(None, max_length=50)
    mint_mark: Optional[str] = Field(None, max_length=10)
    grade: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    condition_notes: Optional[str] = None
    is_silver: Optional[bool] = None
    silver_percent: Optional[float] = Field(None, ge=0, le=100)
    silver_content_oz: Optional[float] = Field(None, ge=0)
    paid_price: Optional[float] = Field(None, ge=0)
    # Note: Some fields removed to match actual database schema
    quantity: Optional[int] = Field(None, ge=1)
    status: Optional[str] = Field(None, pattern="^(active|sold|inactive|pending)$")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    shopify_metadata: Optional[Dict[str, Any]] = Field(None, description="Shopify product metadata")
    collection_ids: Optional[List[int]] = Field(default=[], description="Collection IDs this coin belongs to")

class CoinResponse(CoinBase):
    id: int
    computed_price: Optional[float] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    images: Optional[List[str]] = Field(default=[], description="Image URLs for this coin")
    
    class Config:
        from_attributes = True
