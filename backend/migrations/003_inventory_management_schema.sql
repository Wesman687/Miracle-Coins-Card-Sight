-- Migration: Add Inventory Management Tables
-- Description: Creates tables for inventory management, locations, movements, and analysis
-- Date: 2025-01-27

-- Locations Table
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    address TEXT,
    location_type VARCHAR(50) DEFAULT 'store' CHECK (location_type IN ('store', 'warehouse', 'vault')),
    active BOOLEAN DEFAULT TRUE,
    settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inventory Items Table
CREATE TABLE IF NOT EXISTS inventory_items (
    id SERIAL PRIMARY KEY,
    coin_id BIGINT NOT NULL REFERENCES coins(id),
    location_id INTEGER NOT NULL REFERENCES locations(id),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    reserved_quantity INTEGER DEFAULT 0 CHECK (reserved_quantity >= 0),
    available_quantity INTEGER NOT NULL CHECK (available_quantity >= 0),
    last_counted TIMESTAMP WITH TIME ZONE,
    last_moved TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inventory Movements Table
CREATE TABLE IF NOT EXISTS inventory_movements (
    id SERIAL PRIMARY KEY,
    coin_id BIGINT NOT NULL REFERENCES coins(id),
    from_location_id INTEGER REFERENCES locations(id),
    to_location_id INTEGER NOT NULL REFERENCES locations(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    movement_type VARCHAR(50) NOT NULL CHECK (movement_type IN ('transfer', 'sale', 'adjustment', 'count')),
    reason VARCHAR(200),
    reference_id VARCHAR(100),
    moved_by VARCHAR(100),
    moved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dead Stock Analysis Table
CREATE TABLE IF NOT EXISTS dead_stock_analysis (
    id SERIAL PRIMARY KEY,
    coin_id BIGINT NOT NULL REFERENCES coins(id),
    days_since_last_sale INTEGER,
    days_since_added INTEGER,
    profit_margin DECIMAL(5,2),
    category VARCHAR(50) CHECK (category IN ('slow_moving', 'dead_stock', 'fast_moving')),
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    criteria_used JSONB
);

-- Inventory Metrics Table
CREATE TABLE IF NOT EXISTS inventory_metrics (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    total_coins INTEGER DEFAULT 0,
    total_value DECIMAL(12,2) DEFAULT 0,
    dead_stock_count INTEGER DEFAULT 0,
    dead_stock_value DECIMAL(12,2) DEFAULT 0,
    turnover_rate DECIMAL(5,2) DEFAULT 0,
    location_breakdown JSONB,
    category_breakdown JSONB,
    profit_margin_analysis JSONB,
    average_value_per_coin DECIMAL(10,2) DEFAULT 0,
    dead_stock_percentage DECIMAL(5,2) DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Turnover Analysis Table
CREATE TABLE IF NOT EXISTS turnover_analysis (
    id SERIAL PRIMARY KEY,
    coin_id BIGINT NOT NULL REFERENCES coins(id),
    analysis_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    analysis_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    days_since_last_sale INTEGER,
    days_since_added INTEGER,
    sales_count INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    turnover_category VARCHAR(50) CHECK (turnover_category IN ('fast_moving', 'slow_moving', 'dead_stock')),
    sales_velocity DECIMAL(8,2) DEFAULT 0,
    profit_margin DECIMAL(5,2) DEFAULT 0,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    criteria_used JSONB
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_inventory_items_coin_id ON inventory_items(coin_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_location_id ON inventory_items(location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_available_quantity ON inventory_items(available_quantity);

CREATE INDEX IF NOT EXISTS idx_inventory_movements_coin_id ON inventory_movements(coin_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_from_location ON inventory_movements(from_location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_to_location ON inventory_movements(to_location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_moved_at ON inventory_movements(moved_at);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_type ON inventory_movements(movement_type);

CREATE INDEX IF NOT EXISTS idx_dead_stock_analysis_coin_id ON dead_stock_analysis(coin_id);
CREATE INDEX IF NOT EXISTS idx_dead_stock_analysis_category ON dead_stock_analysis(category);
CREATE INDEX IF NOT EXISTS idx_dead_stock_analysis_date ON dead_stock_analysis(analysis_date);

CREATE INDEX IF NOT EXISTS idx_inventory_metrics_period_type ON inventory_metrics(period_type);
CREATE INDEX IF NOT EXISTS idx_inventory_metrics_period_start ON inventory_metrics(period_start);
CREATE INDEX IF NOT EXISTS idx_inventory_metrics_period_end ON inventory_metrics(period_end);

CREATE INDEX IF NOT EXISTS idx_turnover_analysis_coin_id ON turnover_analysis(coin_id);
CREATE INDEX IF NOT EXISTS idx_turnover_analysis_category ON turnover_analysis(turnover_category);
CREATE INDEX IF NOT EXISTS idx_turnover_analysis_date ON turnover_analysis(analysis_date);

CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);
CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(location_type);
CREATE INDEX IF NOT EXISTS idx_locations_active ON locations(active);

-- Insert Default Locations
INSERT INTO locations (name, location_type, settings) VALUES
('Main Store', 'store', '{"address": "123 Main St", "cash_register": true, "display_cases": 5}'),
('Warehouse', 'warehouse', '{"address": "456 Warehouse Ave", "storage_units": 10, "climate_controlled": true}'),
('Vault', 'vault', '{"security_level": "high", "access_restricted": true, "insurance_required": true}')
ON CONFLICT (name) DO NOTHING;

-- Add Comments for Documentation
COMMENT ON TABLE locations IS 'Physical locations where inventory is stored';
COMMENT ON TABLE inventory_items IS 'Individual inventory items with quantity tracking';
COMMENT ON TABLE inventory_movements IS 'History of all inventory movements between locations';
COMMENT ON TABLE dead_stock_analysis IS 'Analysis of slow-moving and dead stock items';
COMMENT ON TABLE inventory_metrics IS 'Aggregated inventory metrics for different time periods';
COMMENT ON TABLE turnover_analysis IS 'Analysis of inventory turnover rates and sales velocity';

COMMENT ON COLUMN inventory_items.available_quantity IS 'Calculated as quantity - reserved_quantity';
COMMENT ON COLUMN inventory_items.reserved_quantity IS 'Quantity reserved for pending sales or transfers';
COMMENT ON COLUMN inventory_movements.movement_type IS 'Type of movement: transfer, sale, adjustment, count';
COMMENT ON COLUMN inventory_movements.reference_id IS 'Reference to external system (sale ID, order ID, etc.)';
COMMENT ON COLUMN dead_stock_analysis.category IS 'Classification: slow_moving, dead_stock, fast_moving';
COMMENT ON COLUMN turnover_analysis.sales_velocity IS 'Sales per day for the analysis period';
COMMENT ON COLUMN turnover_analysis.turnover_category IS 'Classification based on sales velocity';

-- Create Function to Update Available Quantity
CREATE OR REPLACE FUNCTION update_available_quantity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.available_quantity = NEW.quantity - COALESCE(NEW.reserved_quantity, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create Trigger to Automatically Update Available Quantity
CREATE TRIGGER trigger_update_available_quantity
    BEFORE INSERT OR UPDATE ON inventory_items
    FOR EACH ROW
    EXECUTE FUNCTION update_available_quantity();


