-- Migration 014: Collection Metadata and Images System
-- Add support for flexible metadata fields and image management for collections

-- Create collection_metadata table
CREATE TABLE IF NOT EXISTS collection_metadata (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_type VARCHAR(20) NOT NULL CHECK (field_type IN ('text', 'textarea', 'number', 'date', 'boolean', 'select')),
    field_value TEXT,
    field_options JSONB,
    field_label VARCHAR(200),
    field_description TEXT,
    is_required BOOLEAN DEFAULT FALSE,
    is_searchable BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT unique_collection_field_name UNIQUE (collection_id, field_name)
);

-- Create indexes for collection_metadata
CREATE INDEX IF NOT EXISTS idx_collection_metadata_collection_id ON collection_metadata(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_metadata_field_name ON collection_metadata(field_name);
CREATE INDEX IF NOT EXISTS idx_collection_metadata_field_type ON collection_metadata(field_type);
CREATE INDEX IF NOT EXISTS idx_collection_metadata_searchable ON collection_metadata(is_searchable) WHERE is_searchable = TRUE;

-- Create collection_images table
CREATE TABLE IF NOT EXISTS collection_images (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(200),
    caption TEXT,
    is_featured BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT unique_collection_featured_image EXCLUDE (collection_id WITH =) WHERE (is_featured = TRUE)
);

-- Create indexes for collection_images
CREATE INDEX IF NOT EXISTS idx_collection_images_collection_id ON collection_images(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_images_featured ON collection_images(is_featured) WHERE is_featured = TRUE;
CREATE INDEX IF NOT EXISTS idx_collection_images_sort_order ON collection_images(collection_id, sort_order);

-- Add description_html column to collections table for rich text support
ALTER TABLE collections ADD COLUMN IF NOT EXISTS description_html TEXT;

-- Create trigger to update updated_at timestamp for collection_metadata
CREATE OR REPLACE FUNCTION update_collection_metadata_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_collection_metadata_updated_at
    BEFORE UPDATE ON collection_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_collection_metadata_updated_at();

-- Create trigger to update updated_at timestamp for collection_images
CREATE OR REPLACE FUNCTION update_collection_images_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_collection_images_updated_at
    BEFORE UPDATE ON collection_images
    FOR EACH ROW
    EXECUTE FUNCTION update_collection_images_updated_at();

-- Insert some sample metadata fields for existing collections
INSERT INTO collection_metadata (collection_id, field_name, field_type, field_label, field_description, is_required, sort_order)
SELECT 
    c.id,
    'year_range',
    'text',
    'Year Range',
    'The range of years for coins in this collection',
    FALSE,
    1
FROM collections c
WHERE NOT EXISTS (
    SELECT 1 FROM collection_metadata cm 
    WHERE cm.collection_id = c.id AND cm.field_name = 'year_range'
);

INSERT INTO collection_metadata (collection_id, field_name, field_type, field_label, field_description, is_required, sort_order)
SELECT 
    c.id,
    'metal_type',
    'select',
    'Metal Type',
    'Primary metal type for this collection',
    TRUE,
    2
FROM collections c
WHERE NOT EXISTS (
    SELECT 1 FROM collection_metadata cm 
    WHERE cm.collection_id = c.id AND cm.field_name = 'metal_type'
);

-- Update the metal_type field with options
UPDATE collection_metadata 
SET field_options = '["Silver", "Gold", "Copper", "Nickel", "Mixed"]'::jsonb
WHERE field_name = 'metal_type';

INSERT INTO collection_metadata (collection_id, field_name, field_type, field_label, field_description, is_required, sort_order)
SELECT 
    c.id,
    'condition_grade',
    'select',
    'Condition Grade',
    'Typical condition grade for coins in this collection',
    FALSE,
    3
FROM collections c
WHERE NOT EXISTS (
    SELECT 1 FROM collection_metadata cm 
    WHERE cm.collection_id = c.id AND cm.field_name = 'condition_grade'
);

-- Update the condition_grade field with options
UPDATE collection_metadata 
SET field_options = '["Poor", "Fair", "Good", "Very Good", "Fine", "Very Fine", "Extremely Fine", "About Uncirculated", "Uncirculated", "Proof"]'::jsonb
WHERE field_name = 'condition_grade';

INSERT INTO collection_metadata (collection_id, field_name, field_type, field_label, field_description, is_required, sort_order)
SELECT 
    c.id,
    'rarity_level',
    'select',
    'Rarity Level',
    'Rarity level of coins in this collection',
    FALSE,
    4
FROM collections c
WHERE NOT EXISTS (
    SELECT 1 FROM collection_metadata cm 
    WHERE cm.collection_id = c.id AND cm.field_name = 'rarity_level'
);

-- Update the rarity_level field with options
UPDATE collection_metadata 
SET field_options = '["Common", "Uncommon", "Scarce", "Rare", "Very Rare", "Extremely Rare"]'::jsonb
WHERE field_name = 'rarity_level';

-- Add some sample values for existing collections
UPDATE collection_metadata 
SET field_value = 'Silver'
WHERE field_name = 'metal_type' AND collection_id IN (
    SELECT id FROM collections WHERE name ILIKE '%silver%'
);

UPDATE collection_metadata 
SET field_value = 'Gold'
WHERE field_name = 'metal_type' AND collection_id IN (
    SELECT id FROM collections WHERE name ILIKE '%gold%'
);

UPDATE collection_metadata 
SET field_value = 'Mixed'
WHERE field_name = 'metal_type' AND collection_id IN (
    SELECT id FROM collections WHERE name ILIKE '%mixed%' OR name ILIKE '%circulated%'
);

-- Create a view for collection metadata summary
CREATE OR REPLACE VIEW collection_metadata_summary AS
SELECT 
    c.id as collection_id,
    c.name as collection_name,
    COUNT(cm.id) as total_metadata_fields,
    COUNT(CASE WHEN cm.field_value IS NOT NULL AND cm.field_value != '' THEN 1 END) as fields_with_values,
    COUNT(CASE WHEN cm.is_required = TRUE THEN 1 END) as required_fields,
    COUNT(CASE WHEN cm.is_required = TRUE AND cm.field_value IS NOT NULL AND cm.field_value != '' THEN 1 END) as required_fields_completed,
    ROUND(
        COUNT(CASE WHEN cm.field_value IS NOT NULL AND cm.field_value != '' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(cm.id), 0), 2
    ) as completion_percentage
FROM collections c
LEFT JOIN collection_metadata cm ON c.id = cm.collection_id
GROUP BY c.id, c.name;

-- Create a view for collection images summary
CREATE OR REPLACE VIEW collection_images_summary AS
SELECT 
    c.id as collection_id,
    c.name as collection_name,
    COUNT(ci.id) as total_images,
    COUNT(CASE WHEN ci.is_featured = TRUE THEN 1 END) as featured_images,
    COALESCE(SUM(ci.file_size), 0) as total_size_bytes,
    COALESCE(AVG(ci.file_size), 0) as average_size_bytes,
    COALESCE(MAX(ci.uploaded_at), c.created_at) as last_image_upload
FROM collections c
LEFT JOIN collection_images ci ON c.id = ci.collection_id
GROUP BY c.id, c.name, c.created_at;

-- Add comments for documentation
COMMENT ON TABLE collection_metadata IS 'Flexible metadata fields for collections with support for different field types';
COMMENT ON TABLE collection_images IS 'Image management for collections with support for featured images and ordering';
COMMENT ON COLUMN collection_metadata.field_type IS 'Type of metadata field: text, textarea, number, date, boolean, select';
COMMENT ON COLUMN collection_metadata.field_options IS 'JSON array of options for select fields';
COMMENT ON COLUMN collection_images.is_featured IS 'Only one image per collection can be featured (enforced by unique constraint)';
COMMENT ON COLUMN collections.description_html IS 'Rich text description in HTML format';

-- Update migration log
INSERT INTO migration_log (migration_name, applied_at, description) 
VALUES (
    '014_collection_metadata_and_images', 
    CURRENT_TIMESTAMP, 
    'Added collection metadata system with flexible field types and image management with featured image support'
) ON CONFLICT (migration_name) DO NOTHING;

