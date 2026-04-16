-- Migration: Add Sales Management Tables
-- Description: Creates tables for sales tracking, channels, forecasting, and metrics
-- Date: 2025-01-27

-- Sales Channels Table
CREATE TABLE IF NOT EXISTS sales_channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('shopify', 'in_store', 'auction', 'direct')),
    active BOOLEAN DEFAULT TRUE,
    settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Table
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    coin_id BIGINT NOT NULL REFERENCES coins(id),
    channel_id INTEGER NOT NULL REFERENCES sales_channels(id),
    sale_price DECIMAL(10,2) NOT NULL CHECK (sale_price > 0),
    profit DECIMAL(10,2) NOT NULL,
    quantity_sold INTEGER DEFAULT 1 CHECK (quantity_sold > 0),
    customer_info JSONB,
    transaction_id VARCHAR(100),
    sold_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Forecasts Table
CREATE TABLE IF NOT EXISTS sales_forecasts (
    id SERIAL PRIMARY KEY,
    forecast_type VARCHAR(20) NOT NULL CHECK (forecast_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
    forecast_horizon INTEGER NOT NULL CHECK (forecast_horizon > 0),
    confidence_level INTEGER NOT NULL CHECK (confidence_level BETWEEN 50 AND 95),
    forecast_data JSONB NOT NULL,
    factors_used JSONB,
    accuracy_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    include_seasonality BOOLEAN DEFAULT TRUE,
    include_trends BOOLEAN DEFAULT TRUE,
    include_external_factors BOOLEAN DEFAULT FALSE
);

-- Forecast Periods Table
CREATE TABLE IF NOT EXISTS forecast_periods (
    id SERIAL PRIMARY KEY,
    forecast_id INTEGER NOT NULL REFERENCES sales_forecasts(id),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    period_name VARCHAR(50) NOT NULL,
    predicted_revenue DECIMAL(12,2) NOT NULL,
    confidence_min DECIMAL(12,2) NOT NULL,
    confidence_max DECIMAL(12,2) NOT NULL,
    factors JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Metrics Table
CREATE TABLE IF NOT EXISTS sales_metrics (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    total_sales DECIMAL(12,2) DEFAULT 0,
    total_profit DECIMAL(12,2) DEFAULT 0,
    sales_count INTEGER DEFAULT 0,
    unique_customers INTEGER DEFAULT 0,
    channel_breakdown JSONB,
    top_items JSONB,
    average_sale_value DECIMAL(10,2) DEFAULT 0,
    profit_margin_percentage DECIMAL(5,2) DEFAULT 0,
    sales_velocity DECIMAL(8,2) DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_sales_coin_id ON sales(coin_id);
CREATE INDEX IF NOT EXISTS idx_sales_channel_id ON sales(channel_id);
CREATE INDEX IF NOT EXISTS idx_sales_sold_at ON sales(sold_at);
CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales(created_at);

CREATE INDEX IF NOT EXISTS idx_sales_channels_name ON sales_channels(name);
CREATE INDEX IF NOT EXISTS idx_sales_channels_type ON sales_channels(channel_type);
CREATE INDEX IF NOT EXISTS idx_sales_channels_active ON sales_channels(active);

CREATE INDEX IF NOT EXISTS idx_sales_forecasts_type ON sales_forecasts(forecast_type);
CREATE INDEX IF NOT EXISTS idx_sales_forecasts_created_at ON sales_forecasts(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_forecasts_valid_until ON sales_forecasts(valid_until);

CREATE INDEX IF NOT EXISTS idx_forecast_periods_forecast_id ON forecast_periods(forecast_id);
CREATE INDEX IF NOT EXISTS idx_forecast_periods_period_start ON forecast_periods(period_start);

CREATE INDEX IF NOT EXISTS idx_sales_metrics_period_type ON sales_metrics(period_type);
CREATE INDEX IF NOT EXISTS idx_sales_metrics_period_start ON sales_metrics(period_start);
CREATE INDEX IF NOT EXISTS idx_sales_metrics_period_end ON sales_metrics(period_end);

-- Insert Default Sales Channels
INSERT INTO sales_channels (name, channel_type, settings) VALUES
('Shopify', 'shopify', '{"webhook_url": "/webhooks/shopify/order-created", "sync_enabled": true}'),
('In-Store', 'in_store', '{"location": "main_store", "cash_register": true}'),
('Auction', 'auction', '{"platform": "local_auction", "fee_percentage": 10}'),
('Direct Sales', 'direct', '{"customer_type": "walk_in", "payment_methods": ["cash", "card"]}')
ON CONFLICT (name) DO NOTHING;

-- Add Comments for Documentation
COMMENT ON TABLE sales_channels IS 'Sales channels for tracking different sales methods';
COMMENT ON TABLE sales IS 'Individual sales records with profit tracking';
COMMENT ON TABLE sales_forecasts IS 'Revenue forecasts with confidence levels and factors';
COMMENT ON TABLE forecast_periods IS 'Individual forecast periods with predictions and confidence ranges';
COMMENT ON TABLE sales_metrics IS 'Aggregated sales metrics for different time periods';

COMMENT ON COLUMN sales.profit IS 'Calculated profit: sale_price - paid_price';
COMMENT ON COLUMN sales.customer_info IS 'Customer details: name, email, phone, etc.';
COMMENT ON COLUMN sales.transaction_id IS 'External transaction ID for reconciliation';
COMMENT ON COLUMN sales_forecasts.forecast_data IS 'Array of forecast periods with predictions';
COMMENT ON COLUMN sales_forecasts.factors_used IS 'Factors considered in the forecast';
COMMENT ON COLUMN sales_forecasts.accuracy_score IS 'Historical accuracy percentage';
COMMENT ON COLUMN sales_metrics.channel_breakdown IS 'Sales breakdown by channel';
COMMENT ON COLUMN sales_metrics.top_items IS 'Top selling coins for the period';
COMMENT ON COLUMN sales_metrics.sales_velocity IS 'Sales per day for the period';


