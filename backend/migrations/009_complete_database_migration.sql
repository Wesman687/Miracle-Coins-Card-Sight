-- Miracle Coins CoinSync Pro - Complete Database Migration
-- Date: 2025-01-28
-- Description: Complete database setup with collections and flexible pricing

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================
-- 1. COLLECTIONS TABLE (Simplified System)
-- ==============================================

-- Create collections table
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#FFFFFF',
    icon VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    shopify_collection_id VARCHAR(255) UNIQUE,
    default_markup NUMERIC(6, 3) DEFAULT 1.300,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add collection_id to coins table
ALTER TABLE coins ADD COLUMN IF NOT EXISTS collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL;

-- Create indexes for collections
CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name);
CREATE INDEX IF NOT EXISTS idx_collections_sort ON collections(sort_order);
CREATE INDEX IF NOT EXISTS idx_collections_shopify ON collections(shopify_collection_id);
CREATE INDEX IF NOT EXISTS idx_coins_collection ON coins(collection_id);

-- ==============================================
-- 2. FLEXIBLE PRICING STRATEGIES
-- ==============================================

-- Add new pricing fields to coins table
ALTER TABLE coins ADD COLUMN IF NOT EXISTS fixed_price DECIMAL(10,2);

-- Update price_strategy default value and add new options
ALTER TABLE coins ALTER COLUMN price_strategy SET DEFAULT 'paid_price_multiplier';
ALTER TABLE coins ALTER COLUMN price_multiplier SET DEFAULT 1.500;

-- Add check constraint for price_strategy values
ALTER TABLE coins DROP CONSTRAINT IF EXISTS coins_price_strategy_check;
ALTER TABLE coins ADD CONSTRAINT coins_price_strategy_check 
CHECK (price_strategy IN ('paid_price_multiplier', 'silver_spot_multiplier', 'gold_spot_multiplier', 'fixed_price', 'entry_based'));

-- Update existing records to use new default pricing strategy
UPDATE coins SET price_strategy = 'paid_price_multiplier' WHERE price_strategy = 'spot_multiplier';
UPDATE coins SET price_multiplier = 1.500 WHERE price_multiplier = 1.300;

-- Add indexes for pricing performance
CREATE INDEX IF NOT EXISTS idx_coins_price_strategy ON coins(price_strategy);
CREATE INDEX IF NOT EXISTS idx_coins_fixed_price ON coins(fixed_price) WHERE fixed_price IS NOT NULL;

-- ==============================================
-- 3. SAMPLE DATA
-- ==============================================

-- Insert default collections
INSERT INTO collections (name, description, color, icon, shopify_collection_id, default_markup) VALUES
('Silver Bullion', 'General silver bullion products', '#C0C0C0', '💰', 'gid://shopify/Collection/12345', 1.150),
('Gold Bullion', 'General gold bullion products', '#FFD700', '👑', 'gid://shopify/Collection/67890', 1.080),
('Mercury Dimes', 'Classic Mercury Dime collection', '#A9A9A9', '🪙', 'gid://shopify/Collection/11223', 1.500),
('Morgan Dollars', 'Historic Morgan Silver Dollars', '#D3D3D3', '💵', 'gid://shopify/Collection/44556', 1.400),
('Kennedy Half Dollars', 'Kennedy Half Dollar collection', '#BEBEBE', '🥈', 'gid://shopify/Collection/77889', 1.350),
('Silver Eagles', 'American Silver Eagles 1986-present', '#C0C0C0', '🦅', 'gid://shopify/Collection/33445', 1.200),
('Gold Eagles', 'American Gold Eagles 1986-present', '#FFD700', '🦅', 'gid://shopify/Collection/55667', 1.100),
('Peace Dollars', 'Peace Silver Dollars 1921-1935', '#D3D3D3', '🕊️', 'gid://shopify/Collection/77890', 1.450),
('Walking Liberty', 'Walking Liberty Half Dollars 1916-1947', '#C0C0C0', '🚶', 'gid://shopify/Collection/88901', 1.350),
('Commemorative', 'Special commemorative coins', '#8B5CF6', '⭐', 'gid://shopify/Collection/99012', 1.600)
ON CONFLICT (name) DO NOTHING;

-- ==============================================
-- 4. UTILITY FUNCTIONS
-- ==============================================

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for collections updated_at
CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for coins updated_at
CREATE TRIGGER update_coins_updated_at BEFORE UPDATE ON coins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- 5. COMMENTS FOR DOCUMENTATION
-- ==============================================

-- Add comments for documentation
COMMENT ON TABLE collections IS 'Collections for organizing coins (replaces categories)';
COMMENT ON COLUMN collections.name IS 'Collection name (unique)';
COMMENT ON COLUMN collections.color IS 'Hex color code for UI display';
COMMENT ON COLUMN collections.icon IS 'Icon identifier for UI display';
COMMENT ON COLUMN collections.shopify_collection_id IS 'Shopify collection ID for integration';
COMMENT ON COLUMN collections.default_markup IS 'Default pricing markup for coins in this collection';

COMMENT ON COLUMN coins.price_strategy IS 'Pricing strategy: paid_price_multiplier, silver_spot_multiplier, gold_spot_multiplier, fixed_price, entry_based';
COMMENT ON COLUMN coins.price_multiplier IS 'Multiplier value for pricing calculations (default varies by strategy)';
COMMENT ON COLUMN coins.fixed_price IS 'Hardcoded price when price_strategy is fixed_price';
COMMENT ON COLUMN coins.paid_price IS 'Price paid for the coin (used as base for paid_price_multiplier)';
COMMENT ON COLUMN coins.entry_spot IS 'Spot price at time of purchase (used for entry_based pricing)';
COMMENT ON COLUMN coins.entry_melt IS 'Melt value at time of purchase (used for entry_based pricing)';
COMMENT ON COLUMN coins.collection_id IS 'Reference to collections table for organization';

-- ==============================================
-- 6. VERIFICATION QUERIES
-- ==============================================

-- Verify collections were created
SELECT 'Collections created:' as status, COUNT(*) as count FROM collections;

-- Verify pricing constraints
SELECT 'Pricing strategies available:' as status, 
       string_agg(DISTINCT price_strategy, ', ') as strategies 
FROM coins 
WHERE price_strategy IS NOT NULL;

-- Show sample collections
SELECT 'Sample collections:' as status, name, color, icon, default_markup FROM collections LIMIT 5;

-- ==============================================
-- MIGRATION COMPLETE
-- ==============================================

SELECT 'Database migration completed successfully!' as status;
