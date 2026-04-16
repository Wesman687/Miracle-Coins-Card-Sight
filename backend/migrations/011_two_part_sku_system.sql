-- Two-Part SKU System Migration
-- Format: [PREFIX]-[SEQUENCE] (e.g., ASE-001, MOR-002)

-- 1. Create SKU Prefixes Table
CREATE TABLE IF NOT EXISTS sku_prefixes (
    id SERIAL PRIMARY KEY,
    prefix VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    auto_increment BOOLEAN DEFAULT TRUE,
    current_sequence INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create SKU Sequences Table for tracking
CREATE TABLE IF NOT EXISTS sku_sequences (
    id SERIAL PRIMARY KEY,
    prefix VARCHAR(20) REFERENCES sku_prefixes(prefix) NOT NULL,
    sequence_number INTEGER NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    coin_id INTEGER REFERENCES coins(id),
    UNIQUE(prefix, sequence_number)
);

-- 3. Add new SKU columns to coins table
ALTER TABLE coins ADD COLUMN IF NOT EXISTS sku_prefix VARCHAR(20);
ALTER TABLE coins ADD COLUMN IF NOT EXISTS sku_sequence INTEGER;

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_coins_sku_prefix ON coins(sku_prefix);
CREATE INDEX IF NOT EXISTS idx_coins_sku_sequence ON coins(sku_sequence);
CREATE INDEX IF NOT EXISTS idx_sku_prefixes_prefix ON sku_prefixes(prefix);
CREATE INDEX IF NOT EXISTS idx_sku_sequences_prefix ON sku_sequences(prefix);

-- 5. Insert default prefixes based on existing coin categories
INSERT INTO sku_prefixes (prefix, description, auto_increment, current_sequence) VALUES
('ASE', 'American Silver Eagles', TRUE, 0),
('MOR', 'Morgan Dollars', TRUE, 0),
('PEA', 'Peace Dollars', TRUE, 0),
('KEN', 'Kennedy Half Dollars', TRUE, 0),
('WAL', 'Walking Liberty Half Dollars', TRUE, 0),
('MER', 'Mercury Dimes', TRUE, 0),
('ROO', 'Roosevelt Dimes', TRUE, 0),
('WAS', 'Washington Quarters', TRUE, 0),
('STA', 'Standing Liberty Quarters', TRUE, 0),
('BAR', 'Barber Coins', TRUE, 0),
('LIB', 'Liberty Head Coins', TRUE, 0),
('BUF', 'Buffalo Nickels', TRUE, 0),
('IND', 'Indian Head Coins', TRUE, 0),
('GLD', 'Gold Coins', TRUE, 0),
('GEN', 'General Coins', TRUE, 0)
ON CONFLICT (prefix) DO NOTHING;

-- 6. Create function to generate next SKU
CREATE OR REPLACE FUNCTION generate_next_sku(p_prefix VARCHAR(20)) 
RETURNS VARCHAR(50) AS $$
DECLARE
    next_sequence INTEGER;
    new_sku VARCHAR(50);
BEGIN
    -- Get next sequence number
    SELECT COALESCE(current_sequence, 0) + 1 INTO next_sequence
    FROM sku_prefixes 
    WHERE prefix = p_prefix;
    
    -- Update the current sequence
    UPDATE sku_prefixes 
    SET current_sequence = next_sequence,
        updated_at = CURRENT_TIMESTAMP
    WHERE prefix = p_prefix;
    
    -- Build the SKU
    new_sku := p_prefix || '-' || LPAD(next_sequence::text, 3, '0');
    
    RETURN new_sku;
END;
$$ LANGUAGE plpgsql;

-- 7. Create function to get next sequence for bulk operations
CREATE OR REPLACE FUNCTION get_next_sequence_range(p_prefix VARCHAR(20), p_count INTEGER) 
RETURNS TABLE(start_seq INTEGER, end_seq INTEGER) AS $$
DECLARE
    current_seq INTEGER;
BEGIN
    -- Get current sequence
    SELECT COALESCE(current_sequence, 0) INTO current_seq
    FROM sku_prefixes 
    WHERE prefix = p_prefix;
    
    -- Update the current sequence
    UPDATE sku_prefixes 
    SET current_sequence = current_seq + p_count,
        updated_at = CURRENT_TIMESTAMP
    WHERE prefix = p_prefix;
    
    -- Return range
    RETURN QUERY SELECT current_seq + 1, current_seq + p_count;
END;
$$ LANGUAGE plpgsql;

-- 8. Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_sku_prefixes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_sku_prefixes_updated_at
    BEFORE UPDATE ON sku_prefixes
    FOR EACH ROW
    EXECUTE FUNCTION update_sku_prefixes_updated_at();

-- 9. Add constraints
ALTER TABLE sku_prefixes ADD CONSTRAINT check_prefix_length CHECK (LENGTH(prefix) >= 2 AND LENGTH(prefix) <= 20);
ALTER TABLE sku_prefixes ADD CONSTRAINT check_sequence_positive CHECK (current_sequence >= 0);
ALTER TABLE sku_sequences ADD CONSTRAINT check_sequence_positive CHECK (sequence_number > 0);

-- 10. Add comments for documentation
COMMENT ON TABLE sku_prefixes IS 'SKU prefix management for two-part SKU system';
COMMENT ON TABLE sku_sequences IS 'SKU sequence tracking for audit and management';
COMMENT ON COLUMN coins.sku_prefix IS 'SKU prefix (e.g., ASE, MOR)';
COMMENT ON COLUMN coins.sku_sequence IS 'SKU sequence number (e.g., 001, 002)';

-- Success message
SELECT 'Two-Part SKU System schema created successfully!' as status;
