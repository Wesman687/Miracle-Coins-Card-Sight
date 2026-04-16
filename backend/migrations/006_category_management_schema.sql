-- Category Management Schema Migration
-- This migration adds comprehensive category management for coins and Shopify integration

-- Create enum types for category management
CREATE TYPE category_type_enum AS ENUM (
    'silver_coins',
    'gold_coins', 
    'collector_coins',
    'bullion',
    'proof_coins',
    'error_coins',
    'ancient_coins',
    'world_coins',
    'us_coins',
    'commemorative',
    'custom'
);

CREATE TYPE category_status_enum AS ENUM (
    'active',
    'inactive',
    'archived'
);

CREATE TYPE field_type_enum AS ENUM (
    'text',
    'number',
    'boolean',
    'select',
    'date'
);

-- Shopify Categories Table
CREATE TABLE shopify_categories (
    id SERIAL PRIMARY KEY,
    shopify_collection_id VARCHAR(100) UNIQUE NOT NULL,
    shopify_collection_handle VARCHAR(200) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    shopify_product_type VARCHAR(100),
    shopify_tags JSONB DEFAULT '[]'::jsonb,
    shopify_metafields JSONB DEFAULT '{}'::jsonb,
    parent_category_id INTEGER REFERENCES shopify_categories(id),
    sort_order INTEGER DEFAULT 0,
    status category_status_enum DEFAULT 'active',
    is_auto_created BOOLEAN DEFAULT FALSE,
    coin_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE
);

-- Coin Categories Table
CREATE TABLE coin_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    category_type category_type_enum NOT NULL,
    parent_category_id INTEGER REFERENCES coin_categories(id),
    
    -- Metadata for automatic categorization
    keywords JSONB DEFAULT '[]'::jsonb,
    denomination_patterns JSONB DEFAULT '[]'::jsonb,
    year_ranges JSONB DEFAULT '[]'::jsonb,
    mint_mark_patterns JSONB DEFAULT '[]'::jsonb,
    grade_patterns JSONB DEFAULT '[]'::jsonb,
    
    -- Pricing and business rules
    default_price_multiplier NUMERIC(6,3) DEFAULT 1.300 CHECK (default_price_multiplier >= 0.1 AND default_price_multiplier <= 10.0),
    min_price_multiplier NUMERIC(6,3) DEFAULT 1.200 CHECK (min_price_multiplier >= 0.1 AND min_price_multiplier <= 10.0),
    max_price_multiplier NUMERIC(6,3) DEFAULT 2.000 CHECK (max_price_multiplier >= 0.1 AND max_price_multiplier <= 10.0),
    
    -- Silver/gold content rules
    is_precious_metal BOOLEAN DEFAULT TRUE,
    metal_type VARCHAR(20),
    expected_silver_content NUMERIC(7,4) CHECK (expected_silver_content >= 0 AND expected_silver_content <= 100),
    
    -- Shopify integration
    shopify_category_id INTEGER REFERENCES shopify_categories(id),
    auto_sync_to_shopify BOOLEAN DEFAULT TRUE,
    
    -- Display and organization
    sort_order INTEGER DEFAULT 0,
    status category_status_enum DEFAULT 'active',
    icon VARCHAR(100),
    color VARCHAR(20),
    
    -- Statistics
    coin_count INTEGER DEFAULT 0,
    total_value NUMERIC(12,2) DEFAULT 0,
    avg_price NUMERIC(10,2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Category Metadata Table
CREATE TABLE category_metadata (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES coin_categories(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_type field_type_enum NOT NULL,
    field_label VARCHAR(200) NOT NULL,
    field_description TEXT,
    is_required BOOLEAN DEFAULT FALSE,
    default_value VARCHAR(500),
    validation_rules JSONB DEFAULT '{}'::jsonb,
    select_options JSONB DEFAULT '[]'::jsonb,
    sort_order INTEGER DEFAULT 0,
    is_searchable BOOLEAN DEFAULT TRUE,
    is_filterable BOOLEAN DEFAULT TRUE,
    is_display_in_list BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Category Rules Table
CREATE TABLE category_rules (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES coin_categories(id) ON DELETE CASCADE,
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT,
    conditions JSONB NOT NULL,
    priority INTEGER DEFAULT 100 CHECK (priority >= 1 AND priority <= 1000),
    is_active BOOLEAN DEFAULT TRUE,
    match_count INTEGER DEFAULT 0,
    last_matched_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add category_id foreign key to coins table
ALTER TABLE coins ADD COLUMN category_id INTEGER REFERENCES coin_categories(id);

-- Create indexes for better performance
CREATE INDEX idx_coin_categories_type ON coin_categories(category_type);
CREATE INDEX idx_coin_categories_status ON coin_categories(status);
CREATE INDEX idx_coin_categories_parent ON coin_categories(parent_category_id);
CREATE INDEX idx_coin_categories_shopify ON coin_categories(shopify_category_id);
CREATE INDEX idx_coin_categories_keywords ON coin_categories USING GIN(keywords);

CREATE INDEX idx_shopify_categories_status ON shopify_categories(status);
CREATE INDEX idx_shopify_categories_parent ON shopify_categories(parent_category_id);
CREATE INDEX idx_shopify_categories_tags ON shopify_categories USING GIN(shopify_tags);

CREATE INDEX idx_category_metadata_category ON category_metadata(category_id);
CREATE INDEX idx_category_metadata_type ON category_metadata(field_type);

CREATE INDEX idx_category_rules_category ON category_rules(category_id);
CREATE INDEX idx_category_rules_active ON category_rules(is_active);
CREATE INDEX idx_category_rules_priority ON category_rules(priority);

CREATE INDEX idx_coins_category ON coins(category_id);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_shopify_categories_updated_at 
    BEFORE UPDATE ON shopify_categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_coin_categories_updated_at 
    BEFORE UPDATE ON coin_categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_category_metadata_updated_at 
    BEFORE UPDATE ON category_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_category_rules_updated_at 
    BEFORE UPDATE ON category_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default coin categories
INSERT INTO coin_categories (name, display_name, description, category_type, keywords, default_price_multiplier, is_precious_metal, metal_type, sort_order) VALUES
('silver_eagles', 'Silver Eagles', 'American Silver Eagle coins', 'silver_coins', '["silver eagle", "eagle", "ase"]', 1.35, TRUE, 'silver', 1),
('morgan_dollars', 'Morgan Dollars', 'Morgan Silver Dollars (1878-1921)', 'silver_coins', '["morgan", "morgan dollar", "peace dollar"]', 1.40, TRUE, 'silver', 2),
('walking_liberty', 'Walking Liberty Half Dollars', 'Walking Liberty Half Dollars', 'silver_coins', '["walking liberty", "liberty half"]', 1.35, TRUE, 'silver', 3),
('kennedy_half_dollars', 'Kennedy Half Dollars', 'Kennedy Half Dollars (1964-present)', 'silver_coins', '["kennedy", "kennedy half", "half dollar"]', 1.30, TRUE, 'silver', 4),
('quarters', 'Silver Quarters', 'Silver quarters including Washington, Standing Liberty', 'silver_coins', '["quarter", "silver quarter", "washington quarter"]', 1.25, TRUE, 'silver', 5),
('dimes', 'Silver Dimes', 'Silver dimes including Mercury and Roosevelt', 'silver_coins', '["dime", "silver dime", "mercury dime", "roosevelt dime"]', 1.25, TRUE, 'silver', 6),
('gold_coins', 'Gold Coins', 'Various gold coins and bullion', 'gold_coins', '["gold", "gold coin", "gold bullion"]', 1.50, TRUE, 'gold', 10),
('proof_coins', 'Proof Coins', 'Proof and special finish coins', 'proof_coins', '["proof", "proof coin", "special finish"]', 1.60, TRUE, 'silver', 20),
('error_coins', 'Error Coins', 'Coins with minting errors', 'error_coins', '["error", "error coin", "mint error"]', 2.00, FALSE, NULL, 30),
('world_coins', 'World Coins', 'International coins', 'world_coins', '["world", "international", "foreign"]', 1.30, FALSE, NULL, 40);

-- Insert default category metadata for Silver Eagles
INSERT INTO category_metadata (category_id, field_name, field_type, field_label, field_description, is_required, sort_order) 
SELECT 
    cc.id,
    'year',
    'number',
    'Year',
    'Year the coin was minted',
    TRUE,
    1
FROM coin_categories cc WHERE cc.name = 'silver_eagles';

INSERT INTO category_metadata (category_id, field_name, field_type, field_label, field_description, is_required, sort_order) 
SELECT 
    cc.id,
    'mint_mark',
    'select',
    'Mint Mark',
    'Mint mark on the coin',
    FALSE,
    2
FROM coin_categories cc WHERE cc.name = 'silver_eagles';

INSERT INTO category_metadata (category_id, field_name, field_type, field_label, field_description, is_required, sort_order, select_options) 
SELECT 
    cc.id,
    'condition',
    'select',
    'Condition',
    'Physical condition of the coin',
    TRUE,
    3,
    '["BU", "AU", "XF", "VF", "F", "VG", "G", "AG", "FA"]'::jsonb
FROM coin_categories cc WHERE cc.name = 'silver_eagles';

-- Insert default category metadata for Morgan Dollars
INSERT INTO category_metadata (category_id, field_name, field_type, field_label, field_description, is_required, sort_order) 
SELECT 
    cc.id,
    'year',
    'number',
    'Year',
    'Year the Morgan Dollar was minted (1878-1921)',
    TRUE,
    1
FROM coin_categories cc WHERE cc.name = 'morgan_dollars';

INSERT INTO category_metadata (category_id, field_name, field_type, field_label, field_description, is_required, sort_order, select_options) 
SELECT 
    cc.id,
    'mint_mark',
    'select',
    'Mint Mark',
    'Mint mark on the Morgan Dollar',
    FALSE,
    2,
    '["CC", "S", "O", "D", "No Mark"]'::jsonb
FROM coin_categories cc WHERE cc.name = 'morgan_dollars';

INSERT INTO category_metadata (category_id, field_name, field_type, field_label, field_description, is_required, sort_order, select_options) 
SELECT 
    cc.id,
    'grade',
    'select',
    'Grade',
    'PCGS or NGC grade',
    FALSE,
    3,
    '["MS70", "MS69", "MS68", "MS67", "MS66", "MS65", "MS64", "MS63", "MS62", "MS61", "MS60", "AU58", "AU55", "AU53", "XF45", "XF40", "VF35", "VF30", "VF25", "VF20", "F15", "F12", "VG10", "VG8", "G6", "G4", "AG3", "FA2", "PO1"]'::jsonb
FROM coin_categories cc WHERE cc.name = 'morgan_dollars';

-- Insert sample categorization rules
INSERT INTO category_rules (category_id, rule_name, rule_description, conditions, priority) 
SELECT 
    cc.id,
    'Silver Eagle Auto-Categorization',
    'Automatically categorize coins with silver eagle keywords',
    '{"keywords": ["silver eagle", "ase"], "required_matches": 1}'::jsonb,
    100
FROM coin_categories cc WHERE cc.name = 'silver_eagles';

INSERT INTO category_rules (category_id, rule_name, rule_description, conditions, priority) 
SELECT 
    cc.id,
    'Morgan Dollar Auto-Categorization',
    'Automatically categorize Morgan and Peace dollars',
    '{"keywords": ["morgan", "peace dollar"], "year_range": {"min": 1878, "max": 1935}, "required_matches": 2}'::jsonb,
    100
FROM coin_categories cc WHERE cc.name = 'morgan_dollars';

-- Create a function to update category statistics
CREATE OR REPLACE FUNCTION update_category_statistics(category_id INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE coin_categories 
    SET 
        coin_count = (SELECT COUNT(*) FROM coins WHERE coins.category_id = category_id),
        total_value = (SELECT COALESCE(SUM(computed_price * quantity), 0) FROM coins WHERE coins.category_id = category_id),
        avg_price = (SELECT COALESCE(AVG(computed_price), 0) FROM coins WHERE coins.category_id = category_id),
        updated_at = NOW()
    WHERE id = category_id;
END;
$$ LANGUAGE plpgsql;

-- Create a function to auto-categorize coins
CREATE OR REPLACE FUNCTION auto_categorize_coin(coin_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    best_category_id INTEGER;
    coin_record RECORD;
    category_record RECORD;
    match_score FLOAT;
    best_score FLOAT := 0;
BEGIN
    -- Get coin details
    SELECT * INTO coin_record FROM coins WHERE id = coin_id;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- Check each active category
    FOR category_record IN 
        SELECT * FROM coin_categories WHERE status = 'active'
    LOOP
        match_score := 0;
        
        -- Check keywords match
        IF category_record.keywords IS NOT NULL THEN
            SELECT COUNT(*) INTO match_score
            FROM jsonb_array_elements_text(category_record.keywords) AS keyword
            WHERE LOWER(coin_record.title || ' ' || COALESCE(coin_record.description, '')) LIKE '%' || LOWER(keyword) || '%';
            
            IF match_score > 0 THEN
                match_score := match_score / jsonb_array_length(category_record.keywords);
            END IF;
        END IF;
        
        -- If this is the best match so far, remember it
        IF match_score > best_score THEN
            best_score := match_score;
            best_category_id := category_record.id;
        END IF;
    END LOOP;
    
    -- If we found a good match (score > 0.3), apply it
    IF best_score > 0.3 THEN
        UPDATE coins SET category_id = best_category_id WHERE id = coin_id;
        RETURN best_category_id;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create a view for category analytics
CREATE VIEW category_analytics AS
SELECT 
    cc.id,
    cc.name,
    cc.display_name,
    cc.category_type,
    cc.coin_count,
    cc.total_value,
    cc.avg_price,
    cc.default_price_multiplier,
    sc.name as shopify_category_name,
    sc.shopify_collection_handle,
    COUNT(cr.id) as rule_count,
    cc.created_at,
    cc.updated_at
FROM coin_categories cc
LEFT JOIN shopify_categories sc ON cc.shopify_category_id = sc.id
LEFT JOIN category_rules cr ON cc.id = cr.category_id
GROUP BY cc.id, sc.name, sc.shopify_collection_handle
ORDER BY cc.sort_order, cc.name;

-- Add comments for documentation
COMMENT ON TABLE coin_categories IS 'Structured coin categories with rich metadata for automatic categorization';
COMMENT ON TABLE shopify_categories IS 'Shopify collection mappings for coin categories';
COMMENT ON TABLE category_metadata IS 'Rich metadata field definitions for each category';
COMMENT ON TABLE category_rules IS 'Automated categorization rules based on coin properties';
COMMENT ON FUNCTION auto_categorize_coin(INTEGER) IS 'Automatically categorize a coin based on its properties and category rules';
COMMENT ON FUNCTION update_category_statistics(INTEGER) IS 'Update statistics for a specific category';
COMMENT ON VIEW category_analytics IS 'Analytics view combining category data with Shopify and rule information';
