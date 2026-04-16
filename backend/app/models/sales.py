from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime
from decimal import Decimal

class SalesChannel(Base):
    __tablename__ = "sales_channels"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    channel_type = Column(String(50), nullable=False)  # shopify, in_store, auction, direct
    active = Column(Boolean, default=True)
    settings = Column(JSON)  # Channel-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales = relationship("Sale", back_populates="channel")

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("sales_channels.id"), nullable=False)
    
    # Sale details
    sale_price = Column(Numeric(10, 2), nullable=False)
    profit = Column(Numeric(10, 2), nullable=False)
    quantity_sold = Column(Integer, default=1)
    
    # Customer information
    customer_info = Column(JSON)  # Name, email, phone, etc.
    transaction_id = Column(String(100))  # External transaction ID
    
    # Timestamps
    sold_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # coin = relationship("Coin", back_populates="sales")  # Temporarily disabled
    channel = relationship("SalesChannel", back_populates="sales")

class SalesForecast(Base):
    __tablename__ = "sales_forecasts"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    forecast_horizon = Column(Integer, nullable=False)  # Number of periods ahead
    confidence_level = Column(Integer, nullable=False)  # 50-95%
    
    # Forecast data
    forecast_data = Column(JSON)  # Array of forecast periods
    factors_used = Column(JSON)  # Factors considered in forecast
    accuracy_score = Column(Numeric(5, 2))  # Historical accuracy
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Settings used
    include_seasonality = Column(Boolean, default=True)
    include_trends = Column(Boolean, default=True)
    include_external_factors = Column(Boolean, default=False)
    
    # Relationships
    forecast_periods = relationship("ForecastPeriod", back_populates="forecast")

class ForecastPeriod(Base):
    __tablename__ = "forecast_periods"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, ForeignKey("sales_forecasts.id"), nullable=False)
    
    # Period details
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_name = Column(String(50), nullable=False)  # e.g., "2025-01-27", "Week 1", "January 2025"
    
    # Forecast values
    predicted_revenue = Column(Numeric(12, 2), nullable=False)
    confidence_min = Column(Numeric(12, 2), nullable=False)
    confidence_max = Column(Numeric(12, 2), nullable=False)
    
    # Factors that influenced this prediction
    factors = Column(JSON)  # Array of factor objects with impact and weight
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    forecast = relationship("SalesForecast", back_populates="forecast_periods")

class SalesMetrics(Base):
    __tablename__ = "sales_metrics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Time period
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Metrics
    total_sales = Column(Numeric(12, 2), default=Decimal('0'))
    total_profit = Column(Numeric(12, 2), default=Decimal('0'))
    sales_count = Column(Integer, default=0)
    unique_customers = Column(Integer, default=0)
    
    # Channel breakdown
    channel_breakdown = Column(JSON)  # Sales by channel
    
    # Top performing items
    top_items = Column(JSON)  # Top selling coins
    
    # Calculated metrics
    average_sale_value = Column(Numeric(10, 2), default=Decimal('0'))
    profit_margin_percentage = Column(Numeric(5, 2), default=Decimal('0'))
    sales_velocity = Column(Numeric(8, 2), default=Decimal('0'))  # Sales per day
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for efficient queries
    __table_args__ = (
        {'extend_existing': True}
    )


