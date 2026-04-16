from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Base schemas
class CoinBase(BaseModel):
    sku: Optional[str] = None
    name: str  # Changed from title to match database
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
    # Updated pricing strategy options
    price_strategy: str = 'paid_price_multiplier'  # Updated default
    price_multiplier: Decimal = Decimal('1.500')  # Updated default
    base_from_entry: bool = True
    entry_spot: Optional[Decimal] = None
    entry_melt: Optional[Decimal] = None
    override_price: bool = False
    override_value: Optional[Decimal] = None
    fixed_price: Optional[Decimal] = None  # New field for fixed pricing
    quantity: int = 1
    status: str = 'active'
    # New bulk operation fields
    bulk_operation_id: Optional[int] = None
    bulk_item_id: Optional[int] = None
    serial_number: Optional[str] = None
    bulk_sequence_number: Optional[int] = None
    # Collection relationship
    collection_id: Optional[int] = None

class CoinCreate(CoinBase):
    pass

class CoinUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None  # Changed from title
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
    fixed_price: Optional[Decimal] = None  # New field
    quantity: Optional[int] = None
    status: Optional[str] = None
    # New bulk operation fields
    bulk_operation_id: Optional[int] = None
    bulk_item_id: Optional[int] = None
    serial_number: Optional[str] = None
    bulk_sequence_number: Optional[int] = None
    # Collection relationship
    collection_id: Optional[int] = None

class Coin(CoinBase):
    id: int
    computed_price: Optional[Decimal] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CoinImageBase(BaseModel):
    url: str
    file_key: str  # New field for file uploader integration
    filename: str  # New field for original filename
    mime_type: str  # New field for MIME type
    size: int  # New field for file size
    alt: Optional[str] = None
    sort_order: int = 0
    is_primary: bool = False  # New field for primary image flag

class CoinImageCreate(CoinImageBase):
    coin_id: int

class CoinImage(CoinImageBase):
    id: int
    coin_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None  # New field
    
    class Config:
        from_attributes = True

class ListingBase(BaseModel):
    channel: str
    external_id: Optional[str] = None
    external_variant_id: Optional[str] = None
    url: Optional[str] = None
    status: str = 'unlisted'

class ListingCreate(ListingBase):
    coin_id: int

class Listing(ListingBase):
    id: int
    coin_id: int
    last_error: Optional[str] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    channel: str
    external_order_id: str
    qty: int = 1
    sold_price: Decimal
    fees: Decimal = Decimal('0.00')
    shipping_cost: Decimal = Decimal('0.00')

class OrderCreate(OrderBase):
    coin_id: int

class Order(OrderBase):
    id: int
    coin_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SpotPriceBase(BaseModel):
    metal: str
    price: Decimal
    source: Optional[str] = None

class SpotPriceCreate(SpotPriceBase):
    pass

class SpotPrice(SpotPriceBase):
    id: int
    fetched_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogBase(BaseModel):
    actor: Optional[str] = None
    action: str
    entity: str
    entity_id: Optional[str] = None
    payload: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard KPI schemas
class DashboardKPIs(BaseModel):
    inventory_melt_value: Decimal
    inventory_list_value: Decimal
    gross_profit: Decimal
    melt_vs_list_ratio: Decimal
    total_coins: int
    active_listings: int
    sold_this_month: int

# Collections Management
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = '#FFFFFF'
    icon: Optional[str] = None
    sort_order: int = 0
    shopify_collection_id: Optional[str] = None
    default_markup: Decimal = Decimal('1.300')

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    shopify_collection_id: Optional[str] = None
    default_markup: Optional[Decimal] = None

class Collection(CollectionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Bulk Operations
class BulkOperationBase(BaseModel):
    operation_type: str  # 'purchase', 'transfer', 'price_update', 'status_change'
    description: Optional[str] = None
    total_items: int
    operation_metadata: Optional[dict] = None

class BulkOperationCreate(BulkOperationBase):
    pass

class BulkOperationItemBase(BaseModel):
    coin_id: Optional[int] = None
    status: str = 'pending'
    error_message: Optional[str] = None
    item_metadata: Optional[dict] = None

class BulkOperationItemCreate(BulkOperationItemBase):
    bulk_operation_id: int

class BulkOperation(BulkOperationBase):
    id: int
    processed_items: int = 0
    failed_items: int = 0
    status: str = 'pending'
    created_by: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BulkOperationItem(BulkOperationItemBase):
    id: int
    bulk_operation_id: int
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BulkOperationResponse(BaseModel):
    operation: BulkOperation
    items: List[BulkOperationItem]
    stats: dict

class BulkOperationStatusResponse(BaseModel):
    id: int
    status: str
    progress: dict
    estimated_completion: Optional[datetime] = None

# Legacy bulk operations (for backward compatibility)
class BulkImportRequest(BaseModel):
    csv_data: str  # Base64 encoded CSV content

class BulkRepriceRequest(BaseModel):
    coin_ids: Optional[List[int]] = None  # If None, reprice all
    new_multiplier: Optional[Decimal] = None
    force_refresh_spot: bool = False

# Sales Management
class SalesChannelBase(BaseModel):
    name: str
    channel_type: str  # 'shopify', 'ebay', 'etsy', 'in_store', 'auction', 'direct'
    is_active: bool = True
    configuration: Optional[dict] = None

class SalesChannelCreate(SalesChannelBase):
    pass

class SalesChannel(SalesChannelBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    coin_id: int
    channel_id: int
    sale_price: Decimal
    quantity: int = 1
    fees: Decimal = Decimal('0.00')
    shipping_cost: Decimal = Decimal('0.00')
    customer_info: Optional[dict] = None
    sale_date: datetime

class SaleCreate(SaleBase):
    pass

class Sale(SaleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Sales Forecasting
class SalesForecastBase(BaseModel):
    forecast_type: str  # 'daily', 'weekly', 'monthly', 'quarterly', 'annually'
    period_start: datetime
    period_end: datetime
    predicted_revenue: Decimal
    confidence_level: str  # 'high', 'medium', 'low'
    algorithm_used: Optional[str] = None

class SalesForecastCreate(SalesForecastBase):
    pass

class SalesForecast(SalesForecastBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Financial Management
class TransactionBase(BaseModel):
    transaction_type: str  # 'income', 'expense', 'transfer'
    amount: Decimal
    description: str
    category: Optional[str] = None
    reference_id: Optional[str] = None
    transaction_date: datetime

class TransactionCreate(TransactionBase):
    created_by: str

class Transaction(TransactionBase):
    id: int
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    expense_type: str
    amount: Decimal
    description: str
    vendor: Optional[str] = None
    expense_date: datetime
    receipt_url: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    created_by: str

class Expense(ExpenseBase):
    id: int
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProfitLossStatementBase(BaseModel):
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal
    total_expenses: Decimal
    gross_profit: Decimal
    net_profit: Decimal

class ProfitLossStatementCreate(ProfitLossStatementBase):
    pass

class ProfitLossStatement(ProfitLossStatementBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Alert System
class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    alert_type: str  # 'low_inventory', 'price_change', 'system_issue', 'sales_milestone', 'profit_margin'
    conditions: dict
    product_specific: bool = False
    product_id: Optional[int] = None
    notification_channels: List[str] = ['in_app']
    notification_frequency: str = 'immediate'  # 'immediate', 'daily', 'weekly'
    enabled: bool = True

class AlertRuleCreate(AlertRuleBase):
    created_by: str

class AlertRule(AlertRuleBase):
    id: int
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    rule_id: int
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    message: str
    context_data: Optional[dict] = None
    affected_entity_id: Optional[int] = None
    affected_entity_type: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    status: str = 'active'  # 'active', 'acknowledged', 'resolved', 'dismissed'
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    triggered_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Shopify Integration
class ShopifyIntegrationBase(BaseModel):
    shop_domain: str
    access_token: str
    webhook_secret: Optional[str] = None
    sync_products: bool = True
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_pricing: bool = True
    sync_frequency: str = 'hourly'  # 'real_time', 'hourly', 'daily'
    active: bool = True

class ShopifyIntegrationCreate(ShopifyIntegrationBase):
    created_by: str

class ShopifyIntegration(ShopifyIntegrationBase):
    id: int
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int = 0
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ShopifyProductBase(BaseModel):
    coin_id: int
    shopify_product_id: str
    shopify_variant_id: Optional[str] = None
    shopify_handle: Optional[str] = None
    sync_status: str = 'pending'  # 'pending', 'synced', 'error'
    shopify_title: Optional[str] = None
    shopify_description: Optional[str] = None
    shopify_price: Optional[Decimal] = None
    shopify_inventory_quantity: Optional[int] = None

class ShopifyProductCreate(ShopifyProductBase):
    pass

class ShopifyProduct(ShopifyProductBase):
    id: int
    last_synced: Optional[datetime] = None
    sync_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ShopifyOrderBase(BaseModel):
    shopify_order_id: str
    order_number: Optional[str] = None
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    total_price: Decimal
    currency: str = 'USD'
    order_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    sync_status: str = 'pending'  # 'pending', 'synced', 'error'
    order_date: Optional[datetime] = None

class ShopifyOrderCreate(ShopifyOrderBase):
    pass

class ShopifyOrder(ShopifyOrderBase):
    id: int
    last_synced: Optional[datetime] = None
    sync_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ShopifyOrderItemBase(BaseModel):
    order_id: int
    coin_id: int
    shopify_line_item_id: Optional[str] = None
    product_title: Optional[str] = None
    variant_title: Optional[str] = None
    quantity: int = 1
    price: Decimal

class ShopifyOrderItemCreate(ShopifyOrderItemBase):
    pass

class ShopifyOrderItem(ShopifyOrderItemBase):
    id: int
    
    class Config:
        from_attributes = True

# AI Chat System
class AIChatMessageBase(BaseModel):
    message: str
    message_type: str = 'user'  # 'user', 'assistant', 'system'
    context: Optional[dict] = None
    preset: Optional[str] = None  # 'quick_response', 'in_depth_analysis', 'descriptions', 'year_mintage', 'pricing_only', 'visual_identification', 'grade_assessment'

class AIChatMessageCreate(AIChatMessageBase):
    pass

class AIChatMessage(AIChatMessageBase):
    id: int
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIChatSessionBase(BaseModel):
    session_name: Optional[str] = None
    context_type: str = 'general'  # 'general', 'coin_analysis', 'pricing', 'grading'
    is_active: bool = True

class AIChatSessionCreate(AIChatSessionBase):
    pass

class AIChatSession(AIChatSessionBase):
    id: int
    session_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

