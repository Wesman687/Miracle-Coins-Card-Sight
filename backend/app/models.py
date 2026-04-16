from sqlalchemy import Column, BigInteger, String, Integer, Boolean, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Coin(Base):
    __tablename__ = "coins"
    
    id = Column(BigInteger, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)  # Database has 'title' to match frontend
    year = Column(Integer)
    denomination = Column(String)
    mint_mark = Column(String)
    grade = Column(String)
    category = Column(String)
    description = Column(Text)
    condition_notes = Column(Text)
    is_silver = Column(Boolean, default=False)
    silver_percent = Column(Numeric(5, 4))
    silver_content_oz = Column(Numeric(7, 4))
    paid_price = Column(Numeric(10, 2))
    # Note: Some fields removed to match actual database schema
    price_strategy = Column(String, default='fixed_price')
    computed_price = Column(Numeric(10, 2))
    quantity = Column(Integer, default=1)
    status = Column(String, default='active')
    created_by = Column(String)  # UUID as string
    # Shopify metadata fields
    tags = Column(Text)  # JSON array of tags
    shopify_metadata = Column(Text)  # JSON object for Shopify metadata
    # Collection relationship
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Bulk operation fields
    bulk_operation_id = Column(Integer, ForeignKey("bulk_operations.id"))
    bulk_item_id = Column(Integer, ForeignKey("bulk_operation_items.id"))
    serial_number = Column(String(50))
    bulk_sequence_number = Column(Integer)
    
    # Relationships - temporarily disabled to match actual database schema
    # images = relationship("CoinImage", back_populates="coin", cascade="all, delete-orphan")
    # listings = relationship("Listing", back_populates="coin", cascade="all, delete-orphan")
    # orders = relationship("Order", back_populates="coin")
    # sales = relationship("Sale", back_populates="coin")

class CoinImage(Base):
    __tablename__ = "coin_images"
    
    id = Column(BigInteger, primary_key=True, index=True)
    coin_id = Column(BigInteger, ForeignKey("coins.id", ondelete="CASCADE"))
    url = Column(String, nullable=False)
    alt = Column(String)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - temporarily disabled
    # coin = relationship("Coin", back_populates="images")

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(BigInteger, primary_key=True, index=True)
    coin_id = Column(BigInteger, ForeignKey("coins.id", ondelete="CASCADE"))
    channel = Column(String, nullable=False)
    external_id = Column(String)
    external_variant_id = Column(String)
    url = Column(String)
    status = Column(String, default='unlisted')
    last_error = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships - temporarily disabled
    # coin = relationship("Coin", back_populates="listings")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(BigInteger, primary_key=True, index=True)
    coin_id = Column(BigInteger, ForeignKey("coins.id"))
    channel = Column(String, nullable=False)
    external_order_id = Column(String, nullable=False)
    qty = Column(Integer, default=1)
    sold_price = Column(Numeric(10, 2), nullable=False)
    fees = Column(Numeric(10, 2), default=0.00)
    shipping_cost = Column(Numeric(10, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - temporarily disabled
    # coin = relationship("Coin", back_populates="orders")

class SpotPrice(Base):
    __tablename__ = "spot_prices"
    
    id = Column(BigInteger, primary_key=True, index=True)
    metal = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    source = Column(String)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(BigInteger, primary_key=True, index=True)
    actor = Column(String)  # UUID as string
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(String)
    payload = Column(Text)  # JSONB as text for now
    created_at = Column(DateTime(timezone=True), server_default=func.now())
