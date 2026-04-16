from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from decimal import Decimal

class Location(Base):
    __tablename__ = "locations"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    address = Column(Text)
    location_type = Column(String(50), default="store")  # store, warehouse, vault
    active = Column(Boolean, default=True)
    settings = Column(JSON)  # Location-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="location")
    movements_from = relationship("InventoryMovement", foreign_keys="InventoryMovement.from_location_id")
    movements_to = relationship("InventoryMovement", foreign_keys="InventoryMovement.to_location_id")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Inventory details
    quantity = Column(Integer, nullable=False, default=1)
    reserved_quantity = Column(Integer, default=0)  # Reserved for pending sales
    available_quantity = Column(Integer, nullable=False)  # Calculated field
    
    # Tracking
    last_counted = Column(DateTime)
    last_moved = Column(DateTime)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # coin = relationship("Coin", back_populates="inventory_items")  # Temporarily disabled
    location = relationship("Location", back_populates="inventory_items")

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Movement details
    quantity = Column(Integer, nullable=False)
    movement_type = Column(String(50), nullable=False)  # transfer, sale, adjustment, count
    reason = Column(String(200))
    reference_id = Column(String(100))  # Reference to sale, order, etc.
    
    # User tracking
    moved_by = Column(String(100))  # User who performed the movement
    
    # Timestamps
    moved_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # coin = relationship("Coin")  # Temporarily disabled
    from_location = relationship("Location", foreign_keys=[from_location_id], overlaps="movements_from")
    to_location = relationship("Location", foreign_keys=[to_location_id], overlaps="movements_to")

class DeadStockAnalysis(Base):
    __tablename__ = "dead_stock_analysis"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    
    # Analysis criteria
    days_since_last_sale = Column(Integer)
    days_since_added = Column(Integer)
    profit_margin = Column(Numeric(5, 2))
    category = Column(String(50))  # slow_moving, dead_stock, fast_moving
    
    # Analysis metadata
    analysis_date = Column(DateTime, default=datetime.utcnow)
    criteria_used = Column(JSON)  # Criteria used for classification
    
    # Relationships
    # coin = relationship("Coin")  # Temporarily disabled

class InventoryMetrics(Base):
    __tablename__ = "inventory_metrics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Time period
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Inventory metrics
    total_coins = Column(Integer, default=0)
    total_value = Column(Numeric(12, 2), default=Decimal('0'))
    dead_stock_count = Column(Integer, default=0)
    dead_stock_value = Column(Numeric(12, 2), default=Decimal('0'))
    turnover_rate = Column(Numeric(5, 2), default=Decimal('0'))
    
    # Location breakdown
    location_breakdown = Column(JSON)  # Inventory by location
    
    # Category breakdown
    category_breakdown = Column(JSON)  # Inventory by category
    
    # Profit margin analysis
    profit_margin_analysis = Column(JSON)  # Profit margins by category
    
    # Calculated metrics
    average_value_per_coin = Column(Numeric(10, 2), default=Decimal('0'))
    dead_stock_percentage = Column(Numeric(5, 2), default=Decimal('0'))
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for efficient queries
    __table_args__ = (
        {'extend_existing': True}
    )

class TurnoverAnalysis(Base):
    __tablename__ = "turnover_analysis"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    
    # Analysis period
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)
    
    # Turnover metrics
    days_since_last_sale = Column(Integer)
    days_since_added = Column(Integer)
    sales_count = Column(Integer, default=0)
    total_revenue = Column(Numeric(12, 2), default=Decimal('0'))
    turnover_category = Column(String(50))  # fast_moving, slow_moving, dead_stock
    
    # Performance metrics
    sales_velocity = Column(Numeric(8, 2), default=Decimal('0'))  # Sales per day
    profit_margin = Column(Numeric(5, 2), default=Decimal('0'))
    
    # Analysis metadata
    analysis_date = Column(DateTime, default=datetime.utcnow)
    criteria_used = Column(JSON)  # Criteria used for classification
    
    # Relationships
    # coin = relationship("Coin")  # Temporarily disabled


