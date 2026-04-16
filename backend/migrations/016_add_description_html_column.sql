-- Migration to add description_html column to collections table
-- Run this manually if the column doesn't exist

-- Check if column exists first
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'collections' 
        AND column_name = 'description_html'
    ) THEN
        -- Add the column if it doesn't exist
        ALTER TABLE collections ADD COLUMN description_html TEXT;
        RAISE NOTICE 'Added description_html column to collections table';
    ELSE
        RAISE NOTICE 'description_html column already exists in collections table';
    END IF;
END $$;

