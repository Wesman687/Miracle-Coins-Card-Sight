from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging

from app.models.alerts import AlertRule, Alert, NotificationTemplate, NotificationLog
from app.models import Coin
from app.models.sales import Sale
from app.models.inventory import InventoryItem
from app.schemas.alerts import (
    AlertRuleCreate, AlertRuleUpdate, AlertCreate, AlertUpdate,
    NotificationTemplateCreate, AlertCondition, SystemHealthCheck
)

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert_rule(self, rule_data: AlertRuleCreate, created_by: str) -> AlertRule:
        """Create a new alert rule."""
        rule = AlertRule(
            name=rule_data.name,
            description=rule_data.description,
            alert_type=rule_data.alert_type,
            conditions=rule_data.conditions,
            product_specific=rule_data.product_specific,
            product_id=rule_data.product_id,
            notification_channels=rule_data.notification_channels or ["in_app"],
            notification_frequency=rule_data.notification_frequency,
            enabled=True,
            created_by=created_by
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_alert_rule(self, rule_id: int, rule_data: AlertRuleUpdate) -> Optional[AlertRule]:
        """Update an existing alert rule."""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return None

        if rule_data.name is not None:
            rule.name = rule_data.name
        if rule_data.description is not None:
            rule.description = rule_data.description
        if rule_data.conditions is not None:
            rule.conditions = rule_data.conditions
        if rule_data.enabled is not None:
            rule.enabled = rule_data.enabled
        if rule_data.notification_channels is not None:
            rule.notification_channels = rule_data.notification_channels
        if rule_data.notification_frequency is not None:
            rule.notification_frequency = rule_data.notification_frequency

        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_alert_rule(self, rule_id: int) -> bool:
        """Delete an alert rule."""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return False

        self.db.delete(rule)
        self.db.commit()
        return True

    def get_alert_rules(self, enabled_only: bool = False) -> List[AlertRule]:
        """Get all alert rules."""
        query = self.db.query(AlertRule)
        if enabled_only:
            query = query.filter(AlertRule.enabled == True)
        return query.order_by(desc(AlertRule.created_at)).all()

    def get_alert_rule(self, rule_id: int) -> Optional[AlertRule]:
        """Get a specific alert rule."""
        return self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()

    def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert."""
        alert = Alert(
            rule_id=alert_data.rule_id,
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            title=alert_data.title,
            message=alert_data.message,
            context_data=alert_data.context_data,
            affected_entity_id=alert_data.affected_entity_id,
            affected_entity_type=alert_data.affected_entity_type,
            status="active"
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def update_alert(self, alert_id: int, alert_data: AlertUpdate, updated_by: str) -> Optional[Alert]:
        """Update an alert status."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None

        alert.status = alert_data.status
        alert.updated_at = datetime.utcnow()

        if alert_data.status == "acknowledged":
            alert.acknowledged_by = updated_by
            alert.acknowledged_at = datetime.utcnow()
        elif alert_data.status == "resolved":
            alert.resolved_by = updated_by
            alert.resolved_at = datetime.utcnow()
            alert.resolution_notes = alert_data.resolution_notes

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return self.db.query(Alert).filter(Alert.status == "active").order_by(desc(Alert.created_at)).all()

    def get_alerts_by_type(self, alert_type: str, limit: int = 50) -> List[Alert]:
        """Get alerts by type."""
        return self.db.query(Alert).filter(Alert.alert_type == alert_type).order_by(desc(Alert.created_at)).limit(limit).all()

    def get_recent_alerts(self, hours: int = 24, limit: int = 100) -> List[Alert]:
        """Get recent alerts within specified hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Alert).filter(Alert.created_at >= since).order_by(desc(Alert.created_at)).limit(limit).all()

    def check_low_inventory_alerts(self) -> List[Alert]:
        """Check for low inventory alerts."""
        alerts = []
        rules = self.db.query(AlertRule).filter(
            and_(
                AlertRule.enabled == True,
                AlertRule.alert_type == "low_inventory"
            )
        ).all()

        for rule in rules:
            conditions = rule.conditions
            threshold = conditions.get("threshold", 10)
            
            # Get inventory items below threshold
            query = self.db.query(InventoryItem).join(Coin)
            if rule.product_specific and rule.product_id:
                query = query.filter(InventoryItem.coin_id == rule.product_id)
            
            low_items = query.filter(InventoryItem.quantity <= threshold).all()
            
            for item in low_items:
                alert_data = AlertCreate(
                    rule_id=rule.id,
                    alert_type="low_inventory",
                    severity="medium",
                    title=f"Low Inventory Alert: {item.coin.name}",
                    message=f"Inventory for {item.coin.name} is below threshold ({item.quantity} <= {threshold})",
                    context_data={
                        "coin_id": item.coin_id,
                        "current_quantity": item.quantity,
                        "threshold": threshold,
                        "coin_name": item.coin.name
                    },
                    affected_entity_id=item.coin_id,
                    affected_entity_type="coin"
                )
                alert = self.create_alert(alert_data)
                alerts.append(alert)
                
                # Update rule trigger count
                rule.last_triggered = datetime.utcnow()
                rule.trigger_count += 1

        self.db.commit()
        return alerts

    def check_price_change_alerts(self) -> List[Alert]:
        """Check for significant price changes."""
        alerts = []
        rules = self.db.query(AlertRule).filter(
            and_(
                AlertRule.enabled == True,
                AlertRule.alert_type == "price_change"
            )
        ).all()

        for rule in rules:
            conditions = rule.conditions
            threshold_percent = conditions.get("threshold_percent", 5)
            time_window_hours = conditions.get("time_window_hours", 24)
            
            # Get coins with significant price changes
            since = datetime.utcnow() - timedelta(hours=time_window_hours)
            query = self.db.query(Coin)
            if rule.product_specific and rule.product_id:
                query = query.filter(Coin.id == rule.product_id)
            
            coins = query.all()
            
            for coin in coins:
                if coin.computed_price and coin.paid_price:
                    price_change_percent = ((coin.computed_price - coin.paid_price) / coin.paid_price) * 100
                    
                    if abs(price_change_percent) >= threshold_percent:
                        severity = "high" if abs(price_change_percent) >= threshold_percent * 2 else "medium"
                        
                        alert_data = AlertCreate(
                            rule_id=rule.id,
                            alert_type="price_change",
                            severity=severity,
                            title=f"Price Change Alert: {coin.name}",
                            message=f"Price change of {price_change_percent:.1f}% detected for {coin.name}",
                            context_data={
                                "coin_id": coin.id,
                                "old_price": float(coin.paid_price),
                                "new_price": float(coin.computed_price),
                                "change_percent": price_change_percent,
                                "coin_name": coin.name
                            },
                            affected_entity_id=coin.id,
                            affected_entity_type="coin"
                        )
                        alert = self.create_alert(alert_data)
                        alerts.append(alert)
                        
                        # Update rule trigger count
                        rule.last_triggered = datetime.utcnow()
                        rule.trigger_count += 1

        self.db.commit()
        return alerts

    def check_system_issue_alerts(self) -> List[Alert]:
        """Check for system issues."""
        alerts = []
        rules = self.db.query(AlertRule).filter(
            and_(
                AlertRule.enabled == True,
                AlertRule.alert_type == "system_issue"
            )
        ).all()

        # Check for system health issues
        health_check = self.get_system_health()
        
        for rule in rules:
            conditions = rule.conditions
            check_type = conditions.get("check_type", "overall")
            
            if check_type == "overall" and health_check.overall_status != "healthy":
                alert_data = AlertCreate(
                    rule_id=rule.id,
                    alert_type="system_issue",
                    severity="high",
                    title="System Health Issue Detected",
                    message=f"System health check failed: {health_check.overall_status}",
                    context_data={
                        "health_check": health_check.dict(),
                        "check_type": check_type
                    }
                )
                alert = self.create_alert(alert_data)
                alerts.append(alert)
                
                # Update rule trigger count
                rule.last_triggered = datetime.utcnow()
                rule.trigger_count += 1

        self.db.commit()
        return alerts

    def check_sales_milestone_alerts(self) -> List[Alert]:
        """Check for sales milestones."""
        alerts = []
        rules = self.db.query(AlertRule).filter(
            and_(
                AlertRule.enabled == True,
                AlertRule.alert_type == "sales_milestone"
            )
        ).all()

        for rule in rules:
            conditions = rule.conditions
            milestone_type = conditions.get("milestone_type", "daily_sales")
            threshold = conditions.get("threshold", 1000)
            time_period = conditions.get("time_period", "daily")
            
            # Calculate sales for the specified period
            if time_period == "daily":
                since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == "weekly":
                since = datetime.utcnow() - timedelta(days=7)
            elif time_period == "monthly":
                since = datetime.utcnow() - timedelta(days=30)
            else:
                since = datetime.utcnow() - timedelta(days=1)
            
            sales_query = self.db.query(func.sum(Sale.total_amount)).filter(Sale.created_at >= since)
            total_sales = sales_query.scalar() or 0
            
            if total_sales >= threshold:
                alert_data = AlertCreate(
                    rule_id=rule.id,
                    alert_type="sales_milestone",
                    severity="low",
                    title=f"Sales Milestone Reached: {time_period.title()}",
                    message=f"Sales target of ${threshold} reached for {time_period} period. Total: ${total_sales}",
                    context_data={
                        "milestone_type": milestone_type,
                        "threshold": threshold,
                        "actual_value": float(total_sales),
                        "time_period": time_period
                    }
                )
                alert = self.create_alert(alert_data)
                alerts.append(alert)
                
                # Update rule trigger count
                rule.last_triggered = datetime.utcnow()
                rule.trigger_count += 1

        self.db.commit()
        return alerts

    def check_profit_margin_alerts(self) -> List[Alert]:
        """Check for profit margin deviations."""
        alerts = []
        rules = self.db.query(AlertRule).filter(
            and_(
                AlertRule.enabled == True,
                AlertRule.alert_type == "profit_margin"
            )
        ).all()

        for rule in rules:
            conditions = rule.conditions
            expected_margin = conditions.get("expected_margin", 0.3)  # 30%
            deviation_threshold = conditions.get("deviation_threshold", 0.1)  # 10%
            
            # Get coins with profit margin deviations
            query = self.db.query(Coin).filter(
                and_(
                    Coin.computed_price.isnot(None),
                    Coin.paid_price.isnot(None),
                    Coin.paid_price > 0
                )
            )
            
            if rule.product_specific and rule.product_id:
                query = query.filter(Coin.id == rule.product_id)
            
            coins = query.all()
            
            for coin in coins:
                if coin.computed_price and coin.paid_price:
                    profit_margin = (coin.computed_price - coin.paid_price) / coin.computed_price
                    deviation = abs(profit_margin - expected_margin)
                    
                    if deviation >= deviation_threshold:
                        severity = "high" if deviation >= deviation_threshold * 2 else "medium"
                        
                        alert_data = AlertCreate(
                            rule_id=rule.id,
                            alert_type="profit_margin",
                            severity=severity,
                            title=f"Profit Margin Alert: {coin.name}",
                            message=f"Profit margin deviation detected: {profit_margin:.1%} (expected: {expected_margin:.1%})",
                            context_data={
                                "coin_id": coin.id,
                                "actual_margin": profit_margin,
                                "expected_margin": expected_margin,
                                "deviation": deviation,
                                "coin_name": coin.name
                            },
                            affected_entity_id=coin.id,
                            affected_entity_type="coin"
                        )
                        alert = self.create_alert(alert_data)
                        alerts.append(alert)
                        
                        # Update rule trigger count
                        rule.last_triggered = datetime.utcnow()
                        rule.trigger_count += 1

        self.db.commit()
        return alerts

    def run_all_alert_checks(self) -> List[Alert]:
        """Run all alert checks and return new alerts."""
        all_alerts = []
        
        try:
            all_alerts.extend(self.check_low_inventory_alerts())
            all_alerts.extend(self.check_price_change_alerts())
            all_alerts.extend(self.check_system_issue_alerts())
            all_alerts.extend(self.check_sales_milestone_alerts())
            all_alerts.extend(self.check_profit_margin_alerts())
        except Exception as e:
            logger.error(f"Error running alert checks: {str(e)}")
            
            # Create system error alert
            error_alert = AlertCreate(
                rule_id=0,  # System rule
                alert_type="system_issue",
                severity="critical",
                title="Alert System Error",
                message=f"Error running alert checks: {str(e)}",
                context_data={"error": str(e)}
            )
            all_alerts.append(self.create_alert(error_alert))
        
        return all_alerts

    def get_system_health(self) -> SystemHealthCheck:
        """Get system health status."""
        try:
            # Check database connection
            self.db.execute("SELECT 1")
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"
        
        # Check Redis connection (if available)
        try:
            # This would be implemented with actual Redis check
            redis_status = "healthy"
        except Exception:
            redis_status = "unhealthy"
        
        # Check Shopify connection (if available)
        try:
            # This would be implemented with actual Shopify API check
            shopify_connection = "healthy"
        except Exception:
            shopify_connection = "unhealthy"
        
        # Check alert system
        try:
            recent_alerts = self.get_recent_alerts(hours=1)
            alert_system_status = "healthy"
        except Exception:
            alert_system_status = "unhealthy"
        
        # Determine overall status
        overall_status = "healthy"
        if any(status != "healthy" for status in [database_status, redis_status, shopify_connection, alert_system_status]):
            overall_status = "degraded"
        if any(status == "unhealthy" for status in [database_status, redis_status]):
            overall_status = "unhealthy"
        
        return SystemHealthCheck(
            database_status=database_status,
            redis_status=redis_status,
            shopify_connection=shopify_connection,
            alert_system_status=alert_system_status,
            last_check=datetime.utcnow(),
            overall_status=overall_status
        )

    def create_notification_template(self, template_data: NotificationTemplateCreate, created_by: str) -> NotificationTemplate:
        """Create a notification template."""
        template = NotificationTemplate(
            name=template_data.name,
            template_type=template_data.template_type,
            alert_type=template_data.alert_type,
            subject_template=template_data.subject_template,
            body_template=template_data.body_template,
            available_variables=template_data.available_variables or [],
            active=True,
            created_by=created_by
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_notification_templates(self, alert_type: Optional[str] = None) -> List[NotificationTemplate]:
        """Get notification templates."""
        query = self.db.query(NotificationTemplate).filter(NotificationTemplate.active == True)
        if alert_type:
            query = query.filter(NotificationTemplate.alert_type == alert_type)
        return query.order_by(NotificationTemplate.name).all()

    def log_notification(self, alert_id: int, notification_type: str, recipient: str, 
                        subject: Optional[str], message: str, status: str, 
                        error_message: Optional[str] = None) -> NotificationLog:
        """Log a notification attempt."""
        log = NotificationLog(
            alert_id=alert_id,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            message=message,
            status=status,
            error_message=error_message,
            sent_at=datetime.utcnow() if status == "sent" else None
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        total_alerts = self.db.query(Alert).count()
        active_alerts = self.db.query(Alert).filter(Alert.status == "active").count()
        resolved_alerts = self.db.query(Alert).filter(Alert.status == "resolved").count()
        
        # Alerts by type
        alerts_by_type = self.db.query(
            Alert.alert_type,
            func.count(Alert.id)
        ).group_by(Alert.alert_type).all()
        
        # Alerts by severity
        alerts_by_severity = self.db.query(
            Alert.severity,
            func.count(Alert.id)
        ).group_by(Alert.severity).all()
        
        # Recent alert trends (last 7 days)
        since = datetime.utcnow() - timedelta(days=7)
        recent_trends = self.db.query(
            func.date(Alert.created_at).label('date'),
            func.count(Alert.id).label('count')
        ).filter(Alert.created_at >= since).group_by(func.date(Alert.created_at)).all()
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "alerts_by_type": dict(alerts_by_type),
            "alerts_by_severity": dict(alerts_by_severity),
            "recent_trends": [{"date": str(trend.date), "count": trend.count} for trend in recent_trends]
        }


