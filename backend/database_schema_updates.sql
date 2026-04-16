-- Miracle Coins CoinSync Pro - Database Schema Updates
-- Run this script in your PostgreSQL database to add the new features

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Add SKU field to coins table if it doesn't exist
ALTER TABLE coins ADD COLUMN IF NOT EXISTS sku VARCHAR(100) UNIQUE;

-- Create index on SKU for faster lookups
CREATE INDEX IF NOT EXISTS idx_coins_sku ON coins(sku);

-- 2. Create coin_categories table
CREATE TABLE IF NOT EXISTS coin_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    category_type VARCHAR(50) DEFAULT 'US_COINS',
    status VARCHAR(20) DEFAULT 'ACTIVE',
    parent_id INTEGER REFERENCES coin_categories(id),
    shopify_category_id INTEGER,
    auto_sync_to_shopify BOOLEAN DEFAULT FALSE,
    is_auto_created BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_coins INTEGER DEFAULT 0,
    total_value DECIMAL(12, 2) DEFAULT 0.00,
    avg_price DECIMAL(10, 2) DEFAULT 0.00,
    last_stats_update TIMESTAMP WITH TIME ZONE
);

-- 3. Create shopify_categories table
CREATE TABLE IF NOT EXISTS shopify_categories (
    id SERIAL PRIMARY KEY,
    shopify_collection_id VARCHAR(100) UNIQUE NOT NULL,
    shopify_collection_handle VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    shopify_tags JSONB,
    shopify_metafields JSONB,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    is_auto_created BOOLEAN DEFAULT FALSE,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create category_metadata table
CREATE TABLE IF NOT EXISTS category_metadata (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES coin_categories(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    field_type VARCHAR(20) DEFAULT 'TEXT',
    is_required BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    options JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create category_rules table
CREATE TABLE IF NOT EXISTS category_rules (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES coin_categories(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL,
    rule_value TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Create coin_metadata table
CREATE TABLE IF NOT EXISTS coin_metadata (
    id SERIAL PRIMARY KEY,
    coin_id INTEGER NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_coin_categories_name ON coin_categories(name);
CREATE INDEX IF NOT EXISTS idx_coin_categories_type ON coin_categories(category_type);
CREATE INDEX IF NOT EXISTS idx_coin_categories_status ON coin_categories(status);
CREATE INDEX IF NOT EXISTS idx_shopify_categories_collection_id ON shopify_categories(shopify_collection_id);
CREATE INDEX IF NOT EXISTS idx_category_metadata_category_id ON category_metadata(category_id);
CREATE INDEX IF NOT EXISTS idx_category_rules_category_id ON category_rules(category_id);
CREATE INDEX IF NOT EXISTS idx_coin_metadata_coin_id ON coin_metadata(coin_id);

-- 7. Insert default coin categories
INSERT INTO coin_categories (name, display_name, description, category_type, status) VALUES
('silver_eagles', 'Silver Eagles', 'American Silver Eagle bullion coins', 'SILVER_COINS', 'ACTIVE'),
('morgan_dollars', 'Morgan Silver Dollars', 'Morgan silver dollars from 1878-1921', 'US_COINS', 'ACTIVE'),
('peace_dollars', 'Peace Silver Dollars', 'Peace silver dollars from 1921-1935', 'US_COINS', 'ACTIVE'),
('kennedy_halves', 'Kennedy Half Dollars', 'Kennedy half dollars (1964-present)', 'US_COINS', 'ACTIVE'),
('walking_liberty_halves', 'Walking Liberty Half Dollars', 'Walking Liberty half dollars (1916-1947)', 'US_COINS', 'ACTIVE'),
('mercury_dimes', 'Mercury Dimes', 'Mercury dimes (1916-1945)', 'US_COINS', 'ACTIVE'),
('roosevelt_dimes', 'Roosevelt Dimes', 'Roosevelt dimes (1946-present)', 'US_COINS', 'ACTIVE'),
('washington_quarters', 'Washington Quarters', 'Washington quarters (1932-present)', 'US_COINS', 'ACTIVE'),
('standing_liberty_quarters', 'Standing Liberty Quarters', 'Standing Liberty quarters (1916-1930)', 'US_COINS', 'ACTIVE'),
('barber_coins', 'Barber Coins', 'Barber dimes, quarters, and half dollars (1892-1916)', 'US_COINS', 'ACTIVE')
ON CONFLICT (name) DO NOTHING;

-- 8. Insert sample metadata fields for Silver Eagles category
INSERT INTO category_metadata (category_id, field_name, display_name, field_type, is_required, description) VALUES
((SELECT id FROM coin_categories WHERE name = 'silver_eagles'), 'mint_year', 'Mint Year', 'NUMBER', TRUE, 'Year the coin was minted'),
((SELECT id FROM coin_categories WHERE name = 'silver_eagles'), 'mint_location', 'Mint Location', 'SELECT', TRUE, 'Mint facility where coin was produced'),
((SELECT id FROM coin_categories WHERE name = 'silver_eagles'), 'grade', 'Grade', 'SELECT', TRUE, 'Coin grade (MS70, MS69, etc.)'),
((SELECT id FROM coin_categories WHERE name = 'silver_eagles'), 'certification', 'Certification', 'SELECT', FALSE, 'Grading service certification')
ON CONFLICT DO NOTHING;

-- 9. Insert sample metadata fields for Morgan Dollars category
INSERT INTO category_metadata (category_id, field_name, display_name, field_type, is_required, description) VALUES
((SELECT id FROM coin_categories WHERE name = 'morgan_dollars'), 'mint_year', 'Mint Year', 'NUMBER', TRUE, 'Year the coin was minted'),
((SELECT id FROM coin_categories WHERE name = 'morgan_dollars'), 'mint_mark', 'Mint Mark', 'SELECT', TRUE, 'Mint mark on the coin'),
((SELECT id FROM coin_categories WHERE name = 'morgan_dollars'), 'grade', 'Grade', 'SELECT', TRUE, 'Coin grade'),
((SELECT id FROM coin_categories WHERE name = 'morgan_dollars'), 'variety', 'Variety', 'TEXT', FALSE, 'Coin variety or type')
ON CONFLICT DO NOTHING;

-- 10. Insert sample rules for auto-categorization
INSERT INTO category_rules (category_id, rule_type, rule_value, priority, is_active) VALUES
((SELECT id FROM coin_categories WHERE name = 'silver_eagles'), 'keyword', 'silver eagle', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'morgan_dollars'), 'keyword', 'morgan', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'morgan_dollars'), 'keyword', 'morgan dollar', 15, TRUE),
((SELECT id FROM coin_categories WHERE name = 'peace_dollars'), 'keyword', 'peace', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'kennedy_halves'), 'keyword', 'kennedy', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'walking_liberty_halves'), 'keyword', 'walking liberty', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'mercury_dimes'), 'keyword', 'mercury', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'roosevelt_dimes'), 'keyword', 'roosevelt', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'washington_quarters'), 'keyword', 'washington', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'standing_liberty_quarters'), 'keyword', 'standing liberty', 10, TRUE),
((SELECT id FROM coin_categories WHERE name = 'barber_coins'), 'keyword', 'barber', 10, TRUE)
ON CONFLICT DO NOTHING;

-- 11. Function to generate SKU for a coin
CREATE OR REPLACE FUNCTION generate_coin_sku(
    p_title TEXT,
    p_year INTEGER,
    p_denomination TEXT,
    p_mint_mark TEXT,
    p_grade TEXT,
    p_category_name TEXT DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    category_prefix TEXT;
    year_str TEXT;
    denomination_str TEXT;
    mint_str TEXT;
    grade_str TEXT;
    sequence_num INTEGER;
    base_sku TEXT;
    final_sku TEXT;
BEGIN
    -- Determine category prefix
    IF p_category_name IS NOT NULL THEN
        category_prefix := CASE 
            WHEN LOWER(p_category_name) LIKE '%silver eagle%' THEN 'ASE'
            WHEN LOWER(p_category_name) LIKE '%morgan%' THEN 'MOR'
            WHEN LOWER(p_category_name) LIKE '%peace%' THEN 'PEA'
            WHEN LOWER(p_category_name) LIKE '%kennedy%' THEN 'KEN'
            WHEN LOWER(p_category_name) LIKE '%walking liberty%' THEN 'WAL'
            WHEN LOWER(p_category_name) LIKE '%mercury%' THEN 'MER'
            WHEN LOWER(p_category_name) LIKE '%roosevelt%' THEN 'ROO'
            WHEN LOWER(p_category_name) LIKE '%washington%' THEN 'WAS'
            WHEN LOWER(p_category_name) LIKE '%standing liberty%' THEN 'STA'
            WHEN LOWER(p_category_name) LIKE '%barber%' THEN 'BAR'
            WHEN LOWER(p_category_name) LIKE '%liberty head%' THEN 'LIB'
            WHEN LOWER(p_category_name) LIKE '%buffalo%' THEN 'BUF'
            WHEN LOWER(p_category_name) LIKE '%indian head%' THEN 'IND'
            WHEN LOWER(p_category_name) LIKE '%gold%' THEN 'GLD'
            ELSE UPPER(LEFT(p_category_name, 3))
        END;
    ELSE
        category_prefix := CASE 
            WHEN LOWER(p_title) LIKE '%silver eagle%' THEN 'ASE'
            WHEN LOWER(p_title) LIKE '%morgan%' THEN 'MOR'
            WHEN LOWER(p_title) LIKE '%peace%' THEN 'PEA'
            WHEN LOWER(p_title) LIKE '%kennedy%' THEN 'KEN'
            WHEN LOWER(p_title) LIKE '%walking liberty%' THEN 'WAL'
            WHEN LOWER(p_title) LIKE '%mercury%' THEN 'MER'
            WHEN LOWER(p_title) LIKE '%roosevelt%' THEN 'ROO'
            WHEN LOWER(p_title) LIKE '%washington%' THEN 'WAS'
            WHEN LOWER(p_title) LIKE '%standing liberty%' THEN 'STA'
            WHEN LOWER(p_title) LIKE '%barber%' THEN 'BAR'
            WHEN LOWER(p_title) LIKE '%liberty head%' THEN 'LIB'
            WHEN LOWER(p_title) LIKE '%buffalo%' THEN 'BUF'
            WHEN LOWER(p_title) LIKE '%indian head%' THEN 'IND'
            WHEN LOWER(p_title) LIKE '%gold%' THEN 'GLD'
            ELSE UPPER(LEFT(p_title, 3))
        END;
    END IF;
    
    -- Format other components
    year_str := COALESCE(p_year::text, '0000');
    
    denomination_str := CASE 
        WHEN LOWER(p_denomination) LIKE '%dollar%' OR LOWER(p_denomination) LIKE '%$1%' THEN '1DOL'
        WHEN LOWER(p_denomination) LIKE '%half%' OR LOWER(p_denomination) LIKE '%50%' THEN '50C'
        WHEN LOWER(p_denomination) LIKE '%quarter%' OR LOWER(p_denomination) LIKE '%25%' THEN '25C'
        WHEN LOWER(p_denomination) LIKE '%dime%' OR LOWER(p_denomination) LIKE '%10%' THEN '10C'
        WHEN LOWER(p_denomination) LIKE '%nickel%' OR LOWER(p_denomination) LIKE '%5%' THEN '5C'
        WHEN LOWER(p_denomination) LIKE '%penny%' OR LOWER(p_denomination) LIKE '%cent%' OR LOWER(p_denomination) LIKE '%1%' THEN '1C'
        WHEN LOWER(p_denomination) LIKE '%ounce%' OR LOWER(p_denomination) LIKE '%oz%' THEN '1OZ'
        WHEN LOWER(p_denomination) LIKE '%gram%' OR LOWER(p_denomination) LIKE '%g%' THEN '1G'
        ELSE '1OZ'
    END;
    
    mint_str := CASE 
        WHEN p_mint_mark IS NULL OR p_mint_mark = '' OR LOWER(p_mint_mark) LIKE '%no mark%' OR LOWER(p_mint_mark) LIKE '%philadelphia%' THEN 'NM'
        WHEN LOWER(p_mint_mark) LIKE '%denver%' OR UPPER(p_mint_mark) = 'D' THEN 'D'
        WHEN LOWER(p_mint_mark) LIKE '%san francisco%' OR UPPER(p_mint_mark) = 'S' THEN 'S'
        WHEN LOWER(p_mint_mark) LIKE '%carson city%' OR UPPER(p_mint_mark) = 'CC' THEN 'CC'
        WHEN LOWER(p_mint_mark) LIKE '%new orleans%' OR UPPER(p_mint_mark) = 'O' THEN 'O'
        WHEN LOWER(p_mint_mark) LIKE '%west point%' OR UPPER(p_mint_mark) = 'W' THEN 'W'
        ELSE UPPER(LEFT(p_mint_mark, 2))
    END;
    
    grade_str := CASE 
        WHEN p_grade IS NULL OR p_grade = '' THEN 'UNG'
        WHEN UPPER(p_grade) LIKE 'MS%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'AU%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'XF%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'VF%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'F%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'VG%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'G%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'AG%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'FA%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE 'PO%' THEN UPPER(p_grade)
        WHEN UPPER(p_grade) LIKE '%UNCIRCULATED%' OR UPPER(p_grade) LIKE '%UNC%' THEN 'UNC'
        WHEN UPPER(p_grade) LIKE '%BRILLIANT UNCIRCULATED%' OR UPPER(p_grade) LIKE '%BU%' THEN 'BU'
        WHEN UPPER(p_grade) LIKE '%PROOF%' OR UPPER(p_grade) LIKE '%PRF%' THEN 'PRF'
        WHEN UPPER(p_grade) LIKE '%CIRCULATED%' OR UPPER(p_grade) LIKE '%CIR%' THEN 'CIR'
        ELSE UPPER(LEFT(p_grade, 4))
    END;
    
    -- Build base SKU
    base_sku := category_prefix || '-' || year_str || '-' || denomination_str || '-' || mint_str || '-' || grade_str;
    
    -- Find next sequence number
    SELECT COALESCE(MAX(CAST(SUBSTRING(sku FROM '[0-9]+$') AS INTEGER)), 0) + 1
    INTO sequence_num
    FROM coins 
    WHERE sku LIKE base_sku || '-%';
    
    -- Build final SKU
    final_sku := base_sku || '-' || LPAD(sequence_num::text, 3, '0');
    
    RETURN final_sku;
END;
$$ LANGUAGE plpgsql;

-- 12. Generate SKUs for existing coins
UPDATE coins 
SET sku = generate_coin_sku(
    title,
    year,
    denomination,
    mint_mark,
    grade,
    category
)
WHERE sku IS NULL OR sku = '';

-- Add comments for documentation
COMMENT ON TABLE coin_categories IS 'Coin categories for organization and management';
COMMENT ON TABLE shopify_categories IS 'Shopify collection mappings for category sync';
COMMENT ON TABLE category_metadata IS 'Metadata fields for each category';
COMMENT ON TABLE category_rules IS 'Rules for auto-categorization';
COMMENT ON TABLE coin_metadata IS 'Additional metadata for individual coins';
COMMENT ON COLUMN coins.sku IS 'Auto-generated unique SKU for each coin';

-- Success message
SELECT 'Database schema updates completed successfully!' as status;
