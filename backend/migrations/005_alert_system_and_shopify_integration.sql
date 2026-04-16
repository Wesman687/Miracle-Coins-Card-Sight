-- Migration: 005_alert_system_and_shopify_integration.sql
-- Description: Create tables for alert system and Shopify integration
-- Date: 2025-01-27

-- Alert Rules Table
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('low_inventory', 'price_change', 'system_issue', 'sales_milestone', 'profit_margin')),
    conditions JSONB NOT NULL,
    product_specific BOOLEAN DEFAULT FALSE,
    product_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
    notification_channels TEXT[] DEFAULT ARRAY['in_app'],
    notification_frequency VARCHAR(20) DEFAULT 'immediate' CHECK (notification_frequency IN ('immediate', 'daily', 'weekly')),
    enabled BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alerts Table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alert_rules(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('low_inventory', 'price_change', 'system_issue', 'sales_milestone', 'profit_margin')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    context_data JSONB,
    affected_entity_id INTEGER,
    affected_entity_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved', 'dismissed')),
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification Templates Table
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    template_type VARCHAR(20) NOT NULL CHECK (template_type IN ('email', 'sms', 'in_app')),
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('low_inventory', 'price_change', 'system_issue', 'sales_milestone', 'profit_margin')),
    subject_template TEXT,
    body_template TEXT NOT NULL,
    available_variables TEXT[],
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification Logs Table
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    notification_type VARCHAR(20) NOT NULL CHECK (notification_type IN ('email', 'sms', 'in_app')),
    recipient VARCHAR(200) NOT NULL,
    subject VARCHAR(500),
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('sent', 'failed', 'pending')),
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Shopify Integration Table
CREATE TABLE shopify_integrations (
    id SERIAL PRIMARY KEY,
    shop_domain VARCHAR(200) NOT NULL,
    access_token VARCHAR(500) NOT NULL,
    webhook_secret VARCHAR(500),
    sync_products BOOLEAN DEFAULT TRUE,
    sync_inventory BOOLEAN DEFAULT TRUE,
    sync_orders BOOLEAN DEFAULT TRUE,
    sync_pricing BOOLEAN DEFAULT TRUE,
    sync_frequency VARCHAR(20) DEFAULT 'hourly' CHECK (sync_frequency IN ('real_time', 'hourly', 'daily')),
    active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Shopify Sync Logs Table
CREATE TABLE shopify_sync_logs (
    id SERIAL PRIMARY KEY,
    integration_id INTEGER REFERENCES shopify_integrations(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL CHECK (sync_type IN ('products', 'inventory', 'orders', 'pricing', 'all')),
    sync_direction VARCHAR(20) NOT NULL CHECK (sync_direction IN ('to_shopify', 'from_shopify')),
    items_processed INTEGER DEFAULT 0,
    items_successful INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    status VARCHAR(30) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'completed_with_errors', 'failed'))
);

-- Shopify Products Table
CREATE TABLE shopify_products (
    id SERIAL PRIMARY KEY,
    coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
    shopify_product_id VARCHAR(100) NOT NULL,
    shopify_variant_id VARCHAR(100),
    shopify_handle VARCHAR(200),
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'error')),
    last_synced TIMESTAMP WITH TIME ZONE,
    sync_error TEXT,
    shopify_title VARCHAR(500),
    shopify_description TEXT,
    shopify_price DECIMAL(10,2),
    shopify_inventory_quantity INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coin_id, shopify_product_id)
);

-- Shopify Orders Table
CREATE TABLE shopify_orders (
    id SERIAL PRIMARY KEY,
    shopify_order_id VARCHAR(100) NOT NULL UNIQUE,
    order_number VARCHAR(100),
    customer_email VARCHAR(200),
    customer_name VARCHAR(200),
    total_price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    order_status VARCHAR(50),
    fulfillment_status VARCHAR(50),
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'error')),
    last_synced TIMESTAMP WITH TIME ZONE,
    sync_error TEXT,
    order_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Shopify Order Items Table
CREATE TABLE shopify_order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES shopify_orders(id) ON DELETE CASCADE,
    coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
    shopify_line_item_id VARCHAR(100),
    product_title VARCHAR(500),
    variant_title VARCHAR(200),
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL
);

-- Create indexes for better performance
CREATE INDEX idx_alert_rules_alert_type ON alert_rules(alert_type);
CREATE INDEX idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX idx_alert_rules_product_id ON alert_rules(product_id);

CREATE INDEX idx_alerts_rule_id ON alerts(rule_id);
CREATE INDEX idx_alerts_alert_type ON alerts(alert_type);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_triggered_at ON alerts(triggered_at);
CREATE INDEX idx_alerts_affected_entity ON alerts(affected_entity_id, affected_entity_type);

CREATE INDEX idx_notification_templates_alert_type ON notification_templates(alert_type);
CREATE INDEX idx_notification_templates_active ON notification_templates(active);

CREATE INDEX idx_notification_logs_alert_id ON notification_logs(alert_id);
CREATE INDEX idx_notification_logs_status ON notification_logs(status);
CREATE INDEX idx_notification_logs_created_at ON notification_logs(created_at);

CREATE INDEX idx_shopify_integrations_active ON shopify_integrations(active);
CREATE INDEX idx_shopify_integrations_shop_domain ON shopify_integrations(shop_domain);

CREATE INDEX idx_shopify_sync_logs_integration_id ON shopify_sync_logs(integration_id);
CREATE INDEX idx_shopify_sync_logs_sync_type ON shopify_sync_logs(sync_type);
CREATE INDEX idx_shopify_sync_logs_started_at ON shopify_sync_logs(started_at);
CREATE INDEX idx_shopify_sync_logs_status ON shopify_sync_logs(status);

CREATE INDEX idx_shopify_products_coin_id ON shopify_products(coin_id);
CREATE INDEX idx_shopify_products_shopify_product_id ON shopify_products(shopify_product_id);
CREATE INDEX idx_shopify_products_sync_status ON shopify_products(sync_status);

CREATE INDEX idx_shopify_orders_shopify_order_id ON shopify_orders(shopify_order_id);
CREATE INDEX idx_shopify_orders_order_date ON shopify_orders(order_date);
CREATE INDEX idx_shopify_orders_sync_status ON shopify_orders(sync_status);

CREATE INDEX idx_shopify_order_items_order_id ON shopify_order_items(order_id);
CREATE INDEX idx_shopify_order_items_coin_id ON shopify_order_items(coin_id);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alert_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE ON notification_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shopify_integrations_updated_at BEFORE UPDATE ON shopify_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shopify_products_updated_at BEFORE UPDATE ON shopify_products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shopify_orders_updated_at BEFORE UPDATE ON shopify_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default alert rules
INSERT INTO alert_rules (name, description, alert_type, conditions, notification_channels, created_by) VALUES
('Low Inventory Alert', 'Alert when inventory falls below threshold', 'low_inventory', '{"threshold": 10}', ARRAY['in_app', 'email'], 'system'),
('Price Change Alert', 'Alert on significant price changes', 'price_change', '{"threshold_percent": 5, "time_window_hours": 24}', ARRAY['in_app'], 'system'),
('System Health Check', 'Monitor system health status', 'system_issue', '{"check_type": "overall"}', ARRAY['in_app', 'email'], 'system'),
('Daily Sales Milestone', 'Alert when daily sales target is reached', 'sales_milestone', '{"milestone_type": "daily_sales", "threshold": 1000, "time_period": "daily"}', ARRAY['in_app'], 'system'),
('Profit Margin Alert', 'Alert on profit margin deviations', 'profit_margin', '{"expected_margin": 0.3, "deviation_threshold": 0.1}', ARRAY['in_app'], 'system');

-- Insert default notification templates
INSERT INTO notification_templates (name, template_type, alert_type, subject_template, body_template, available_variables, created_by) VALUES
('Low Inventory Email', 'email', 'low_inventory', 'Low Inventory Alert: {{coin_name}}', 'Inventory for {{coin_name}} is below threshold ({{current_quantity}} <= {{threshold}}). Please restock soon.', ARRAY['coin_name', 'current_quantity', 'threshold'], 'system'),
('Price Change In-App', 'in_app', 'price_change', 'Price Change: {{coin_name}}', 'Price change of {{change_percent}}% detected for {{coin_name}} ({{old_price}} -> {{new_price}}).', ARRAY['coin_name', 'change_percent', 'old_price', 'new_price'], 'system'),
('System Issue Email', 'email', 'system_issue', 'System Health Issue', 'System health check failed: {{overall_status}}. Please investigate immediately.', ARRAY['overall_status'], 'system'),
('Sales Milestone In-App', 'in_app', 'sales_milestone', 'Sales Milestone Reached', 'Sales target of ${{threshold}} reached for {{time_period}} period. Total: ${{actual_value}}', ARRAY['threshold', 'time_period', 'actual_value'], 'system'),
('Profit Margin In-App', 'in_app', 'profit_margin', 'Profit Margin Alert: {{coin_name}}', 'Profit margin deviation detected: {{actual_margin}}% (expected: {{expected_margin}}%)', ARRAY['coin_name', 'actual_margin', 'expected_margin'], 'system');

-- Add comments to tables
COMMENT ON TABLE alert_rules IS 'Configuration rules for generating alerts';
COMMENT ON TABLE alerts IS 'Generated alerts based on rules';
COMMENT ON TABLE notification_templates IS 'Templates for alert notifications';
COMMENT ON TABLE notification_logs IS 'Log of notification attempts';
COMMENT ON TABLE shopify_integrations IS 'Shopify store integration configurations';
COMMENT ON TABLE shopify_sync_logs IS 'Log of Shopify synchronization operations';
COMMENT ON TABLE shopify_products IS 'Mapping between coins and Shopify products';
COMMENT ON TABLE shopify_orders IS 'Orders synced from Shopify';
COMMENT ON TABLE shopify_order_items IS 'Items within Shopify orders';


