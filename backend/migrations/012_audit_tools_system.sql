-- Audit Tools System Migration
-- Comprehensive audit logging, compliance reporting, and data integrity monitoring

-- 1. Create Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(100)
);

-- 2. Create Audit Events Table for custom events
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'INFO', -- INFO, WARNING, ERROR, CRITICAL
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

-- 3. Create Compliance Reports Table
CREATE TABLE IF NOT EXISTS compliance_reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,
    report_name VARCHAR(200) NOT NULL,
    report_data JSONB NOT NULL,
    generated_by VARCHAR(100),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE' -- ACTIVE, EXPIRED, ARCHIVED
);

-- 4. Create Data Integrity Checks Table
CREATE TABLE IF NOT EXISTS data_integrity_checks (
    id SERIAL PRIMARY KEY,
    check_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL, -- CONSTRAINT, REFERENCE, CONSISTENCY, BUSINESS_RULE
    table_name VARCHAR(100),
    column_name VARCHAR(100),
    check_query TEXT,
    expected_result TEXT,
    actual_result TEXT,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, PASSED, FAILED, ERROR
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create User Activity Logs Table
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX IF NOT EXISTS idx_audit_logs_changed_at ON audit_logs(changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_changed_by ON audit_logs(changed_by);

CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_category ON audit_events(event_category);
CREATE INDEX IF NOT EXISTS idx_audit_events_severity ON audit_events(severity);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at);

CREATE INDEX IF NOT EXISTS idx_compliance_reports_type ON compliance_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_status ON compliance_reports(status);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_generated_at ON compliance_reports(generated_at);

CREATE INDEX IF NOT EXISTS idx_data_integrity_checks_name ON data_integrity_checks(check_name);
CREATE INDEX IF NOT EXISTS idx_data_integrity_checks_type ON data_integrity_checks(check_type);
CREATE INDEX IF NOT EXISTS idx_data_integrity_checks_status ON data_integrity_checks(status);
CREATE INDEX IF NOT EXISTS idx_data_integrity_checks_table ON data_integrity_checks(table_name);

CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_action ON user_activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);

-- 7. Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (table_name, record_id, operation, new_values, changed_by, changed_at)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW), current_user, NOW());
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (table_name, record_id, operation, old_values, new_values, changed_by, changed_at)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_user, NOW());
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (table_name, record_id, operation, old_values, changed_by, changed_at)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD), current_user, NOW());
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 8. Create audit triggers for key tables
CREATE TRIGGER audit_coins_trigger
    AFTER INSERT OR UPDATE OR DELETE ON coins
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_collections_trigger
    AFTER INSERT OR UPDATE OR DELETE ON collections
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_bulk_operations_trigger
    AFTER INSERT OR UPDATE OR DELETE ON bulk_operations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_sku_prefixes_trigger
    AFTER INSERT OR UPDATE OR DELETE ON sku_prefixes
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- 9. Create function to generate compliance reports
CREATE OR REPLACE FUNCTION generate_compliance_report(
    p_report_type VARCHAR(50),
    p_report_name VARCHAR(200),
    p_generated_by VARCHAR(100)
) RETURNS INTEGER AS $$
DECLARE
    report_id INTEGER;
    report_data JSONB;
BEGIN
    -- Generate report data based on type
    CASE p_report_type
        WHEN 'USER_ACTIVITY' THEN
            SELECT jsonb_build_object(
                'total_activities', COUNT(*),
                'unique_users', COUNT(DISTINCT user_id),
                'activities_by_action', jsonb_object_agg(action, action_count)
            ) INTO report_data
            FROM (
                SELECT action, COUNT(*) as action_count
                FROM user_activity_logs
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY action
            ) subq;
        
        WHEN 'DATA_CHANGES' THEN
            SELECT jsonb_build_object(
                'total_changes', COUNT(*),
                'changes_by_table', jsonb_object_agg(table_name, table_count),
                'changes_by_operation', jsonb_object_agg(operation, operation_count)
            ) INTO report_data
            FROM (
                SELECT table_name, operation, COUNT(*) as table_count, COUNT(*) as operation_count
                FROM audit_logs
                WHERE changed_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY table_name, operation
            ) subq;
        
        WHEN 'SYSTEM_HEALTH' THEN
            SELECT jsonb_build_object(
                'total_events', COUNT(*),
                'events_by_severity', jsonb_object_agg(severity, severity_count),
                'unresolved_events', COUNT(*) FILTER (WHERE resolved_at IS NULL)
            ) INTO report_data
            FROM (
                SELECT severity, COUNT(*) as severity_count
                FROM audit_events
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY severity
            ) subq;
        
        ELSE
            report_data := '{}'::jsonb;
    END CASE;
    
    -- Insert compliance report
    INSERT INTO compliance_reports (report_type, report_name, report_data, generated_by)
    VALUES (p_report_type, p_report_name, report_data, p_generated_by)
    RETURNING id INTO report_id;
    
    RETURN report_id;
END;
$$ LANGUAGE plpgsql;

-- 10. Create function to run data integrity checks
CREATE OR REPLACE FUNCTION run_data_integrity_check(p_check_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    check_record RECORD;
    result_count INTEGER;
    check_passed BOOLEAN := FALSE;
BEGIN
    -- Get check details
    SELECT * INTO check_record FROM data_integrity_checks WHERE id = p_check_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Run the check query
    EXECUTE check_record.check_query INTO result_count;
    
    -- Compare with expected result
    IF check_record.expected_result IS NULL THEN
        check_passed := (result_count = 0);
    ELSE
        check_passed := (result_count::TEXT = check_record.expected_result);
    END IF;
    
    -- Update check status
    UPDATE data_integrity_checks
    SET status = CASE WHEN check_passed THEN 'PASSED' ELSE 'FAILED' END,
        actual_result = result_count::TEXT,
        last_run = NOW(),
        updated_at = NOW()
    WHERE id = p_check_id;
    
    -- Log the result as an audit event
    INSERT INTO audit_events (event_type, event_category, description, severity)
    VALUES (
        'DATA_INTEGRITY_CHECK',
        'SYSTEM',
        'Data integrity check "' || check_record.check_name || '" ' || 
        CASE WHEN check_passed THEN 'PASSED' ELSE 'FAILED' END,
        CASE WHEN check_passed THEN 'INFO' ELSE 'WARNING' END
    );
    
    RETURN check_passed;
END;
$$ LANGUAGE plpgsql;

-- 11. Insert default data integrity checks
INSERT INTO data_integrity_checks (check_name, check_type, table_name, check_query, expected_result) VALUES
('Coins SKU Uniqueness', 'CONSTRAINT', 'coins', 'SELECT COUNT(*) FROM coins WHERE sku IS NULL OR sku = ''''', '0'),
('Collections Name Uniqueness', 'CONSTRAINT', 'collections', 'SELECT COUNT(*) FROM collections WHERE name IS NULL OR name = ''''', '0'),
('SKU Prefixes Uniqueness', 'CONSTRAINT', 'sku_prefixes', 'SELECT COUNT(*) FROM sku_prefixes WHERE prefix IS NULL OR prefix = ''''', '0'),
('Bulk Operations Status', 'BUSINESS_RULE', 'bulk_operations', 'SELECT COUNT(*) FROM bulk_operations WHERE status NOT IN (''pending'', ''processing'', ''completed'', ''failed'', ''cancelled'')', '0'),
('Orphaned Bulk Items', 'REFERENCE', 'bulk_operation_items', 'SELECT COUNT(*) FROM bulk_operation_items boi LEFT JOIN bulk_operations bo ON boi.bulk_operation_id = bo.id WHERE bo.id IS NULL', '0'),
('Orphaned SKU Sequences', 'REFERENCE', 'sku_sequences', 'SELECT COUNT(*) FROM sku_sequences ss LEFT JOIN sku_prefixes sp ON ss.prefix = sp.prefix WHERE sp.prefix IS NULL', '0')
ON CONFLICT DO NOTHING;

-- 12. Add constraints
ALTER TABLE audit_logs ADD CONSTRAINT check_operation_valid CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'));
ALTER TABLE audit_events ADD CONSTRAINT check_severity_valid CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'));
ALTER TABLE compliance_reports ADD CONSTRAINT check_status_valid CHECK (status IN ('ACTIVE', 'EXPIRED', 'ARCHIVED'));
ALTER TABLE data_integrity_checks ADD CONSTRAINT check_status_valid CHECK (status IN ('PENDING', 'PASSED', 'FAILED', 'ERROR'));

-- 13. Add comments for documentation
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for all data changes';
COMMENT ON TABLE audit_events IS 'System events and custom audit events';
COMMENT ON TABLE compliance_reports IS 'Generated compliance and audit reports';
COMMENT ON TABLE data_integrity_checks IS 'Data integrity validation rules and checks';
COMMENT ON TABLE user_activity_logs IS 'User activity tracking and monitoring';

-- Success message
SELECT 'Audit Tools System schema created successfully!' as status;
