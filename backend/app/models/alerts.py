from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from decimal import Decimal

class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Alert configuration
    alert_type = Column(String(50), nullable=False)  # low_inventory, price_change, system_issue, sales_milestone, profit_margin
    conditions = Column(JSON, nullable=False)  # Alert conditions and thresholds
    
    # Scope
    product_specific = Column(Boolean, default=False)
    product_id = Column(Integer, ForeignKey("coins.id"))  # Specific coin if product_specific is True
    
    # Notification settings
    notification_channels = Column(JSON)  # email, in_app, sms
    notification_frequency = Column(String(20), default="immediate")  # immediate, daily, weekly
    
    # Status
    enabled = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # product = relationship("Coin", foreign_keys=[product_id])  # Temporarily disabled
    alerts = relationship("Alert", back_populates="rule")

class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Context data
    context_data = Column(JSON)  # Additional data about the alert
    affected_entity_id = Column(Integer)  # ID of affected coin, sale, etc.
    affected_entity_type = Column(String(50))  # coin, sale, system, etc.
    
    # Status
    status = Column(String(20), default="active")  # active, acknowledged, resolved, dismissed
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")

class ShopifyIntegration(Base):
    __tablename__ = "shopify_integration"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Shopify configuration
    shop_domain = Column(String(200), nullable=False)
    access_token = Column(String(500), nullable=False)
    webhook_secret = Column(String(200))
    
    # Sync settings
    sync_products = Column(Boolean, default=True)
    sync_inventory = Column(Boolean, default=True)
    sync_orders = Column(Boolean, default=True)
    sync_pricing = Column(Boolean, default=True)
    
    # Sync frequency
    sync_frequency = Column(String(20), default="hourly")  # real_time, hourly, daily
    
    # Status
    active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sync_logs = relationship("ShopifySyncLog", back_populates="integration")

class ShopifySyncLog(Base):
    __tablename__ = "shopify_sync_logs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("shopify_integration.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # products, inventory, orders, pricing
    sync_direction = Column(String(20), nullable=False)  # to_shopify, from_shopify, bidirectional
    
    # Results
    items_processed = Column(Integer, default=0)
    items_successful = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Error details
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Status
    status = Column(String(20), nullable=False)  # running, completed, failed, cancelled
    
    # Relationships
    integration = relationship("ShopifyIntegration", back_populates="sync_logs")

class ShopifyProduct(Base):
    __tablename__ = "shopify_products"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    
    # Shopify product details
    shopify_product_id = Column(String(100), nullable=False, unique=True)
    shopify_variant_id = Column(String(100))
    shopify_handle = Column(String(200))
    
    # Sync status
    sync_status = Column(String(20), default="pending")  # pending, synced, error
    last_synced = Column(DateTime)
    sync_error = Column(Text)
    
    # Product data
    shopify_title = Column(String(200))
    shopify_description = Column(Text)
    shopify_price = Column(DECIMAL(10, 2))
    shopify_inventory_quantity = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # coin = relationship("Coin")  # Temporarily disabled

class ShopifyOrder(Base):
    __tablename__ = "shopify_orders"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Shopify order details
    shopify_order_id = Column(String(100), nullable=False, unique=True)
    order_number = Column(String(100))
    
    # Order information
    customer_email = Column(String(200))
    customer_name = Column(String(200))
    total_price = Column(DECIMAL(10, 2))
    currency = Column(String(3), default="USD")
    
    # Order status
    order_status = Column(String(50))  # pending, paid, fulfilled, cancelled
    fulfillment_status = Column(String(50))  # unfulfilled, partial, fulfilled
    
    # Sync status
    sync_status = Column(String(20), default="pending")  # pending, synced, error
    last_synced = Column(DateTime)
    sync_error = Column(Text)
    
    # Timestamps
    order_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = relationship("ShopifyOrderItem", back_populates="order")

class ShopifyOrderItem(Base):
    __tablename__ = "shopify_order_items"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("shopify_orders.id"), nullable=False)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    
    # Item details
    shopify_line_item_id = Column(String(100))
    product_title = Column(String(200))
    variant_title = Column(String(200))
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    order = relationship("ShopifyOrder", back_populates="order_items")
    # coin = relationship("Coin")  # Temporarily disabled

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False)  # email, sms, in_app
    alert_type = Column(String(50), nullable=False)  # Corresponds to alert types
    
    # Template content
    subject_template = Column(String(200))  # For email
    body_template = Column(Text, nullable=False)
    
    # Variables available in template
    available_variables = Column(JSON)
    
    # Status
    active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    
    # Notification details
    notification_type = Column(String(50), nullable=False)  # email, sms, in_app
    recipient = Column(String(200), nullable=False)  # email address, phone number, user_id
    
    # Content
    subject = Column(String(200))
    message = Column(Text, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False)  # pending, sent, failed, bounced
    sent_at = Column(DateTime)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    alert = relationship("Alert")


