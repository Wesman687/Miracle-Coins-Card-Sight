-- Migration to rename 'name' column to 'title' in coins table
-- This aligns the database schema with frontend expectations

-- Rename the column
ALTER TABLE coins RENAME COLUMN name TO title;

-- Update any indexes that might reference the old column name
-- (if there are any specific indexes on the name column, they would be recreated automatically)

-- Add a comment to document the change
COMMENT ON COLUMN coins.title IS 'Coin title/name - renamed from name to match frontend expectations';

