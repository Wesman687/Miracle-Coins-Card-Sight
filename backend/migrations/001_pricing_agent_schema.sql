-- Pricing Agent Database Schema
-- Miracle Coins CoinSync Pro

-- Market prices table for storing pricing data
CREATE TABLE IF NOT EXISTS market_prices (
    id BIGSERIAL PRIMARY KEY,
    coin_id BIGINT REFERENCES coins(id) ON DELETE CASCADE,
    spot_price DECIMAL(10,2) NOT NULL,
    market_avg DECIMAL(10,2),
    market_min DECIMAL(10,2),
    market_max DECIMAL(10,2),
    melt_value DECIMAL(10,2) NOT NULL,
    markup_factor DECIMAL(6,3) NOT NULL DEFAULT 1.500,
    final_price DECIMAL(10,2) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 0.50,
    scam_detected BOOLEAN DEFAULT FALSE,
    scam_reason TEXT,
    source TEXT NOT NULL,
    sample_size INTEGER DEFAULT 1,
    price_change_percent DECIMAL(5,2),
    last_updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pricing configuration table
CREATE TABLE IF NOT EXISTS pricing_config (
    id BIGSERIAL PRIMARY KEY,
    coin_type VARCHAR(50) NOT NULL,
    min_markup DECIMAL(6,3) NOT NULL DEFAULT 1.200,
    max_markup DECIMAL(6,3) NOT NULL DEFAULT 2.000,
    default_markup DECIMAL(6,3) NOT NULL DEFAULT 1.500,
    scam_threshold DECIMAL(6,3) NOT NULL DEFAULT 0.300,
    confidence_threshold DECIMAL(3,2) NOT NULL DEFAULT 0.70,
    price_update_threshold DECIMAL(5,2) NOT NULL DEFAULT 3.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scam detection results table
CREATE TABLE IF NOT EXISTS scam_detection_results (
    id BIGSERIAL PRIMARY KEY,
    coin_id BIGINT REFERENCES coins(id) ON DELETE CASCADE,
    market_price_id BIGINT REFERENCES market_prices(id) ON DELETE CASCADE,
    scam_probability DECIMAL(3,2) NOT NULL,
    scam_reasons TEXT[] NOT NULL DEFAULT '{}',
    detection_method VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    price_deviation DECIMAL(5,2),
    statistical_z_score DECIMAL(8,4),
    reviewed_by BIGINT,
    reviewed_at TIMESTAMP,
    is_false_positive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Price history table for tracking changes
CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    coin_id BIGINT REFERENCES coins(id) ON DELETE CASCADE,
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2) NOT NULL,
    price_change_percent DECIMAL(5,2),
    change_reason VARCHAR(100),
    spot_price_at_change DECIMAL(10,2),
    market_avg_at_change DECIMAL(10,2),
    updated_by VARCHAR(50) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_prices_coin_id ON market_prices(coin_id);
CREATE INDEX IF NOT EXISTS idx_market_prices_created_at ON market_prices(created_at);
CREATE INDEX IF NOT EXISTS idx_market_prices_scam_detected ON market_prices(scam_detected);
CREATE INDEX IF NOT EXISTS idx_market_prices_confidence_score ON market_prices(confidence_score);

CREATE INDEX IF NOT EXISTS idx_pricing_config_coin_type ON pricing_config(coin_type);
CREATE INDEX IF NOT EXISTS idx_pricing_config_active ON pricing_config(is_active);

CREATE INDEX IF NOT EXISTS idx_scam_detection_coin_id ON scam_detection_results(coin_id);
CREATE INDEX IF NOT EXISTS idx_scam_detection_probability ON scam_detection_results(scam_probability);
CREATE INDEX IF NOT EXISTS idx_scam_detection_created_at ON scam_detection_results(created_at);

CREATE INDEX IF NOT EXISTS idx_price_history_coin_id ON price_history(coin_id);
CREATE INDEX IF NOT EXISTS idx_price_history_created_at ON price_history(created_at);

-- Insert default pricing configurations
INSERT INTO pricing_config (coin_type, min_markup, max_markup, default_markup, scam_threshold, confidence_threshold, price_update_threshold) VALUES
('silver_eagle', 1.300, 1.800, 1.550, 0.250, 0.75, 3.00),
('silver_round', 1.200, 1.600, 1.400, 0.300, 0.70, 3.00),
('silver_bar', 1.150, 1.500, 1.350, 0.350, 0.65, 3.00),
('gold_coin', 1.400, 2.000, 1.700, 0.200, 0.80, 2.50),
('platinum_coin', 1.350, 1.900, 1.650, 0.250, 0.75, 2.50),
('generic_silver', 1.200, 1.700, 1.450, 0.300, 0.70, 3.00)
ON CONFLICT DO NOTHING;




