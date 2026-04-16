from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.database import Base

class MarketPrice(Base):
    """Market price data for coins with scam detection and confidence scoring"""
    __tablename__ = "market_prices"
    __table_args__ = {'extend_existing': True}
    
    id = Column(BigInteger, primary_key=True, index=True)
    coin_id = Column(BigInteger, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    spot_price = Column(Numeric(10, 2), nullable=False)
    market_avg = Column(Numeric(10, 2))
    market_min = Column(Numeric(10, 2))
    market_max = Column(Numeric(10, 2))
    melt_value = Column(Numeric(10, 2), nullable=False)
    markup_factor = Column(Numeric(6, 3), nullable=False, default=Decimal('1.500'))
    final_price = Column(Numeric(10, 2), nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False, default=Decimal('0.50'))
    scam_detected = Column(Boolean, default=False, index=True)
    scam_reason = Column(Text)
    source = Column(String, nullable=False)
    sample_size = Column(Integer, default=1)
    price_change_percent = Column(Numeric(5, 2))
    last_updated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    # coin = relationship("Coin", back_populates="market_prices")  # Temporarily disabled
    scam_results = relationship("ScamDetectionResult", back_populates="market_price")

class PricingConfig(Base):
    """Configuration for different coin types and pricing rules"""
    __tablename__ = "pricing_config"
    __table_args__ = {'extend_existing': True}
    
    id = Column(BigInteger, primary_key=True, index=True)
    coin_type = Column(String(50), nullable=False, unique=True, index=True)
    min_markup = Column(Numeric(6, 3), nullable=False, default=Decimal('1.200'))
    max_markup = Column(Numeric(6, 3), nullable=False, default=Decimal('2.000'))
    default_markup = Column(Numeric(6, 3), nullable=False, default=Decimal('1.500'))
    scam_threshold = Column(Numeric(6, 3), nullable=False, default=Decimal('0.300'))
    confidence_threshold = Column(Numeric(3, 2), nullable=False, default=Decimal('0.70'))
    price_update_threshold = Column(Numeric(5, 2), nullable=False, default=Decimal('3.00'))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ScamDetectionResult(Base):
    """Results from AI scam detection analysis"""
    __tablename__ = "scam_detection_results"
    __table_args__ = {'extend_existing': True}
    
    id = Column(BigInteger, primary_key=True, index=True)
    coin_id = Column(BigInteger, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    market_price_id = Column(BigInteger, ForeignKey("market_prices.id", ondelete="CASCADE"), nullable=False)
    scam_probability = Column(Numeric(3, 2), nullable=False, index=True)
    scam_reasons = Column(ARRAY(Text), nullable=False, default=list)
    detection_method = Column(String(50), nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False)
    price_deviation = Column(Numeric(5, 2))
    statistical_z_score = Column(Numeric(8, 4))
    reviewed_by = Column(BigInteger)
    reviewed_at = Column(DateTime)
    is_false_positive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    # coin = relationship("Coin", back_populates="scam_results")  # Temporarily disabled
    market_price = relationship("MarketPrice", back_populates="scam_results")

class PriceHistory(Base):
    """Historical record of price changes"""
    __tablename__ = "price_history"
    __table_args__ = {'extend_existing': True}
    
    id = Column(BigInteger, primary_key=True, index=True)
    coin_id = Column(BigInteger, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2), nullable=False)
    price_change_percent = Column(Numeric(5, 2))
    change_reason = Column(String(100))
    spot_price_at_change = Column(Numeric(10, 2))
    market_avg_at_change = Column(Numeric(10, 2))
    updated_by = Column(String(50), default='system')
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    # coin = relationship("Coin", back_populates="price_history")  # Temporarily disabled

# Note: Coin model is defined in app/models.py to avoid conflicts

# Pricing data classes for type hints
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SpotPriceData:
    """Spot price data from external APIs"""
    price: Decimal
    currency: str
    source: str
    timestamp: datetime
    confidence: float = 1.0

@dataclass
class MarketData:
    """Market data from scraping"""
    avg_price: Decimal
    min_price: Decimal
    max_price: Decimal
    sample_size: int
    source: str
    timestamp: datetime
    confidence: float = 0.8

@dataclass
class ScamDetectionData:
    """Scam detection analysis results"""
    is_scam: bool
    probability: float
    reasons: List[str]
    method: str
    confidence: float
    z_score: Optional[float] = None
    price_deviation: Optional[float] = None

@dataclass
class PricingResult:
    """Final pricing calculation result"""
    final_price: Decimal
    melt_value: Decimal
    markup_factor: Decimal
    confidence_score: float
    scam_detected: bool
    sources_used: List[str]
    calculation_method: str
    timestamp: datetime


