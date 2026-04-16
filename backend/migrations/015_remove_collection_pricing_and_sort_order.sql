-- Migration: Remove pricing strategy and sort order from collections
-- Date: 2025-01-28
-- Description: Remove default_markup and sort_order columns from collections table

-- Remove default_markup column
ALTER TABLE collections DROP COLUMN IF EXISTS default_markup;

-- Remove sort_order column  
ALTER TABLE collections DROP COLUMN IF EXISTS sort_order;

-- Update any existing collections to ensure they have proper defaults
UPDATE collections SET color = '#3b82f6' WHERE color IS NULL;

-- Add comment to document the change
COMMENT ON TABLE collections IS 'Collections table - pricing strategies removed as they belong to individual products, sort order removed in favor of drag-and-drop reordering';

