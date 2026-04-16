-- Real-Time Sync System Migration
-- Multi-channel synchronization with conflict resolution

-- 1. Create Sync Channels Table
CREATE TABLE IF NOT EXISTS sync_channels (
    id SERIAL PRIMARY KEY,
    channel_name VARCHAR(50) UNIQUE NOT NULL,
    channel_type VARCHAR(20) NOT NULL, -- SHOPIFY, EBAY, ETSY, IN_STORE, AUCTION, DIRECT
    is_active BOOLEAN DEFAULT TRUE,
    sync_frequency_minutes INTEGER DEFAULT 60, -- Sync every X minutes
    last_sync_at TIMESTAMP,
    next_sync_at TIMESTAMP,
    sync_config JSONB, -- Channel-specific configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create Sync Logs Table
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES sync_channels(id) ON DELETE CASCADE,
    sync_type VARCHAR(20) NOT NULL, -- FULL, INCREMENTAL, PRODUCTS, INVENTORY, ORDERS
    status VARCHAR(20) NOT NULL, -- PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    items_processed INTEGER DEFAULT 0,
    items_successful INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_message TEXT,
    sync_data JSONB, -- Detailed sync results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Sync Conflicts Table
CREATE TABLE IF NOT EXISTS sync_conflicts (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES sync_channels(id) ON DELETE CASCADE,
    conflict_type VARCHAR(50) NOT NULL, -- PRICE_MISMATCH, INVENTORY_MISMATCH, PRODUCT_NOT_FOUND, DUPLICATE_SKU
    resource_type VARCHAR(50) NOT NULL, -- PRODUCT, INVENTORY, ORDER
    resource_id VARCHAR(100) NOT NULL,
    local_data JSONB,
    remote_data JSONB,
    conflict_details JSONB,
    resolution_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, RESOLVED, IGNORED, ESCALATED
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create Sync Queue Table for real-time processing
CREATE TABLE IF NOT EXISTS sync_queue (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES sync_channels(id) ON DELETE CASCADE,
    operation VARCHAR(20) NOT NULL, -- CREATE, UPDATE, DELETE, SYNC
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    resource_data JSONB,
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create Sync Status Table for tracking sync state
CREATE TABLE IF NOT EXISTS sync_status (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES sync_channels(id) ON DELETE CASCADE,
    last_full_sync TIMESTAMP,
    last_incremental_sync TIMESTAMP,
    last_product_sync TIMESTAMP,
    last_inventory_sync TIMESTAMP,
    last_order_sync TIMESTAMP,
    sync_in_progress BOOLEAN DEFAULT FALSE,
    current_sync_id INTEGER REFERENCES sync_logs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sync_channels_name ON sync_channels(channel_name);
CREATE INDEX IF NOT EXISTS idx_sync_channels_type ON sync_channels(channel_type);
CREATE INDEX IF NOT EXISTS idx_sync_channels_active ON sync_channels(is_active);

CREATE INDEX IF NOT EXISTS idx_sync_logs_channel ON sync_logs(channel_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON sync_logs(status);
CREATE INDEX IF NOT EXISTS idx_sync_logs_started_at ON sync_logs(started_at);

CREATE INDEX IF NOT EXISTS idx_sync_conflicts_channel ON sync_conflicts(channel_id);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_type ON sync_conflicts(conflict_type);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_status ON sync_conflicts(resolution_status);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_resource ON sync_conflicts(resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_sync_queue_channel ON sync_queue(channel_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_priority ON sync_queue(priority);
CREATE INDEX IF NOT EXISTS idx_sync_queue_scheduled ON sync_queue(scheduled_at);

CREATE INDEX IF NOT EXISTS idx_sync_status_channel ON sync_status(channel_id);

-- 7. Insert default sync channels
INSERT INTO sync_channels (channel_name, channel_type, is_active, sync_frequency_minutes, sync_config) VALUES
('shopify', 'SHOPIFY', TRUE, 60, '{"api_version": "2023-10", "webhook_enabled": true}'),
('in_store', 'IN_STORE', TRUE, 1440, '{"manual_sync": true}'),
('auction', 'AUCTION', TRUE, 1440, '{"manual_sync": true}'),
('direct', 'DIRECT', TRUE, 1440, '{"manual_sync": true}'),
('ebay', 'EBAY', FALSE, 60, '{"api_version": "v1", "sandbox": true}'),
('etsy', 'ETSY', FALSE, 60, '{"api_version": "v3", "sandbox": true}')
ON CONFLICT (channel_name) DO NOTHING;

-- 8. Create sync status records for each channel
INSERT INTO sync_status (channel_id, sync_in_progress)
SELECT id, FALSE FROM sync_channels
ON CONFLICT DO NOTHING;

-- 9. Create function to process sync queue
CREATE OR REPLACE FUNCTION process_sync_queue()
RETURNS INTEGER AS $$
DECLARE
    queue_item RECORD;
    processed_count INTEGER := 0;
BEGIN
    -- Process items in priority order (1=highest, 10=lowest)
    FOR queue_item IN 
        SELECT * FROM sync_queue 
        WHERE status = 'PENDING' 
        AND scheduled_at <= NOW()
        ORDER BY priority ASC, created_at ASC
        LIMIT 100
    LOOP
        -- Update status to processing
        UPDATE sync_queue 
        SET status = 'PROCESSING', processed_at = NOW()
        WHERE id = queue_item.id;
        
        -- Here would be the actual sync processing logic
        -- For now, we'll just mark as completed
        UPDATE sync_queue 
        SET status = 'COMPLETED'
        WHERE id = queue_item.id;
        
        processed_count := processed_count + 1;
    END LOOP;
    
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- 10. Create function to detect sync conflicts
CREATE OR REPLACE FUNCTION detect_sync_conflict(
    p_channel_id INTEGER,
    p_resource_type VARCHAR(50),
    p_resource_id VARCHAR(100),
    p_local_data JSONB,
    p_remote_data JSONB
) RETURNS INTEGER AS $$
DECLARE
    conflict_id INTEGER;
    conflict_type VARCHAR(50);
BEGIN
    -- Determine conflict type based on data comparison
    conflict_type := 'DATA_MISMATCH';
    
    -- Check for specific conflict types
    IF p_local_data->>'price' != p_remote_data->>'price' THEN
        conflict_type := 'PRICE_MISMATCH';
    ELSIF p_local_data->>'inventory' != p_remote_data->>'inventory' THEN
        conflict_type := 'INVENTORY_MISMATCH';
    ELSIF p_remote_data IS NULL THEN
        conflict_type := 'PRODUCT_NOT_FOUND';
    END IF;
    
    -- Insert conflict record
    INSERT INTO sync_conflicts (
        channel_id, conflict_type, resource_type, resource_id,
        local_data, remote_data, conflict_details
    ) VALUES (
        p_channel_id, conflict_type, p_resource_type, p_resource_id,
        p_local_data, p_remote_data,
        jsonb_build_object('detected_at', NOW())
    ) RETURNING id INTO conflict_id;
    
    RETURN conflict_id;
END;
$$ LANGUAGE plpgsql;

-- 11. Create function to resolve sync conflicts
CREATE OR REPLACE FUNCTION resolve_sync_conflict(
    p_conflict_id INTEGER,
    p_resolution VARCHAR(20), -- USE_LOCAL, USE_REMOTE, MANUAL, IGNORE
    p_resolved_by VARCHAR(100),
    p_resolution_notes TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    conflict_record RECORD;
BEGIN
    -- Get conflict details
    SELECT * INTO conflict_record FROM sync_conflicts WHERE id = p_conflict_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Update conflict resolution
    UPDATE sync_conflicts
    SET resolution_status = 'RESOLVED',
        resolved_by = p_resolved_by,
        resolved_at = NOW(),
        resolution_notes = p_resolution_notes,
        conflict_details = conflict_details || jsonb_build_object('resolution', p_resolution)
    WHERE id = p_conflict_id;
    
    -- Here would be the actual resolution logic based on p_resolution
    -- For now, we'll just mark as resolved
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 12. Create trigger to update sync_status when sync completes
CREATE OR REPLACE FUNCTION update_sync_status_on_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' THEN
        -- Update sync status based on sync type
        CASE NEW.sync_type
            WHEN 'FULL' THEN
                UPDATE sync_status SET last_full_sync = NEW.completed_at WHERE channel_id = NEW.channel_id;
            WHEN 'INCREMENTAL' THEN
                UPDATE sync_status SET last_incremental_sync = NEW.completed_at WHERE channel_id = NEW.channel_id;
            WHEN 'PRODUCTS' THEN
                UPDATE sync_status SET last_product_sync = NEW.completed_at WHERE channel_id = NEW.channel_id;
            WHEN 'INVENTORY' THEN
                UPDATE sync_status SET last_inventory_sync = NEW.completed_at WHERE channel_id = NEW.channel_id;
            WHEN 'ORDERS' THEN
                UPDATE sync_status SET last_order_sync = NEW.completed_at WHERE channel_id = NEW.channel_id;
        END CASE;
        
        -- Mark sync as no longer in progress
        UPDATE sync_status 
        SET sync_in_progress = FALSE, current_sync_id = NULL 
        WHERE channel_id = NEW.channel_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_sync_status_on_completion
    AFTER UPDATE ON sync_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_sync_status_on_completion();

-- 13. Add constraints
ALTER TABLE sync_channels ADD CONSTRAINT check_channel_type_valid CHECK (channel_type IN ('SHOPIFY', 'EBAY', 'ETSY', 'IN_STORE', 'AUCTION', 'DIRECT'));
ALTER TABLE sync_logs ADD CONSTRAINT check_sync_type_valid CHECK (sync_type IN ('FULL', 'INCREMENTAL', 'PRODUCTS', 'INVENTORY', 'ORDERS'));
ALTER TABLE sync_logs ADD CONSTRAINT check_sync_status_valid CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'));
ALTER TABLE sync_conflicts ADD CONSTRAINT check_conflict_type_valid CHECK (conflict_type IN ('PRICE_MISMATCH', 'INVENTORY_MISMATCH', 'PRODUCT_NOT_FOUND', 'DUPLICATE_SKU', 'DATA_MISMATCH'));
ALTER TABLE sync_conflicts ADD CONSTRAINT check_resolution_status_valid CHECK (resolution_status IN ('PENDING', 'RESOLVED', 'IGNORED', 'ESCALATED'));
ALTER TABLE sync_queue ADD CONSTRAINT check_operation_valid CHECK (operation IN ('CREATE', 'UPDATE', 'DELETE', 'SYNC'));
ALTER TABLE sync_queue ADD CONSTRAINT check_queue_status_valid CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'));

-- 14. Add comments for documentation
COMMENT ON TABLE sync_channels IS 'Sync channel configuration and management';
COMMENT ON TABLE sync_logs IS 'Sync operation logs and history';
COMMENT ON TABLE sync_conflicts IS 'Sync conflicts and resolution tracking';
COMMENT ON TABLE sync_queue IS 'Real-time sync queue for processing';
COMMENT ON TABLE sync_status IS 'Current sync status for each channel';

-- Success message
SELECT 'Real-Time Sync System schema created successfully!' as status;
