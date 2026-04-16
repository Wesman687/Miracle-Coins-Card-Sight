-- Migration: Bulk Operations System
-- Description: Add bulk operations tables and enhance coin tracking
-- Date: 2025-01-28
-- Version: 1.0

-- Bulk operations tracking table
CREATE TABLE IF NOT EXISTS bulk_operations (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL, -- 'purchase', 'transfer', 'price_update', 'status_change'
    description TEXT,
    total_items INTEGER NOT NULL,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'cancelled'
    created_by INTEGER, -- Will reference users table when available
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    operation_metadata JSONB -- Store operation-specific data
);

-- Bulk operation items tracking
CREATE TABLE IF NOT EXISTS bulk_operation_items (
    id SERIAL PRIMARY KEY,
    bulk_operation_id INTEGER REFERENCES bulk_operations(id) ON DELETE CASCADE,
    coin_id INTEGER REFERENCES coins(id),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,
    processed_at TIMESTAMP,
    item_metadata JSONB -- Store item-specific data
);

-- Add bulk operation reference to coins table
ALTER TABLE coins ADD COLUMN IF NOT EXISTS bulk_operation_id INTEGER REFERENCES bulk_operations(id);
ALTER TABLE coins ADD COLUMN IF NOT EXISTS bulk_item_id INTEGER REFERENCES bulk_operation_items(id);

-- Add serial number tracking for bulk operations
ALTER TABLE coins ADD COLUMN IF NOT EXISTS serial_number VARCHAR(50);
ALTER TABLE coins ADD COLUMN IF NOT EXISTS bulk_sequence_number INTEGER;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON bulk_operations(status);
CREATE INDEX IF NOT EXISTS idx_bulk_operations_type ON bulk_operations(operation_type);
CREATE INDEX IF NOT EXISTS idx_bulk_operation_items_operation ON bulk_operation_items(bulk_operation_id);
CREATE INDEX IF NOT EXISTS idx_bulk_operation_items_status ON bulk_operation_items(status);
CREATE INDEX IF NOT EXISTS idx_coins_bulk_operation ON coins(bulk_operation_id);
CREATE INDEX IF NOT EXISTS idx_coins_serial_number ON coins(serial_number);

-- Add constraints
ALTER TABLE bulk_operations ADD CONSTRAINT check_total_items_positive CHECK (total_items > 0);
ALTER TABLE bulk_operations ADD CONSTRAINT check_total_items_max CHECK (total_items <= 10000000); -- 10M max
ALTER TABLE bulk_operations ADD CONSTRAINT check_processed_items_valid CHECK (processed_items >= 0 AND processed_items <= total_items);
ALTER TABLE bulk_operations ADD CONSTRAINT check_failed_items_valid CHECK (failed_items >= 0 AND failed_items <= total_items);
