-- Coin Metadata Schema Migration
-- This migration adds dynamic metadata fields for coins based on their categories

-- Create coin_metadata table
CREATE TABLE coin_metadata (
    id SERIAL PRIMARY KEY,
    coin_id INTEGER NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    field_name VARCHAR(200) NOT NULL,
    field_value TEXT,
    field_type VARCHAR(50) NOT NULL CHECK (field_type IN ('text', 'number', 'boolean', 'select', 'date')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_coin_metadata_coin_id ON coin_metadata(coin_id);
CREATE INDEX idx_coin_metadata_field_name ON coin_metadata(field_name);
CREATE INDEX idx_coin_metadata_field_type ON coin_metadata(field_type);
CREATE INDEX idx_coin_metadata_field_value ON coin_metadata(field_value);

-- Create composite index for efficient queries
CREATE INDEX idx_coin_metadata_coin_field ON coin_metadata(coin_id, field_name);

-- Create updated_at trigger
CREATE TRIGGER update_coin_metadata_updated_at 
    BEFORE UPDATE ON coin_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE coin_metadata IS 'Dynamic metadata fields for coins based on their category metadata templates';
COMMENT ON COLUMN coin_metadata.coin_id IS 'Reference to the coin';
COMMENT ON COLUMN coin_metadata.field_name IS 'Metadata field name (e.g., coins.year, coins.grade)';
COMMENT ON COLUMN coin_metadata.field_value IS 'Metadata field value stored as text';
COMMENT ON COLUMN coin_metadata.field_type IS 'Field type for validation and UI rendering';

-- Create a view for easy querying of coins with their metadata
CREATE VIEW coins_with_metadata AS
SELECT 
    c.id,
    c.sku,
    c.title,
    c.year,
    c.denomination,
    c.mint_mark,
    c.grade,
    c.category,
    c.description,
    c.condition_notes,
    c.is_silver,
    c.silver_percent,
    c.silver_content_oz,
    c.paid_price,
    c.price_strategy,
    c.price_multiplier,
    c.base_from_entry,
    c.entry_spot,
    c.entry_melt,
    c.override_price,
    c.override_value,
    c.computed_price,
    c.quantity,
    c.status,
    c.created_by,
    c.category_id,
    c.created_at,
    c.updated_at,
    cc.name as category_name,
    cc.display_name as category_display_name,
    cc.category_type,
    -- Aggregate metadata as JSON
    COALESCE(
        json_object_agg(
            cm.field_name, 
            cm.field_value
        ) FILTER (WHERE cm.field_name IS NOT NULL),
        '{}'::json
    ) as metadata
FROM coins c
LEFT JOIN coin_categories cc ON c.category_id = cc.id
LEFT JOIN coin_metadata cm ON c.id = cm.coin_id
GROUP BY c.id, cc.name, cc.display_name, cc.category_type;

-- Create a function to get metadata templates for a category
CREATE OR REPLACE FUNCTION get_category_metadata_templates(category_id INTEGER)
RETURNS TABLE (
    field_name VARCHAR,
    field_type VARCHAR,
    field_label VARCHAR,
    field_description TEXT,
    is_required BOOLEAN,
    default_value VARCHAR,
    select_options JSONB,
    validation_rules JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.field_name,
        cm.field_type,
        cm.field_label,
        cm.field_description,
        cm.is_required,
        cm.default_value,
        cm.select_options,
        cm.validation_rules
    FROM category_metadata cm
    WHERE cm.category_id = get_category_metadata_templates.category_id
    ORDER BY cm.sort_order, cm.field_name;
END;
$$ LANGUAGE plpgsql;

-- Create a function to create metadata fields for a coin based on its category
CREATE OR REPLACE FUNCTION create_coin_metadata_from_category(coin_id INTEGER)
RETURNS VOID AS $$
DECLARE
    category_id INTEGER;
    metadata_record RECORD;
BEGIN
    -- Get the coin's category
    SELECT c.category_id INTO category_id
    FROM coins c
    WHERE c.id = create_coin_metadata_from_category.coin_id;
    
    -- Only proceed if coin has a category
    IF category_id IS NULL THEN
        RETURN;
    END IF;
    
    -- Create metadata entries for all category metadata fields
    FOR metadata_record IN 
        SELECT field_name, field_type, default_value
        FROM category_metadata
        WHERE category_id = create_coin_metadata_from_category.coin_id
    LOOP
        -- Check if metadata already exists
        IF NOT EXISTS (
            SELECT 1 FROM coin_metadata 
            WHERE coin_metadata.coin_id = create_coin_metadata_from_category.coin_id 
            AND coin_metadata.field_name = metadata_record.field_name
        ) THEN
            INSERT INTO coin_metadata (coin_id, field_name, field_value, field_type)
            VALUES (
                create_coin_metadata_from_category.coin_id,
                metadata_record.field_name,
                metadata_record.default_value,
                metadata_record.field_type
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create a function to update coin metadata when category changes
CREATE OR REPLACE FUNCTION update_coin_metadata_on_category_change()
RETURNS TRIGGER AS $$
BEGIN
    -- If category_id changed
    IF OLD.category_id IS DISTINCT FROM NEW.category_id THEN
        -- Delete old metadata
        DELETE FROM coin_metadata 
        WHERE coin_id = NEW.id;
        
        -- Create new metadata based on new category
        PERFORM create_coin_metadata_from_category(NEW.id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update metadata when coin category changes
CREATE TRIGGER coin_category_change_trigger
    AFTER UPDATE OF category_id ON coins
    FOR EACH ROW
    EXECUTE FUNCTION update_coin_metadata_on_category_change();

-- Create a function to validate metadata field values
CREATE OR REPLACE FUNCTION validate_coin_metadata()
RETURNS TRIGGER AS $$
DECLARE
    category_metadata_record RECORD;
BEGIN
    -- Get the category metadata template for this field
    SELECT cm.* INTO category_metadata_record
    FROM category_metadata cm
    JOIN coins c ON cm.category_id = c.category_id
    WHERE c.id = NEW.coin_id 
    AND cm.field_name = NEW.field_name;
    
    -- If no template found, allow the metadata (might be custom)
    IF NOT FOUND THEN
        RETURN NEW;
    END IF;
    
    -- Validate field type
    IF category_metadata_record.field_type = 'number' THEN
        -- Validate that value is a number
        IF NEW.field_value IS NOT NULL AND NEW.field_value !~ '^-?\d+(\.\d+)?$' THEN
            RAISE EXCEPTION 'Invalid number value for field %: %', NEW.field_name, NEW.field_value;
        END IF;
    ELSIF category_metadata_record.field_type = 'boolean' THEN
        -- Validate boolean value
        IF NEW.field_value IS NOT NULL AND NEW.field_value NOT IN ('true', 'false', '1', '0') THEN
            RAISE EXCEPTION 'Invalid boolean value for field %: %', NEW.field_name, NEW.field_value;
        END IF;
    ELSIF category_metadata_record.field_type = 'select' THEN
        -- Validate select option
        IF NEW.field_value IS NOT NULL AND category_metadata_record.select_options IS NOT NULL THEN
            IF NOT (category_metadata_record.select_options ? NEW.field_value) THEN
                RAISE EXCEPTION 'Invalid select option for field %: %', NEW.field_name, NEW.field_value;
            END IF;
        END IF;
    ELSIF category_metadata_record.field_type = 'date' THEN
        -- Basic date validation (can be enhanced)
        IF NEW.field_value IS NOT NULL AND NEW.field_value !~ '^\d{4}-\d{2}-\d{2}$' THEN
            RAISE EXCEPTION 'Invalid date format for field %: % (expected YYYY-MM-DD)', NEW.field_name, NEW.field_value;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to validate metadata field values
CREATE TRIGGER validate_coin_metadata_trigger
    BEFORE INSERT OR UPDATE ON coin_metadata
    FOR EACH ROW
    EXECUTE FUNCTION validate_coin_metadata();

-- Insert sample metadata for existing coins (if any have categories)
DO $$
DECLARE
    coin_record RECORD;
BEGIN
    FOR coin_record IN 
        SELECT id, category_id 
        FROM coins 
        WHERE category_id IS NOT NULL
    LOOP
        PERFORM create_coin_metadata_from_category(coin_record.id);
    END LOOP;
END $$;

-- Create an index for searching metadata values
CREATE INDEX idx_coin_metadata_search ON coin_metadata USING GIN (to_tsvector('english', field_value));

-- Add a function to search coins by metadata
CREATE OR REPLACE FUNCTION search_coins_by_metadata(
    search_term TEXT DEFAULT NULL,
    category_id_param INTEGER DEFAULT NULL,
    metadata_filter JSONB DEFAULT NULL
)
RETURNS TABLE (
    coin_id INTEGER,
    title VARCHAR,
    sku VARCHAR,
    category_name VARCHAR,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.title,
        c.sku,
        cc.name,
        COALESCE(
            json_object_agg(cm.field_name, cm.field_value) FILTER (WHERE cm.field_name IS NOT NULL),
            '{}'::json
        ) as metadata
    FROM coins c
    LEFT JOIN coin_categories cc ON c.category_id = cc.id
    LEFT JOIN coin_metadata cm ON c.id = cm.coin_id
    WHERE 
        (search_term IS NULL OR c.title ILIKE '%' || search_term || '%' OR c.sku ILIKE '%' || search_term || '%')
        AND (category_id_param IS NULL OR c.category_id = category_id_param)
    GROUP BY c.id, cc.name
    HAVING 
        (metadata_filter IS NULL OR (
            SELECT bool_and(
                EXISTS (
                    SELECT 1 FROM coin_metadata cm2 
                    WHERE cm2.coin_id = c.id 
                    AND cm2.field_name = key 
                    AND cm2.field_value = value::text
                )
            )
            FROM jsonb_each(metadata_filter)
        ))
    ORDER BY c.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Add comments for the new functions and views
COMMENT ON FUNCTION get_category_metadata_templates(INTEGER) IS 'Get metadata field templates for a category';
COMMENT ON FUNCTION create_coin_metadata_from_category(INTEGER) IS 'Create metadata fields for a coin based on its category';
COMMENT ON FUNCTION update_coin_metadata_on_category_change() IS 'Update coin metadata when category changes';
COMMENT ON FUNCTION validate_coin_metadata() IS 'Validate metadata field values against category templates';
COMMENT ON FUNCTION search_coins_by_metadata(TEXT, INTEGER, JSONB) IS 'Search coins by metadata with advanced filtering';
COMMENT ON VIEW coins_with_metadata IS 'View combining coins with their metadata and category information';
