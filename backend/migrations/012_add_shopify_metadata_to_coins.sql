-- Add tags and metadata columns to coins table
-- Migration: Add Shopify metadata support to coins table

-- Add tags column (JSON array of strings)
ALTER TABLE coins ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]';

-- Add shopify_metadata column (JSON object for Shopify metadata)
ALTER TABLE coins ADD COLUMN IF NOT EXISTS shopify_metadata JSON DEFAULT '{}';

-- Update existing coins to have empty tags and metadata
UPDATE coins SET tags = '[]' WHERE tags IS NULL;
UPDATE coins SET shopify_metadata = '{}' WHERE shopify_metadata IS NULL;
