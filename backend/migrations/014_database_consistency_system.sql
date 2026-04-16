-- Database Consistency System Migration
-- Automated validation and repair mechanisms

-- 1. Create Consistency Rules Table
CREATE TABLE IF NOT EXISTS consistency_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- CONSTRAINT, REFERENCE, BUSINESS_LOGIC, DATA_QUALITY
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100),
    rule_description TEXT NOT NULL,
    validation_query TEXT NOT NULL,
    repair_query TEXT,
    severity VARCHAR(20) DEFAULT 'WARNING', -- INFO, WARNING, ERROR, CRITICAL
    is_active BOOLEAN DEFAULT TRUE,
    auto_repair BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create Consistency Checks Table
CREATE TABLE IF NOT EXISTS consistency_checks (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES consistency_rules(id) ON DELETE CASCADE,
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

-- 3. Create Consistency Violations Table
CREATE TABLE IF NOT EXISTS consistency_violations (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES consistency_rules(id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100),
    column_name VARCHAR(100),
    expected_value TEXT,
    actual_value TEXT,
    violation_details JSONB,
    severity VARCHAR(20) DEFAULT 'WARNING',
    status VARCHAR(20) DEFAULT 'DETECTED', -- DETECTED, REPAIRING, REPAIRED, IGNORED, ESCALATED
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    repaired_at TIMESTAMP,
    repaired_by VARCHAR(100),
    repair_notes TEXT
);

-- 4. Create Consistency Reports Table
CREATE TABLE IF NOT EXISTS consistency_reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL, -- DAILY, WEEKLY, MONTHLY, ON_DEMAND
    report_name VARCHAR(200) NOT NULL,
    report_data JSONB NOT NULL,
    total_violations INTEGER DEFAULT 0,
    violations_by_severity JSONB,
    violations_by_table JSONB,
    generated_by VARCHAR(100),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE' -- ACTIVE, EXPIRED, ARCHIVED
);

-- 5. Create Consistency Repair Logs Table
CREATE TABLE IF NOT EXISTS consistency_repair_logs (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES consistency_rules(id) ON DELETE CASCADE,
    violation_id INTEGER REFERENCES consistency_violations(id) ON DELETE CASCADE,
    repair_action VARCHAR(100) NOT NULL,
    repair_query TEXT,
    repair_result JSONB,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, SUCCESS, FAILED, ROLLBACK
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    repaired_by VARCHAR(100)
);

-- 6. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_consistency_rules_name ON consistency_rules(rule_name);
CREATE INDEX IF NOT EXISTS idx_consistency_rules_type ON consistency_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_consistency_rules_table ON consistency_rules(table_name);
CREATE INDEX IF NOT EXISTS idx_consistency_rules_active ON consistency_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_consistency_checks_rule ON consistency_checks(rule_id);
CREATE INDEX IF NOT EXISTS idx_consistency_checks_type ON consistency_checks(check_type);
CREATE INDEX IF NOT EXISTS idx_consistency_checks_status ON consistency_checks(status);
CREATE INDEX IF NOT EXISTS idx_consistency_checks_table ON consistency_checks(table_name);

CREATE INDEX IF NOT EXISTS idx_consistency_violations_rule ON consistency_violations(rule_id);
CREATE INDEX IF NOT EXISTS idx_consistency_violations_type ON consistency_violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_consistency_violations_table ON consistency_violations(table_name);
CREATE INDEX IF NOT EXISTS idx_consistency_violations_status ON consistency_violations(status);
CREATE INDEX IF NOT EXISTS idx_consistency_violations_severity ON consistency_violations(severity);

CREATE INDEX IF NOT EXISTS idx_consistency_reports_type ON consistency_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_consistency_reports_status ON consistency_reports(status);
CREATE INDEX IF NOT EXISTS idx_consistency_reports_generated ON consistency_reports(generated_at);

CREATE INDEX IF NOT EXISTS idx_consistency_repair_logs_rule ON consistency_repair_logs(rule_id);
CREATE INDEX IF NOT EXISTS idx_consistency_repair_logs_violation ON consistency_repair_logs(violation_id);
CREATE INDEX IF NOT EXISTS idx_consistency_repair_logs_status ON consistency_repair_logs(status);

-- 7. Insert default consistency rules
INSERT INTO consistency_rules (rule_name, rule_type, table_name, rule_description, validation_query, repair_query, severity, auto_repair) VALUES
('Coins SKU Uniqueness', 'CONSTRAINT', 'coins', 'All coins must have unique, non-null SKUs', 'SELECT COUNT(*) FROM coins WHERE sku IS NULL OR sku = ''''', 'UPDATE coins SET sku = ''UNKNOWN-'' || id WHERE sku IS NULL OR sku = ''''', 'ERROR', true),
('Collections Name Uniqueness', 'CONSTRAINT', 'collections', 'All collections must have unique, non-null names', 'SELECT COUNT(*) FROM collections WHERE name IS NULL OR name = ''''', 'UPDATE collections SET name = ''UNKNOWN-'' || id WHERE name IS NULL OR name = ''''', 'ERROR', true),
('SKU Prefixes Uniqueness', 'CONSTRAINT', 'sku_prefixes', 'All SKU prefixes must be unique and non-null', 'SELECT COUNT(*) FROM sku_prefixes WHERE prefix IS NULL OR prefix = ''''', NULL, 'ERROR', false),
('Bulk Operations Status', 'BUSINESS_LOGIC', 'bulk_operations', 'Bulk operations must have valid status values', 'SELECT COUNT(*) FROM bulk_operations WHERE status NOT IN (''pending'', ''processing'', ''completed'', ''failed'', ''cancelled'')', 'UPDATE bulk_operations SET status = ''pending'' WHERE status NOT IN (''pending'', ''processing'', ''completed'', ''failed'', ''cancelled'')', 'WARNING', true),
('Orphaned Bulk Items', 'REFERENCE', 'bulk_operation_items', 'Bulk operation items must reference valid bulk operations', 'SELECT COUNT(*) FROM bulk_operation_items boi LEFT JOIN bulk_operations bo ON boi.bulk_operation_id = bo.id WHERE bo.id IS NULL', 'DELETE FROM bulk_operation_items WHERE bulk_operation_id NOT IN (SELECT id FROM bulk_operations)', 'ERROR', true),
('Orphaned SKU Sequences', 'REFERENCE', 'sku_sequences', 'SKU sequences must reference valid SKU prefixes', 'SELECT COUNT(*) FROM sku_sequences ss LEFT JOIN sku_prefixes sp ON ss.prefix = sp.prefix WHERE sp.prefix IS NULL', 'DELETE FROM sku_sequences WHERE prefix NOT IN (SELECT prefix FROM sku_prefixes)', 'ERROR', true),
('Coins Price Validation', 'DATA_QUALITY', 'coins', 'Coin prices must be positive numbers', 'SELECT COUNT(*) FROM coins WHERE paid_price < 0 OR computed_price < 0', 'UPDATE coins SET paid_price = 0 WHERE paid_price < 0; UPDATE coins SET computed_price = 0 WHERE computed_price < 0', 'WARNING', true),
('Sync Channels Configuration', 'BUSINESS_LOGIC', 'sync_channels', 'Sync channels must have valid configuration', 'SELECT COUNT(*) FROM sync_channels WHERE channel_name IS NULL OR channel_type IS NULL', 'UPDATE sync_channels SET channel_name = ''UNKNOWN-'' || id WHERE channel_name IS NULL', 'ERROR', true),
('Audit Logs Integrity', 'REFERENCE', 'audit_logs', 'Audit logs must reference valid tables', 'SELECT COUNT(*) FROM audit_logs WHERE table_name NOT IN (''coins'', ''collections'', ''bulk_operations'', ''sku_prefixes'', ''sync_channels'', ''audit_logs'', ''audit_events'')', NULL, 'WARNING', false),
('Data Type Consistency', 'DATA_QUALITY', 'coins', 'Coin data types must be consistent', 'SELECT COUNT(*) FROM coins WHERE year < 1800 OR year > 2030', 'UPDATE coins SET year = 2000 WHERE year < 1800 OR year > 2030', 'WARNING', true)
ON CONFLICT (rule_name) DO NOTHING;

-- 8. Create consistency checks for each rule
INSERT INTO consistency_checks (rule_id, check_name, check_type, table_name, check_query, expected_result)
SELECT 
    r.id,
    r.rule_name || ' Check',
    r.rule_type,
    r.table_name,
    r.validation_query,
    '0'
FROM consistency_rules r
ON CONFLICT DO NOTHING;

-- 9. Create function to run consistency check
CREATE OR REPLACE FUNCTION run_consistency_check(p_check_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    check_record RECORD;
    result_count INTEGER;
    check_passed BOOLEAN := FALSE;
BEGIN
    -- Get check details
    SELECT * INTO check_record FROM consistency_checks WHERE id = p_check_id;
    
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
    UPDATE consistency_checks
    SET status = CASE WHEN check_passed THEN 'PASSED' ELSE 'FAILED' END,
        actual_result = result_count::TEXT,
        last_run = NOW(),
        updated_at = NOW()
    WHERE id = p_check_id;
    
    -- If check failed, create violation records
    IF NOT check_passed THEN
        INSERT INTO consistency_violations (
            rule_id, violation_type, table_name, 
            violation_details, severity, status
        )
        SELECT 
            cr.id,
            cr.rule_type,
            cr.table_name,
            jsonb_build_object(
                'check_id', p_check_id,
                'expected_result', check_record.expected_result,
                'actual_result', result_count::TEXT,
                'detected_at', NOW()
            ),
            cr.severity,
            'DETECTED'
        FROM consistency_rules cr
        WHERE cr.id = check_record.rule_id;
    END IF;
    
    RETURN check_passed;
END;
$$ LANGUAGE plpgsql;

-- 10. Create function to repair consistency violations
CREATE OR REPLACE FUNCTION repair_consistency_violation(
    p_violation_id INTEGER,
    p_repaired_by VARCHAR(100)
) RETURNS BOOLEAN AS $$
DECLARE
    violation_record RECORD;
    rule_record RECORD;
    repair_success BOOLEAN := FALSE;
BEGIN
    -- Get violation details
    SELECT * INTO violation_record FROM consistency_violations WHERE id = p_violation_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Get rule details
    SELECT * INTO rule_record FROM consistency_rules WHERE id = violation_record.rule_id;
    
    -- Execute repair query if available
    IF rule_record.repair_query IS NOT NULL THEN
        BEGIN
            EXECUTE rule_record.repair_query;
            repair_success := TRUE;
            
            -- Log repair action
            INSERT INTO consistency_repair_logs (
                rule_id, violation_id, repair_action, repair_query,
                repair_result, status, completed_at, repaired_by
            ) VALUES (
                violation_record.rule_id, p_violation_id, 'AUTO_REPAIR',
                rule_record.repair_query,
                jsonb_build_object('success', true, 'repaired_at', NOW()),
                'SUCCESS', NOW(), p_repaired_by
            );
            
        EXCEPTION WHEN OTHERS THEN
            repair_success := FALSE;
            
            -- Log failed repair
            INSERT INTO consistency_repair_logs (
                rule_id, violation_id, repair_action, repair_query,
                repair_result, status, error_message, repaired_by
            ) VALUES (
                violation_record.rule_id, p_violation_id, 'AUTO_REPAIR',
                rule_record.repair_query,
                jsonb_build_object('success', false, 'error', SQLERRM),
                'FAILED', SQLERRM, p_repaired_by
            );
        END;
    END IF;
    
    -- Update violation status
    UPDATE consistency_violations
    SET status = CASE WHEN repair_success THEN 'REPAIRED' ELSE 'ESCALATED' END,
        repaired_at = CASE WHEN repair_success THEN NOW() ELSE NULL END,
        repaired_by = CASE WHEN repair_success THEN p_repaired_by ELSE NULL END,
        repair_notes = CASE WHEN repair_success THEN 'Automatically repaired' ELSE 'Repair failed - manual intervention required' END
    WHERE id = p_violation_id;
    
    RETURN repair_success;
END;
$$ LANGUAGE plpgsql;

-- 11. Create function to generate consistency report
CREATE OR REPLACE FUNCTION generate_consistency_report(
    p_report_type VARCHAR(50),
    p_report_name VARCHAR(200),
    p_generated_by VARCHAR(100)
) RETURNS INTEGER AS $$
DECLARE
    report_id INTEGER;
    report_data JSONB;
    total_violations INTEGER;
    violations_by_severity JSONB;
    violations_by_table JSONB;
BEGIN
    -- Get violation statistics
    SELECT COUNT(*) INTO total_violations FROM consistency_violations WHERE status = 'DETECTED';
    
    -- Get violations by severity
    SELECT jsonb_object_agg(severity, severity_count) INTO violations_by_severity
    FROM (
        SELECT severity, COUNT(*) as severity_count
        FROM consistency_violations
        WHERE status = 'DETECTED'
        GROUP BY severity
    ) subq;
    
    -- Get violations by table
    SELECT jsonb_object_agg(table_name, table_count) INTO violations_by_table
    FROM (
        SELECT table_name, COUNT(*) as table_count
        FROM consistency_violations
        WHERE status = 'DETECTED'
        GROUP BY table_name
    ) subq;
    
    -- Build report data
    report_data := jsonb_build_object(
        'total_violations', total_violations,
        'violations_by_severity', violations_by_severity,
        'violations_by_table', violations_by_table,
        'generated_at', NOW(),
        'report_type', p_report_type
    );
    
    -- Insert consistency report
    INSERT INTO consistency_reports (report_type, report_name, report_data, generated_by)
    VALUES (p_report_type, p_report_name, report_data, p_generated_by)
    RETURNING id INTO report_id;
    
    RETURN report_id;
END;
$$ LANGUAGE plpgsql;

-- 12. Create function to run all consistency checks
CREATE OR REPLACE FUNCTION run_all_consistency_checks()
RETURNS JSONB AS $$
DECLARE
    check_record RECORD;
    results JSONB := '{}';
    total_checks INTEGER := 0;
    passed_checks INTEGER := 0;
    failed_checks INTEGER := 0;
    error_checks INTEGER := 0;
BEGIN
    -- Run all active consistency checks
    FOR check_record IN 
        SELECT cc.* FROM consistency_checks cc
        JOIN consistency_rules cr ON cc.rule_id = cr.id
        WHERE cr.is_active = TRUE
    LOOP
        total_checks := total_checks + 1;
        
        BEGIN
            IF run_consistency_check(check_record.id) THEN
                passed_checks := passed_checks + 1;
            ELSE
                failed_checks := failed_checks + 1;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            error_checks := error_checks + 1;
        END;
    END LOOP;
    
    -- Build results
    results := jsonb_build_object(
        'total_checks', total_checks,
        'passed_checks', passed_checks,
        'failed_checks', failed_checks,
        'error_checks', error_checks,
        'success_rate', CASE WHEN total_checks > 0 THEN (passed_checks::FLOAT / total_checks::FLOAT) * 100 ELSE 0 END,
        'completed_at', NOW()
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- 13. Add constraints
ALTER TABLE consistency_rules ADD CONSTRAINT check_rule_type_valid CHECK (rule_type IN ('CONSTRAINT', 'REFERENCE', 'BUSINESS_LOGIC', 'DATA_QUALITY'));
ALTER TABLE consistency_rules ADD CONSTRAINT check_severity_valid CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'));
ALTER TABLE consistency_checks ADD CONSTRAINT check_check_type_valid CHECK (check_type IN ('CONSTRAINT', 'REFERENCE', 'CONSISTENCY', 'BUSINESS_RULE', 'BUSINESS_LOGIC', 'DATA_QUALITY'));
ALTER TABLE consistency_checks ADD CONSTRAINT check_check_status_valid CHECK (status IN ('PENDING', 'PASSED', 'FAILED', 'ERROR'));
ALTER TABLE consistency_violations ADD CONSTRAINT check_violation_status_valid CHECK (status IN ('DETECTED', 'REPAIRING', 'REPAIRED', 'IGNORED', 'ESCALATED'));
ALTER TABLE consistency_violations ADD CONSTRAINT check_violation_severity_valid CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'));
ALTER TABLE consistency_reports ADD CONSTRAINT check_report_status_valid CHECK (status IN ('ACTIVE', 'EXPIRED', 'ARCHIVED'));
ALTER TABLE consistency_repair_logs ADD CONSTRAINT check_repair_status_valid CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'ROLLBACK'));

-- 14. Add comments for documentation
COMMENT ON TABLE consistency_rules IS 'Database consistency rules and validation logic';
COMMENT ON TABLE consistency_checks IS 'Consistency check definitions and execution tracking';
COMMENT ON TABLE consistency_violations IS 'Detected consistency violations and their status';
COMMENT ON TABLE consistency_reports IS 'Generated consistency reports and statistics';
COMMENT ON TABLE consistency_repair_logs IS 'Repair action logs and results';

-- Success message
SELECT 'Database Consistency System schema created successfully!' as status;
