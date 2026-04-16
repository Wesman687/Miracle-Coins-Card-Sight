from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid

# Enums for better type safety
class CoinStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    INACTIVE = "inactive"
    PENDING = "pending"

class ListingStatus(str, Enum):
    UNLISTED = "unlisted"
    LISTED = "listed"
    SOLD = "sold"
    ERROR = "error"

class PricingStrategy(str, Enum):
    SPOT_MULTIPLIER = "spot_multiplier"
    FIXED_PRICE = "fixed_price"
    ENTRY_BASED = "entry_based"

class MarketplaceChannel(str, Enum):
    SHOPIFY = "shopify"
    EBAY = "ebay"
    ETSY = "etsy"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"

class MetalType(str, Enum):
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    PALLADIUM = "palladium"

# Base coin schema with comprehensive types
class CoinBase(BaseModel):
    sku: Optional[str] = Field(None, max_length=100, description="Unique SKU identifier")
    title: str = Field(..., min_length=1, max_length=255, description="Coin title")
    year: Optional[int] = Field(None, ge=1800, le=2030, description="Year of minting")
    denomination: Optional[str] = Field(None, max_length=50, description="Denomination (e.g., $1, 50¢)")
    mint_mark: Optional[str] = Field(None, max_length=10, description="Mint mark (S, D, CC, etc.)")
    grade: Optional[str] = Field(None, max_length=20, description="Coin grade (MS65, AU58, etc.)")
    category: Optional[str] = Field(None, max_length=100, description="Coin category")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    condition_notes: Optional[str] = Field(None, max_length=1000, description="Condition notes")
    is_silver: bool = Field(False, description="Whether this is a silver coin")
    silver_percent: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4, description="Silver percentage (0.900)")
    silver_content_oz: Optional[Decimal] = Field(None, ge=0, decimal_places=4, description="Silver content in ounces")
    paid_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Price paid for the coin")
    price_strategy: PricingStrategy = Field(PricingStrategy.SPOT_MULTIPLIER, description="Pricing strategy")
    price_multiplier: Decimal = Field(Decimal('1.300'), ge=0.1, le=10, decimal_places=3, description="Price multiplier")
    base_from_entry: bool = Field(True, description="Use entry spot for base calculation")
    entry_spot: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Spot price at entry")
    entry_melt: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Melt value at entry")
    override_price: bool = Field(False, description="Override computed price")
    override_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Override price value")
    quantity: int = Field(1, ge=1, description="Quantity in inventory")
    status: CoinStatus = Field(CoinStatus.ACTIVE, description="Coin status")

    @validator('sku')
    def validate_sku(cls, v):
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('SKU must contain only alphanumeric characters, hyphens, and underscores')
        return v

    @validator('year')
    def validate_year(cls, v):
        if v and (v < 1800 or v > datetime.now().year + 1):
            raise ValueError('Year must be between 1800 and current year + 1')
        return v

class CoinCreate(CoinBase):
    pass

class CoinUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    year: Optional[int] = Field(None, ge=1800, le=2030)
    denomination: Optional[str] = Field(None, max_length=50)
    mint_mark: Optional[str] = Field(None, max_length=10)
    grade: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    condition_notes: Optional[str] = Field(None, max_length=1000)
    is_silver: Optional[bool] = None
    silver_percent: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4)
    silver_content_oz: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    paid_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    price_strategy: Optional[PricingStrategy] = None
    price_multiplier: Optional[Decimal] = Field(None, ge=0.1, le=10, decimal_places=3)
    base_from_entry: Optional[bool] = None
    entry_spot: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    entry_melt: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    override_price: Optional[bool] = None
    override_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    quantity: Optional[int] = Field(None, ge=1)
    status: Optional[CoinStatus] = None

class Coin(CoinBase):
    id: int = Field(..., description="Unique coin identifier")
    computed_price: Optional[Decimal] = Field(None, decimal_places=2, description="Computed selling price")
    created_by: Optional[str] = Field(None, description="User who created the coin")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

# Image schemas
class CoinImageBase(BaseModel):
    url: str = Field(..., description="Image URL")
    alt: str = Field(..., max_length=255, description="Alt text for accessibility")
    sort_order: int = Field(0, ge=0, description="Display order")

class CoinImageCreate(CoinImageBase):
    coin_id: int = Field(..., description="Associated coin ID")

class CoinImage(CoinImageBase):
    id: int = Field(..., description="Unique image identifier")
    coin_id: int = Field(..., description="Associated coin ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Listing schemas
class ListingBase(BaseModel):
    channel: MarketplaceChannel = Field(..., description="Marketplace channel")
    external_id: Optional[str] = Field(None, max_length=255, description="External marketplace ID")
    external_variant_id: Optional[str] = Field(None, max_length=255, description="External variant ID")
    url: Optional[str] = Field(None, max_length=500, description="Listing URL")
    status: ListingStatus = Field(ListingStatus.UNLISTED, description="Listing status")

class ListingCreate(ListingBase):
    coin_id: int = Field(..., description="Associated coin ID")

class Listing(ListingBase):
    id: int = Field(..., description="Unique listing identifier")
    coin_id: int = Field(..., description="Associated coin ID")
    last_error: Optional[str] = Field(None, description="Last error message")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Order schemas
class OrderBase(BaseModel):
    channel: MarketplaceChannel = Field(..., description="Marketplace channel")
    external_order_id: str = Field(..., max_length=255, description="External order ID")
    qty: int = Field(1, ge=1, description="Quantity sold")
    sold_price: Decimal = Field(..., ge=0, decimal_places=2, description="Selling price")
    fees: Decimal = Field(Decimal('0.00'), ge=0, decimal_places=2, description="Marketplace fees")
    shipping_cost: Decimal = Field(Decimal('0.00'), ge=0, decimal_places=2, description="Shipping cost")

class OrderCreate(OrderBase):
    coin_id: int = Field(..., description="Associated coin ID")

class Order(OrderBase):
    id: int = Field(..., description="Unique order identifier")
    coin_id: int = Field(..., description="Associated coin ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

# Spot price schemas
class SpotPriceBase(BaseModel):
    metal: MetalType = Field(..., description="Metal type")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Spot price")
    source: Optional[str] = Field(None, max_length=100, description="Price source")

class SpotPriceCreate(SpotPriceBase):
    pass

class SpotPrice(SpotPriceBase):
    id: int = Field(..., description="Unique spot price identifier")
    fetched_at: datetime = Field(..., description="Fetch timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

# Audit log schemas
class AuditLogBase(BaseModel):
    actor: Optional[str] = Field(None, description="User who performed the action")
    action: str = Field(..., max_length=50, description="Action performed")
    entity: str = Field(..., max_length=50, description="Entity type")
    entity_id: Optional[str] = Field(None, max_length=50, description="Entity identifier")
    payload: Optional[Dict[str, Any]] = Field(None, description="Additional data")

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int = Field(..., description="Unique audit log identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Dashboard KPI schemas
class DashboardKPIs(BaseModel):
    inventory_melt_value: Decimal = Field(..., decimal_places=2, description="Total melt value of inventory")
    inventory_list_value: Decimal = Field(..., decimal_places=2, description="Total list value of inventory")
    gross_profit: Decimal = Field(..., decimal_places=2, description="Gross profit potential")
    melt_vs_list_ratio: Decimal = Field(..., decimal_places=4, description="Melt to list ratio")
    total_coins: int = Field(..., ge=0, description="Total number of coins")
    active_listings: int = Field(0, ge=0, description="Number of active listings")
    sold_this_month: int = Field(0, ge=0, description="Coins sold this month")
    metals_prices: Dict[str, Dict[str, Any]] = Field(..., description="Current metals spot prices")
    
    class Config:
        json_encoders = {
            Decimal: str
        }

# AI Evaluation schemas
class AIEvaluationRequest(BaseModel):
    coin_data: CoinBase = Field(..., description="Coin data to evaluate")
    images: Optional[List[str]] = Field(None, description="Image URLs for analysis")

class AIEvaluationResponse(BaseModel):
    suggested_price: Decimal = Field(..., decimal_places=2, description="AI suggested price")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in suggestion")
    selling_recommendation: str = Field(..., description="Individual vs bulk recommendation")
    reasoning: str = Field(..., description="AI reasoning for suggestions")
    market_analysis: Dict[str, Any] = Field(..., description="Market analysis data")
    
    class Config:
        json_encoders = {
            Decimal: str
        }

# Bulk operations
class BulkImportRequest(BaseModel):
    csv_data: str = Field(..., description="Base64 encoded CSV content")
    update_existing: bool = Field(False, description="Update existing coins")

class BulkRepriceRequest(BaseModel):
    coin_ids: Optional[List[int]] = Field(None, description="Specific coin IDs to reprice")
    new_multiplier: Optional[Decimal] = Field(None, ge=0.1, le=10, decimal_places=3, description="New multiplier")
    force_refresh_spot: bool = Field(False, description="Force spot price refresh")

# Collection schemas
class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: Optional[str] = Field(None, max_length=1000, description="Collection description")
    category: Optional[str] = Field(None, max_length=100, description="Collection category")

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)

class Collection(CollectionBase):
    id: int = Field(..., description="Unique collection identifier")
    created_by: Optional[str] = Field(None, description="User who created the collection")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    coin_count: int = Field(0, ge=0, description="Number of coins in collection")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# API Response schemas
class APIResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="Error messages")

class PaginatedResponse(BaseModel):
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=1, description="Total number of pages")



