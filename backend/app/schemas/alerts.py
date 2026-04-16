from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class AlertRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    alert_type: str = Field(..., pattern="^(low_inventory|price_change|system_issue|sales_milestone|profit_margin)$")
    conditions: Dict[str, Any]
    product_specific: bool = False
    product_id: Optional[int] = None
    notification_channels: Optional[List[str]] = None
    notification_frequency: str = Field("immediate", pattern="^(immediate|daily|weekly)$")

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleResponse(AlertRuleBase):
    id: int
    enabled: bool
    last_triggered: Optional[datetime]
    trigger_count: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    rule_id: int
    alert_type: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    title: str = Field(..., min_length=1, max_length=200)
    message: str
    context_data: Optional[Dict[str, Any]] = None
    affected_entity_id: Optional[int] = None
    affected_entity_type: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    triggered_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShopifyIntegrationBase(BaseModel):
    shop_domain: str = Field(..., min_length=1, max_length=200)
    access_token: str = Field(..., min_length=1, max_length=500)
    webhook_secret: Optional[str] = None
    sync_products: bool = True
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_pricing: bool = True
    sync_frequency: str = Field("hourly", pattern="^(real_time|hourly|daily)$")

class ShopifyIntegrationCreate(ShopifyIntegrationBase):
    pass

class ShopifyIntegrationResponse(ShopifyIntegrationBase):
    id: int
    active: bool
    last_sync: Optional[datetime]
    last_error: Optional[str]
    error_count: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ShopifySyncLogResponse(BaseModel):
    id: int
    integration_id: int
    sync_type: str
    sync_direction: str
    items_processed: int
    items_successful: int
    items_failed: int
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    status: str
    
    class Config:
        from_attributes = True

class ShopifyProductResponse(BaseModel):
    id: int
    coin_id: int
    shopify_product_id: str
    shopify_variant_id: Optional[str]
    shopify_handle: Optional[str]
    sync_status: str
    last_synced: Optional[datetime]
    sync_error: Optional[str]
    shopify_title: Optional[str]
    shopify_description: Optional[str]
    shopify_price: Optional[Decimal]
    shopify_inventory_quantity: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ShopifyOrderResponse(BaseModel):
    id: int
    shopify_order_id: str
    order_number: Optional[str]
    customer_email: Optional[str]
    customer_name: Optional[str]
    total_price: Decimal
    currency: str
    order_status: Optional[str]
    fulfillment_status: Optional[str]
    sync_status: str
    last_synced: Optional[datetime]
    sync_error: Optional[str]
    order_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ShopifyOrderItemResponse(BaseModel):
    id: int
    order_id: int
    coin_id: int
    shopify_line_item_id: Optional[str]
    product_title: Optional[str]
    variant_title: Optional[str]
    quantity: int
    price: Decimal
    
    class Config:
        from_attributes = True

class NotificationTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    template_type: str = Field(..., pattern="^(email|sms|in_app)$")
    alert_type: str = Field(..., pattern="^(low_inventory|price_change|system_issue|sales_milestone|profit_margin)$")
    subject_template: Optional[str] = None
    body_template: str
    available_variables: Optional[List[str]] = None

class NotificationTemplateCreate(NotificationTemplateBase):
    pass

class NotificationTemplateResponse(NotificationTemplateBase):
    id: int
    active: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NotificationLogResponse(BaseModel):
    id: int
    alert_id: int
    notification_type: str
    recipient: str
    subject: Optional[str]
    message: str
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertDashboardResponse(BaseModel):
    active_alerts: List[AlertResponse]
    alert_rules: List[AlertRuleResponse]
    recent_alerts: List[AlertResponse]
    alert_stats: Dict[str, Any]
    system_status: Dict[str, Any]

class ShopifyDashboardResponse(BaseModel):
    integration_status: ShopifyIntegrationResponse
    recent_syncs: List[ShopifySyncLogResponse]
    sync_stats: Dict[str, Any]
    product_sync_status: List[ShopifyProductResponse]
    recent_orders: List[ShopifyOrderResponse]

class AlertCondition(BaseModel):
    field: str
    operator: str = Field(..., pattern="^(eq|ne|gt|gte|lt|lte|contains|in|not_in)$")
    value: Any
    threshold: Optional[Decimal] = None

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    notification_channels: Optional[List[str]] = None
    notification_frequency: Optional[str] = None

class AlertUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|acknowledged|resolved|dismissed)$")
    resolution_notes: Optional[str] = None

class ShopifySyncRequest(BaseModel):
    sync_type: str = Field(..., pattern="^(products|inventory|orders|pricing|all)$")
    force_sync: bool = False

class ShopifyWebhookPayload(BaseModel):
    topic: str
    shop_domain: str
    payload: Dict[str, Any]
    webhook_id: str
    created_at: str

class AlertNotificationRequest(BaseModel):
    alert_id: int
    notification_channels: List[str]
    custom_message: Optional[str] = None

class SystemHealthCheck(BaseModel):
    database_status: str
    redis_status: str
    shopify_connection: str
    alert_system_status: str
    last_check: datetime
    overall_status: str


