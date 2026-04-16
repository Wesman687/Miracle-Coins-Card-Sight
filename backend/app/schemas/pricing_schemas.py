from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

class PricingSource(str, Enum):
    """Enum for pricing data sources"""
    METALS_API = "metals-api"
    GOLDAPI = "goldapi"
    ALPHA_VANTAGE = "alpha-vantage"
    FIXER_IO = "fixer-io"
    EBAY = "ebay"
    APMEX = "apmex"
    JM_BULLION = "jm_bullion"
    SD_BULLION = "sd_bullion"
    FALLBACK = "fallback"
    AGGREGATED = "aggregated"

class DetectionMethod(str, Enum):
    """Enum for scam detection methods"""
    STATISTICAL_ANALYSIS = "statistical_analysis"
    PRICE_DEVIATION = "price_deviation"
    PATTERN_RECOGNITION = "pattern_recognition"
    MARKET_CONSISTENCY = "market_consistency"
    COMBINED = "combined"

class CalculationMethod(str, Enum):
    """Enum for price calculation methods"""
    OVERRIDE = "override"
    MARKUP_BASED = "markup_based"
    MARKET_BASED = "market_based"
    MIN_MARKUP_CONSTRAINT = "min_markup_constraint"
    MAX_MARKUP_CONSTRAINT = "max_markup_constraint"
    ERROR = "error"

# Spot Price Schemas
class SpotPriceRequest(BaseModel):
    """Request schema for fetching spot prices"""
    source: Optional[PricingSource] = None
    currency: str = "USD"
    
    @validator('currency')
    def validate_currency(cls, v):
        if v not in ['USD', 'EUR', 'GBP']:
            raise ValueError('Currency must be USD, EUR, or GBP')
        return v

class SpotPriceResponse(BaseModel):
    """Response schema for spot price data"""
    price: Decimal = Field(..., description="Current spot price")
    currency: str = Field(..., description="Currency code")
    source: PricingSource = Field(..., description="Data source")
    timestamp: datetime = Field(..., description="Price timestamp")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

# Market Data Schemas
class MarketDataRequest(BaseModel):
    """Request schema for market data scraping"""
    coin_type: str = Field(..., description="Type of coin to scrape")
    source: Optional[PricingSource] = None
    max_results: int = Field(20, ge=1, le=100, description="Maximum results to return")

class MarketDataResponse(BaseModel):
    """Response schema for market data"""
    avg_price: Decimal = Field(..., description="Average market price")
    min_price: Decimal = Field(..., description="Minimum market price")
    max_price: Decimal = Field(..., description="Maximum market price")
    sample_size: int = Field(..., ge=1, description="Number of samples")
    source: PricingSource = Field(..., description="Data source")
    timestamp: datetime = Field(..., description="Data timestamp")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

# Scam Detection Schemas
class ScamDetectionRequest(BaseModel):
    """Request schema for scam detection"""
    price: Decimal = Field(..., gt=0, description="Price to analyze")
    coin_type: str = Field(..., description="Type of coin")
    market_data: Optional[Dict[str, Any]] = None
    historical_data: Optional[List[Decimal]] = None

class ScamDetectionResponse(BaseModel):
    """Response schema for scam detection results"""
    is_scam: bool = Field(..., description="Whether price is detected as scam")
    probability: float = Field(..., ge=0.0, le=1.0, description="Scam probability")
    reasons: List[str] = Field(..., description="Reasons for scam detection")
    method: DetectionMethod = Field(..., description="Detection method used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    z_score: Optional[float] = Field(None, description="Statistical Z-score")
    price_deviation: Optional[float] = Field(None, description="Price deviation percentage")

# Pricing Engine Schemas
class PricingInputRequest(BaseModel):
    """Request schema for pricing calculation"""
    coin_id: int = Field(..., gt=0, description="Coin ID")
    coin_type: str = Field(..., description="Type of coin")
    weight_oz: Decimal = Field(..., gt=0, description="Weight in ounces")
    purity: Decimal = Field(..., gt=0, le=1, description="Metal purity")
    override_price: Optional[Decimal] = Field(None, gt=0, description="Override price")
    force_update: bool = Field(False, description="Force price update")

class PricingResultResponse(BaseModel):
    """Response schema for pricing calculation results"""
    final_price: Decimal = Field(..., description="Final calculated price")
    melt_value: Decimal = Field(..., description="Melt value")
    markup_factor: Decimal = Field(..., description="Markup factor applied")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    scam_detected: bool = Field(..., description="Whether scam was detected")
    sources_used: List[PricingSource] = Field(..., description="Data sources used")
    calculation_method: CalculationMethod = Field(..., description="Calculation method")
    timestamp: datetime = Field(..., description="Calculation timestamp")

# Database Model Schemas
class MarketPriceResponse(BaseModel):
    """Response schema for market price database records"""
    id: int
    coin_id: int
    spot_price: Decimal
    market_avg: Optional[Decimal]
    market_min: Optional[Decimal]
    market_max: Optional[Decimal]
    melt_value: Decimal
    markup_factor: Decimal
    final_price: Decimal
    confidence_score: Decimal
    scam_detected: bool
    scam_reason: Optional[str]
    source: str
    sample_size: int
    price_change_percent: Optional[Decimal]
    last_updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class PricingConfigResponse(BaseModel):
    """Response schema for pricing configuration"""
    id: int
    coin_type: str
    min_markup: Decimal
    max_markup: Decimal
    default_markup: Decimal
    scam_threshold: Decimal
    confidence_threshold: Decimal
    price_update_threshold: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PricingConfigRequest(BaseModel):
    """Request schema for updating pricing configuration"""
    coin_type: str = Field(..., description="Type of coin")
    min_markup: Decimal = Field(..., gt=1.0, le=5.0, description="Minimum markup factor")
    max_markup: Decimal = Field(..., gt=1.0, le=5.0, description="Maximum markup factor")
    default_markup: Decimal = Field(..., gt=1.0, le=5.0, description="Default markup factor")
    scam_threshold: Decimal = Field(..., gt=0.0, le=1.0, description="Scam detection threshold")
    confidence_threshold: Decimal = Field(..., gt=0.0, le=1.0, description="Confidence threshold")
    price_update_threshold: Decimal = Field(..., gt=0.0, le=10.0, description="Price update threshold percentage")
    is_active: bool = Field(True, description="Whether configuration is active")

class ScamDetectionResultResponse(BaseModel):
    """Response schema for scam detection results"""
    id: int
    coin_id: int
    market_price_id: int
    scam_probability: Decimal
    scam_reasons: List[str]
    detection_method: str
    confidence_score: Decimal
    price_deviation: Optional[Decimal]
    statistical_z_score: Optional[Decimal]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    is_false_positive: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PriceHistoryResponse(BaseModel):
    """Response schema for price history"""
    id: int
    coin_id: int
    old_price: Optional[Decimal]
    new_price: Decimal
    price_change_percent: Optional[Decimal]
    change_reason: str
    spot_price_at_change: Optional[Decimal]
    market_avg_at_change: Optional[Decimal]
    updated_by: str
    created_at: datetime

    class Config:
        from_attributes = True

# Shopify Integration Schemas
class ShopifyProductResponse(BaseModel):
    """Response schema for Shopify product data"""
    id: str
    title: str
    sku: str
    price: Decimal
    compare_at_price: Optional[Decimal]
    inventory_quantity: int
    status: str

class ShopifyUpdateRequest(BaseModel):
    """Request schema for Shopify price updates"""
    product_id: str = Field(..., description="Shopify product ID")
    new_price: Decimal = Field(..., gt=0, description="New price")
    reason: str = Field("pricing_engine_update", description="Update reason")

class ShopifyUpdateResponse(BaseModel):
    """Response schema for Shopify update results"""
    product_id: str
    success: bool
    old_price: Optional[Decimal]
    new_price: Decimal
    error_message: Optional[str]
    updated_at: Optional[datetime]

# Batch Operation Schemas
class BatchPricingRequest(BaseModel):
    """Request schema for batch pricing calculations"""
    pricing_inputs: List[PricingInputRequest] = Field(..., description="List of pricing inputs")

class BatchPricingResponse(BaseModel):
    """Response schema for batch pricing results"""
    results: List[PricingResultResponse] = Field(..., description="Pricing results")
    total_processed: int = Field(..., description="Total inputs processed")
    successful_updates: int = Field(..., description="Number of successful updates")
    failed_updates: int = Field(..., description="Number of failed updates")

class BatchScamDetectionRequest(BaseModel):
    """Request schema for batch scam detection"""
    price_data: List[Dict[str, Any]] = Field(..., description="List of price data to analyze")

class BatchScamDetectionResponse(BaseModel):
    """Response schema for batch scam detection results"""
    results: List[ScamDetectionResponse] = Field(..., description="Scam detection results")
    total_analyzed: int = Field(..., description="Total prices analyzed")
    scams_detected: int = Field(..., description="Number of scams detected")

# Analytics and Reporting Schemas
class PricingAnalyticsRequest(BaseModel):
    """Request schema for pricing analytics"""
    coin_id: Optional[int] = None
    coin_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_scam_data: bool = True

class PricingAnalyticsResponse(BaseModel):
    """Response schema for pricing analytics"""
    total_coins: int
    avg_price: Decimal
    price_range: Dict[str, Decimal]
    confidence_distribution: Dict[str, int]
    scam_detection_stats: Dict[str, int]
    source_reliability: Dict[str, float]
    price_trends: List[Dict[str, Any]]

class PricingSummaryResponse(BaseModel):
    """Response schema for pricing summary"""
    current_price: Decimal
    melt_value: Decimal
    markup_factor: Decimal
    confidence_score: float
    scam_detected: bool
    last_updated: datetime
    price_history: List[PriceHistoryResponse]
    scam_detection_history: List[ScamDetectionResultResponse]

# Error Schemas
class PricingErrorResponse(BaseModel):
    """Response schema for pricing errors"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Task Status Schemas
class TaskStatusResponse(BaseModel):
    """Response schema for task status"""
    task_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Configuration Schemas
class PricingServiceConfig(BaseModel):
    """Configuration schema for pricing services"""
    spot_price_sources: List[PricingSource]
    market_scraping_sources: List[PricingSource]
    scam_detection_enabled: bool
    confidence_threshold: float
    price_update_threshold: Decimal
    batch_size: int
    rate_limits: Dict[str, int]




