-- Migration: Add Collections Table (Simplified)
-- Date: 2025-01-28
-- Description: Create collections table for coin organization (replaces categories/collections)

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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name);
CREATE INDEX IF NOT EXISTS idx_collections_sort ON collections(sort_order);
CREATE INDEX IF NOT EXISTS idx_collections_shopify ON collections(shopify_collection_id);
CREATE INDEX IF NOT EXISTS idx_coins_collection ON coins(collection_id);

-- Insert default collections
INSERT INTO collections (name, description, color, icon, shopify_collection_id, default_markup) VALUES
('Silver Bullion', 'General silver bullion products', '#C0C0C0', '💰', 'gid://shopify/Collection/12345', 1.150),
('Gold Bullion', 'General gold bullion products', '#FFD700', '👑', 'gid://shopify/Collection/67890', 1.080),
('Mercury Dimes', 'Classic Mercury Dime collection', '#A9A9A9', '🪙', 'gid://shopify/Collection/11223', 1.500),
('Morgan Dollars', 'Historic Morgan Silver Dollars', '#D3D3D3', '💵', 'gid://shopify/Collection/44556', 1.400),
('Kennedy Half Dollars', 'Kennedy Half Dollar collection', '#BEBEBE', '🥈', 'gid://shopify/Collection/77889', 1.350)
ON CONFLICT (name) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
