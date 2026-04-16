from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.schemas.alerts import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertCreate, AlertUpdate,
    AlertResponse, NotificationTemplateCreate, NotificationTemplateResponse,
    AlertDashboardResponse, ShopifyIntegrationCreate, ShopifyIntegrationResponse,
    ShopifySyncRequest, ShopifyWebhookPayload, ShopifyDashboardResponse,
    SystemHealthCheck, AlertNotificationRequest
)
from app.services.alert_service import AlertService
from app.services.shopify_service import ShopifyService
from app.auth import get_current_admin_user

router = APIRouter()

@router.post("/alert-rules", response_model=AlertRuleResponse)
def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Create a new alert rule."""
    service = AlertService(db)
    rule = service.create_alert_rule(rule_data, admin_user["username"])
    return rule

@router.get("/alert-rules", response_model=List[AlertRuleResponse])
def get_alert_rules(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get all alert rules."""
    service = AlertService(db)
    rules = service.get_alert_rules(enabled_only)
    return rules

@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get a specific alert rule."""
    service = AlertService(db)
    rule = service.get_alert_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule

@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(
    rule_id: int,
    rule_data: AlertRuleUpdate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Update an alert rule."""
    service = AlertService(db)
    rule = service.update_alert_rule(rule_id, rule_data)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule

@router.delete("/alert-rules/{rule_id}")
def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Delete an alert rule."""
    service = AlertService(db)
    success = service.delete_alert_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return {"message": "Alert rule deleted successfully"}

@router.post("/alerts", response_model=AlertResponse)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Create a new alert."""
    service = AlertService(db)
    alert = service.create_alert(alert_data)
    return alert

@router.get("/alerts/active", response_model=List[AlertResponse])
def get_active_alerts(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get all active alerts."""
    service = AlertService(db)
    alerts = service.get_active_alerts()
    return alerts

@router.get("/alerts/recent", response_model=List[AlertResponse])
def get_recent_alerts(
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get recent alerts."""
    service = AlertService(db)
    alerts = service.get_recent_alerts(hours, limit)
    return alerts

@router.get("/alerts/by-type/{alert_type}", response_model=List[AlertResponse])
def get_alerts_by_type(
    alert_type: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get alerts by type."""
    service = AlertService(db)
    alerts = service.get_alerts_by_type(alert_type, limit)
    return alerts

@router.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Update an alert status."""
    service = AlertService(db)
    alert = service.update_alert(alert_id, alert_data, admin_user["username"])
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/alerts/check")
def run_alert_checks(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Run all alert checks."""
    service = AlertService(db)
    
    def run_checks():
        alerts = service.run_all_alert_checks()
        return alerts
    
    background_tasks.add_task(run_checks)
    return {"message": "Alert checks initiated"}

@router.get("/alerts/statistics")
def get_alert_statistics(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get alert statistics."""
    service = AlertService(db)
    stats = service.get_alert_statistics()
    return stats

@router.get("/system/health", response_model=SystemHealthCheck)
def get_system_health(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get system health status."""
    service = AlertService(db)
    health = service.get_system_health()
    return health

@router.post("/notification-templates", response_model=NotificationTemplateResponse)
def create_notification_template(
    template_data: NotificationTemplateCreate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Create a notification template."""
    service = AlertService(db)
    template = service.create_notification_template(template_data, admin_user["username"])
    return template

@router.get("/notification-templates", response_model=List[NotificationTemplateResponse])
def get_notification_templates(
    alert_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get notification templates."""
    service = AlertService(db)
    templates = service.get_notification_templates(alert_type)
    return templates

@router.post("/notifications/send")
def send_notification(
    notification_data: AlertNotificationRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Send notification for an alert."""
    service = AlertService(db)
    
    # This would integrate with actual notification services (email, SMS, etc.)
    # For now, just log the notification
    for channel in notification_data.notification_channels:
        service.log_notification(
            alert_id=notification_data.alert_id,
            notification_type=channel,
            recipient=admin_user["email"],  # Would be configurable
            subject=f"Alert Notification",
            message=notification_data.custom_message or "Alert notification",
            status="sent"
        )
    
    return {"message": "Notifications sent successfully"}

# Shopify Integration Endpoints

@router.post("/shopify/integrations", response_model=ShopifyIntegrationResponse)
def create_shopify_integration(
    integration_data: ShopifyIntegrationCreate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Create a new Shopify integration."""
    service = ShopifyService(db)
    integration = service.create_integration(integration_data, admin_user["username"])
    return integration

@router.get("/shopify/integrations", response_model=List[ShopifyIntegrationResponse])
def get_shopify_integrations(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get all Shopify integrations."""
    service = ShopifyService(db)
    integrations = service.db.query(service.db.query(ShopifyIntegration).all())
    return integrations

@router.get("/shopify/integrations/{integration_id}", response_model=ShopifyIntegrationResponse)
def get_shopify_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get a specific Shopify integration."""
    service = ShopifyService(db)
    integration = service.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration

@router.post("/shopify/integrations/{integration_id}/test")
def test_shopify_connection(
    integration_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Test Shopify API connection."""
    service = ShopifyService(db)
    result = service.test_connection(integration_id)
    return result

@router.post("/shopify/sync/products")
def sync_products_to_shopify(
    sync_request: ShopifySyncRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Sync products to Shopify."""
    service = ShopifyService(db)
    integration = service.get_active_integration()
    if not integration:
        raise HTTPException(status_code=404, detail="No active Shopify integration found")
    
    result = service.sync_products_to_shopify(integration.id, sync_request.force_sync)
    return result

@router.post("/shopify/sync/orders")
def sync_orders_from_shopify(
    hours_back: int = 24,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Sync orders from Shopify."""
    service = ShopifyService(db)
    integration = service.get_active_integration()
    if not integration:
        raise HTTPException(status_code=404, detail="No active Shopify integration found")
    
    result = service.sync_orders_from_shopify(integration.id, hours_back)
    return result

@router.post("/shopify/sync/inventory")
def sync_inventory_from_shopify(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Sync inventory from Shopify."""
    service = ShopifyService(db)
    integration = service.get_active_integration()
    if not integration:
        raise HTTPException(status_code=404, detail="No active Shopify integration found")
    
    result = service.sync_inventory_from_shopify(integration.id)
    return result

@router.post("/shopify/webhooks")
def process_shopify_webhook(
    webhook_data: ShopifyWebhookPayload,
    db: Session = Depends(get_db)
):
    """Process incoming Shopify webhook."""
    service = ShopifyService(db)
    result = service.process_webhook(webhook_data)
    return result

@router.get("/shopify/sync-logs/{integration_id}")
def get_shopify_sync_logs(
    integration_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get sync logs for a Shopify integration."""
    service = ShopifyService(db)
    logs = service.get_sync_logs(integration_id, limit)
    return logs

@router.get("/shopify/products/{integration_id}")
def get_shopify_products(
    integration_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get Shopify products for an integration."""
    service = ShopifyService(db)
    products = service.get_shopify_products(integration_id)
    return products

@router.get("/shopify/orders/{integration_id}")
def get_shopify_orders(
    integration_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get Shopify orders for an integration."""
    service = ShopifyService(db)
    orders = service.get_shopify_orders(integration_id, limit)
    return orders

@router.get("/shopify/statistics/{integration_id}")
def get_shopify_statistics(
    integration_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get sync statistics for a Shopify integration."""
    service = ShopifyService(db)
    stats = service.get_sync_statistics(integration_id)
    return stats

@router.post("/shopify/create-product-inventory/{coin_id}")
async def create_product_and_inventory(
    coin_id: int,
    integration_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Create a product in Shopify and add it to our inventory."""
    service = ShopifyService(db)
    result = service.create_product_and_inventory(integration_id, coin_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.get("/dashboard", response_model=AlertDashboardResponse)
def get_alert_dashboard(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get alert dashboard data."""
    alert_service = AlertService(db)
    
    active_alerts = alert_service.get_active_alerts()
    alert_rules = alert_service.get_alert_rules()
    recent_alerts = alert_service.get_recent_alerts(hours=24, limit=20)
    alert_stats = alert_service.get_alert_statistics()
    system_status = alert_service.get_system_health()
    
    return AlertDashboardResponse(
        active_alerts=active_alerts,
        alert_rules=alert_rules,
        recent_alerts=recent_alerts,
        alert_stats=alert_stats,
        system_status=system_status.dict()
    )

@router.get("/shopify/dashboard", response_model=ShopifyDashboardResponse)
def get_shopify_dashboard(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get Shopify dashboard data."""
    shopify_service = ShopifyService(db)
    
    integration = shopify_service.get_active_integration()
    if not integration:
        raise HTTPException(status_code=404, detail="No active Shopify integration found")
    
    recent_syncs = shopify_service.get_sync_logs(integration.id, limit=10)
    sync_stats = shopify_service.get_sync_statistics(integration.id)
    product_sync_status = shopify_service.get_shopify_products(integration.id)
    recent_orders = shopify_service.get_shopify_orders(integration.id, limit=20)
    
    return ShopifyDashboardResponse(
        integration_status=integration,
        recent_syncs=recent_syncs,
        sync_stats=sync_stats,
        product_sync_status=product_sync_status,
        recent_orders=recent_orders
    )


