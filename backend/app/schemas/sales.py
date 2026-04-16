from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

class SalesChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    channel_type: str = Field(..., pattern="^(shopify|in_store|auction|direct)$")
    settings: Optional[Dict[str, Any]] = None

class SalesChannelCreate(SalesChannelBase):
    pass

class SalesChannelResponse(SalesChannelBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    coin_id: int
    channel_id: int
    sale_price: Decimal = Field(..., gt=0)
    quantity_sold: int = Field(1, ge=1)
    customer_info: Optional[Dict[str, Any]] = None
    transaction_id: Optional[str] = None

class SaleCreate(SaleBase):
    pass

class SaleResponse(SaleBase):
    id: int
    profit: Decimal
    sold_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class SalesForecastRequest(BaseModel):
    time_period: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    forecast_horizon: int = Field(..., ge=1, le=12)
    confidence_level: int = Field(..., ge=50, le=95)
    include_seasonality: bool = True
    include_trends: bool = True
    include_external_factors: bool = False

class ForecastFactor(BaseModel):
    name: str
    impact: str = Field(..., pattern="^(positive|negative|neutral)$")
    weight: float = Field(..., ge=0, le=1)
    description: str

class ForecastPeriodData(BaseModel):
    period: str
    predicted_revenue: Decimal
    confidence_range: Dict[str, Decimal]
    factors: List[ForecastFactor]
    accuracy_score: Optional[Decimal] = None

class SalesForecastResponse(BaseModel):
    forecast_type: str
    forecast_horizon: int
    confidence_level: int
    forecast_data: List[ForecastPeriodData]
    accuracy_score: Optional[Decimal]
    created_at: datetime
    valid_until: Optional[datetime]
    
    class Config:
        from_attributes = True

class ChannelSales(BaseModel):
    channel: str
    sales_count: int
    revenue: Decimal
    profit: Decimal
    percentage: float

class TopSellingCoin(BaseModel):
    id: int
    title: str
    sales_count: int
    total_sales: Decimal

class PeriodComparison(BaseModel):
    current_period: float
    previous_period: float
    change_percentage: float
    trend: str = Field(..., pattern="^(up|down|stable)$")

class SalesDashboardResponse(BaseModel):
    total_sales: Decimal
    sales_by_channel: List[ChannelSales]
    top_selling_coins: List[TopSellingCoin]
    profit_per_coin: Decimal
    sales_velocity: float
    period_comparison: PeriodComparison
    total_profit: Decimal
    sales_count: int
    unique_customers: int
    average_sale_value: Decimal
    profit_margin_percentage: Decimal

class SalesMetricsRequest(BaseModel):
    start_date: date
    end_date: date
    channel: Optional[str] = None
    period_type: str = Field("daily", pattern="^(daily|weekly|monthly)$")

class SalesMetricsResponse(BaseModel):
    period_type: str
    period_start: datetime
    period_end: datetime
    total_sales: Decimal
    total_profit: Decimal
    sales_count: int
    unique_customers: int
    average_sale_value: Decimal
    profit_margin_percentage: Decimal
    sales_velocity: Decimal
    channel_breakdown: List[ChannelSales]
    top_items: List[TopSellingCoin]
    calculated_at: datetime
    
    class Config:
        from_attributes = True


