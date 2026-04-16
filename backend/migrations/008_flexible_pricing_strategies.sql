-- Migration: Add Flexible Pricing Strategy Fields
-- Date: 2025-01-28
-- Description: Add support for multiple pricing strategies and hardcoded pricing

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

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_coins_price_strategy ON coins(price_strategy);
CREATE INDEX IF NOT EXISTS idx_coins_fixed_price ON coins(fixed_price) WHERE fixed_price IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN coins.price_strategy IS 'Pricing strategy: paid_price_multiplier, silver_spot_multiplier, gold_spot_multiplier, fixed_price, entry_based';
COMMENT ON COLUMN coins.price_multiplier IS 'Multiplier value for pricing calculations (default varies by strategy)';
COMMENT ON COLUMN coins.fixed_price IS 'Hardcoded price when price_strategy is fixed_price';
COMMENT ON COLUMN coins.paid_price IS 'Price paid for the coin (used as base for paid_price_multiplier)';
COMMENT ON COLUMN coins.entry_spot IS 'Spot price at time of purchase (used for entry_based pricing)';
COMMENT ON COLUMN coins.entry_melt IS 'Melt value at time of purchase (used for entry_based pricing)';
