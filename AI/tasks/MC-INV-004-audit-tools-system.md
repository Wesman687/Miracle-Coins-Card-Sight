# MC-INV-004: Comprehensive Audit Tools Implementation

## Overview
Implement comprehensive audit tools and tracking system for inventory management, including change tracking, compliance reporting, and data integrity monitoring.

## Requirements Analysis

### Current State
- Basic audit logging exists in `audit_logs` table
- Limited audit capabilities for inventory operations
- No compliance reporting or data integrity monitoring

### Key Requirements

#### 1. **Change Tracking**
- Track all inventory movements and changes
- Maintain complete audit trail for compliance
- Support rollback operations
- Track user actions and system changes

#### 2. **Compliance Reporting**
- Generate compliance reports for inventory
- Track inventory accuracy and discrepancies
- Monitor data integrity and consistency
- Support regulatory requirements

#### 3. **Data Integrity Monitoring**
- Detect and report data inconsistencies
- Monitor database integrity
- Track system performance and errors
- Alert on suspicious activities

## Technical Implementation

### Database Schema Updates

#### 1. **Enhanced Audit System**
```sql
-- Enhanced audit logs table
CREATE TABLE audit_logs_enhanced (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    operation_type VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE', 'SELECT'
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    operation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation_duration_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB
);

-- Audit configuration table
CREATE TABLE audit_config (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    audit_enabled BOOLEAN DEFAULT TRUE,
    audit_fields TEXT[],
    exclude_fields TEXT[],
    retention_days INTEGER DEFAULT 2555, -- 7 years
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data integrity checks table
CREATE TABLE data_integrity_checks (
    id SERIAL PRIMARY KEY,
    check_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL, -- 'constraint', 'consistency', 'performance'
    description TEXT,
    query TEXT NOT NULL,
    expected_result TEXT,
    actual_result TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'passed', 'failed', 'error'
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance reports table
CREATE TABLE compliance_reports (
    id SERIAL PRIMARY KEY,
    report_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- 'inventory', 'financial', 'operational'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    generated_by INTEGER REFERENCES users(id),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_data JSONB,
    file_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'generated' -- 'generated', 'approved', 'archived'
);
```

#### 2. **Audit Triggers**
```sql
-- Function to create audit triggers
CREATE OR REPLACE FUNCTION create_audit_trigger(table_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        CREATE TRIGGER %I_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON %I
        FOR EACH ROW
        EXECUTE FUNCTION audit_trigger_function();
    ', table_name, table_name);
END;
$$ LANGUAGE plpgsql;

-- Audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_fields TEXT[];
BEGIN
    -- Get old and new data
    IF TG_OP = 'DELETE' THEN
        old_data = to_jsonb(OLD);
        new_data = NULL;
    ELSIF TG_OP = 'INSERT' THEN
        old_data = NULL;
        new_data = to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        old_data = to_jsonb(OLD);
        new_data = to_jsonb(NEW);
        
        -- Find changed fields
        SELECT array_agg(key) INTO changed_fields
        FROM jsonb_each(old_data)
        WHERE old_data->>key IS DISTINCT FROM new_data->>key;
    END IF;
    
    -- Insert audit record
    INSERT INTO audit_logs_enhanced (
        table_name,
        record_id,
        operation_type,
        old_values,
        new_values,
        changed_fields,
        user_id,
        operation_timestamp
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        old_data,
        new_data,
        changed_fields,
        current_setting('app.current_user_id', true)::INTEGER,
        CURRENT_TIMESTAMP
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

### Backend Implementation

#### 1. **Audit Service**
```python
# backend/app/services/audit_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, timedelta
import json
from ..models import AuditLogEnhanced, DataIntegrityCheck, ComplianceReport
from ..schemas.audit import AuditLogResponse, ComplianceReportRequest

class AuditService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_audit_trail(
        self, 
        table_name: str, 
        record_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLogResponse]:
        """Get complete audit trail for a specific record"""
        
        query = self.db.query(AuditLogEnhanced).filter(
            AuditLogEnhanced.table_name == table_name,
            AuditLogEnhanced.record_id == record_id
        )
        
        if start_date:
            query = query.filter(AuditLogEnhanced.operation_timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLogEnhanced.operation_timestamp <= end_date)
        
        return query.order_by(AuditLogEnhanced.operation_timestamp.desc()).all()
    
    def get_user_activity(
        self, 
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLogResponse]:
        """Get all activity for a specific user"""
        
        query = self.db.query(AuditLogEnhanced).filter(
            AuditLogEnhanced.user_id == user_id
        )
        
        if start_date:
            query = query.filter(AuditLogEnhanced.operation_timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLogEnhanced.operation_timestamp <= end_date)
        
        return query.order_by(AuditLogEnhanced.operation_timestamp.desc()).all()
    
    def run_data_integrity_checks(self) -> Dict[str, Any]:
        """Run all data integrity checks"""
        
        checks = self.db.query(DataIntegrityCheck).filter(
            DataIntegrityCheck.status == 'pending'
        ).all()
        
        results = {
            'total_checks': len(checks),
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'details': []
        }
        
        for check in checks:
            try:
                # Execute the check query
                result = self.db.execute(text(check.query)).fetchone()
                
                if result and len(result) > 0:
                    actual_result = str(result[0])
                    
                    if actual_result == check.expected_result:
                        check.status = 'passed'
                        results['passed'] += 1
                    else:
                        check.status = 'failed'
                        results['failed'] += 1
                    
                    check.actual_result = actual_result
                else:
                    check.status = 'failed'
                    results['failed'] += 1
                
                check.last_run = datetime.utcnow()
                check.next_run = datetime.utcnow() + timedelta(days=1)
                
                results['details'].append({
                    'check_name': check.check_name,
                    'status': check.status,
                    'expected': check.expected_result,
                    'actual': check.actual_result
                })
                
            except Exception as e:
                check.status = 'error'
                check.actual_result = str(e)
                results['errors'] += 1
                
                results['details'].append({
                    'check_name': check.check_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        self.db.commit()
        return results
    
    def generate_compliance_report(
        self, 
        request: ComplianceReportRequest
    ) -> ComplianceReport:
        """Generate compliance report"""
        
        # Generate report data based on type
        if request.report_type == 'inventory':
            report_data = self._generate_inventory_compliance_report(
                request.period_start, 
                request.period_end
            )
        elif request.report_type == 'financial':
            report_data = self._generate_financial_compliance_report(
                request.period_start, 
                request.period_end
            )
        else:
            report_data = self._generate_operational_compliance_report(
                request.period_start, 
                request.period_end
            )
        
        # Create compliance report record
        report = ComplianceReport(
            report_name=request.report_name,
            report_type=request.report_type,
            period_start=request.period_start,
            period_end=request.period_end,
            generated_by=request.generated_by,
            report_data=report_data
        )
        
        self.db.add(report)
        self.db.commit()
        
        return report
    
    def _generate_inventory_compliance_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate inventory compliance report"""
        
        # Get inventory movements
        movements = self.db.execute(text("""
            SELECT 
                COUNT(*) as total_movements,
                COUNT(DISTINCT coin_id) as unique_coins,
                SUM(CASE WHEN movement_type = 'in' THEN quantity ELSE 0 END) as total_in,
                SUM(CASE WHEN movement_type = 'out' THEN quantity ELSE 0 END) as total_out
            FROM inventory_movements 
            WHERE created_at BETWEEN :start_date AND :end_date
        """), {
            'start_date': start_date,
            'end_date': end_date
        }).fetchone()
        
        # Get audit trail summary
        audit_summary = self.db.execute(text("""
            SELECT 
                COUNT(*) as total_audit_records,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(CASE WHEN success = false THEN 1 END) as failed_operations
            FROM audit_logs_enhanced 
            WHERE operation_timestamp BETWEEN :start_date AND :end_date
            AND table_name IN ('coins', 'inventory_items', 'inventory_movements')
        """), {
            'start_date': start_date,
            'end_date': end_date
        }).fetchone()
        
        return {
            'inventory_movements': {
                'total_movements': movements.total_movements,
                'unique_coins': movements.unique_coins,
                'total_in': movements.total_in,
                'total_out': movements.total_out
            },
            'audit_summary': {
                'total_audit_records': audit_summary.total_audit_records,
                'unique_users': audit_summary.unique_users,
                'failed_operations': audit_summary.failed_operations
            },
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_financial_compliance_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate financial compliance report"""
        
        # Get financial data
        financial_data = self.db.execute(text("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(bought_price) as total_cost,
                SUM(sold_price) as total_revenue,
                SUM(sold_price - bought_price) as total_profit
            FROM coins 
            WHERE created_at BETWEEN :start_date AND :end_date
            AND sold_price IS NOT NULL
        """), {
            'start_date': start_date,
            'end_date': end_date
        }).fetchone()
        
        return {
            'financial_summary': {
                'total_transactions': financial_data.total_transactions,
                'total_cost': float(financial_data.total_cost) if financial_data.total_cost else 0,
                'total_revenue': float(financial_data.total_revenue) if financial_data.total_revenue else 0,
                'total_profit': float(financial_data.total_profit) if financial_data.total_profit else 0
            },
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_operational_compliance_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate operational compliance report"""
        
        # Get operational metrics
        operational_data = self.db.execute(text("""
            SELECT 
                COUNT(*) as total_operations,
                AVG(operation_duration_ms) as avg_duration_ms,
                COUNT(CASE WHEN success = false THEN 1 END) as failed_operations,
                COUNT(DISTINCT user_id) as active_users
            FROM audit_logs_enhanced 
            WHERE operation_timestamp BETWEEN :start_date AND :end_date
        """), {
            'start_date': start_date,
            'end_date': end_date
        }).fetchone()
        
        return {
            'operational_summary': {
                'total_operations': operational_data.total_operations,
                'avg_duration_ms': float(operational_data.avg_duration_ms) if operational_data.avg_duration_ms else 0,
                'failed_operations': operational_data.failed_operations,
                'active_users': operational_data.active_users
            },
            'generated_at': datetime.utcnow().isoformat()
        }
```

#### 2. **Audit Router**
```python
# backend/app/routers/audit.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import get_db
from ..services.audit_service import AuditService
from ..schemas.audit import (
    AuditLogResponse, 
    ComplianceReportRequest, 
    ComplianceReportResponse,
    DataIntegrityCheckResponse
)

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/trail/{table_name}/{record_id}", response_model=List[AuditLogResponse])
async def get_audit_trail(
    table_name: str,
    record_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get audit trail for a specific record"""
    service = AuditService(db)
    return service.get_audit_trail(table_name, record_id, start_date, end_date)

@router.get("/user/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all activity for a specific user"""
    service = AuditService(db)
    return service.get_user_activity(user_id, start_date, end_date)

@router.post("/compliance-report", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db: Session = Depends(get_db)
):
    """Generate compliance report"""
    service = AuditService(db)
    return service.generate_compliance_report(request)

@router.get("/data-integrity/run")
async def run_data_integrity_checks(
    db: Session = Depends(get_db)
):
    """Run data integrity checks"""
    service = AuditService(db)
    return service.run_data_integrity_checks()

@router.get("/data-integrity/checks", response_model=List[DataIntegrityCheckResponse])
async def get_data_integrity_checks(
    db: Session = Depends(get_db)
):
    """Get all data integrity checks"""
    service = AuditService(db)
    return service.get_data_integrity_checks()
```

### Frontend Implementation

#### 1. **Audit Dashboard Component**
```typescript
// frontend/components/AuditDashboard.tsx
import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { AuditService } from '../lib/api';

interface AuditDashboardProps {
  tableName?: string;
  recordId?: number;
}

export const AuditDashboard: React.FC<AuditDashboardProps> = ({ 
  tableName, 
  recordId 
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState('7d');
  const [selectedUser, setSelectedUser] = useState<number | null>(null);
  
  const { data: auditTrail, isLoading } = useQuery({
    queryKey: ['audit-trail', tableName, recordId, selectedPeriod],
    queryFn: () => AuditService.getAuditTrail(
      tableName!, 
      recordId!, 
      getDateRange(selectedPeriod)
    ),
    enabled: !!tableName && !!recordId
  });
  
  const { data: userActivity } = useQuery({
    queryKey: ['user-activity', selectedUser, selectedPeriod],
    queryFn: () => AuditService.getUserActivity(
      selectedUser!, 
      getDateRange(selectedPeriod)
    ),
    enabled: !!selectedUser
  });
  
  const runIntegrityChecks = useMutation({
    mutationFn: AuditService.runDataIntegrityChecks,
    onSuccess: (data) => {
      // Show results
      console.log('Integrity checks completed:', data);
    }
  });
  
  const generateComplianceReport = useMutation({
    mutationFn: AuditService.generateComplianceReport,
    onSuccess: (data) => {
      // Show report
      console.log('Compliance report generated:', data);
    }
  });
  
  const getDateRange = (period: string) => {
    const now = new Date();
    const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
    return {
      start: new Date(now.getTime() - days * 24 * 60 * 60 * 1000),
      end: now
    };
  };
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Audit Dashboard</h1>
      
      {/* Controls */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Time Period</label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="w-full p-2 border rounded"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">User</label>
            <select
              value={selectedUser || ''}
              onChange={(e) => setSelectedUser(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full p-2 border rounded"
            >
              <option value="">All Users</option>
              {/* Add user options */}
            </select>
          </div>
          
          <div className="flex items-end space-x-2">
            <button
              onClick={() => runIntegrityChecks.mutate()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Run Integrity Checks
            </button>
            <button
              onClick={() => generateComplianceReport.mutate({
                report_name: `Compliance Report - ${selectedPeriod}`,
                report_type: 'inventory',
                period_start: getDateRange(selectedPeriod).start,
                period_end: getDateRange(selectedPeriod).end,
                generated_by: 1 // Current user
              })}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Generate Report
            </button>
          </div>
        </div>
      </div>
      
      {/* Audit Trail */}
      {auditTrail && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Audit Trail</h2>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">Timestamp</th>
                  <th className="border border-gray-300 p-2">Operation</th>
                  <th className="border border-gray-300 p-2">User</th>
                  <th className="border border-gray-300 p-2">Changes</th>
                  <th className="border border-gray-300 p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {auditTrail.map((log) => (
                  <tr key={log.id}>
                    <td className="border border-gray-300 p-2">
                      {new Date(log.operation_timestamp).toLocaleString()}
                    </td>
                    <td className="border border-gray-300 p-2">
                      {log.operation_type}
                    </td>
                    <td className="border border-gray-300 p-2">
                      {log.user_email || `User ${log.user_id}`}
                    </td>
                    <td className="border border-gray-300 p-2">
                      {log.changed_fields?.join(', ') || 'N/A'}
                    </td>
                    <td className="border border-gray-300 p-2">
                      <span className={`px-2 py-1 rounded text-sm ${
                        log.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.success ? 'Success' : 'Failed'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* User Activity */}
      {userActivity && (
        <div>
          <h2 className="text-xl font-semibold mb-4">User Activity</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {userActivity.map((activity) => (
              <div key={activity.id} className="p-4 border rounded-lg">
                <h3 className="font-semibold">{activity.table_name}</h3>
                <p className="text-sm text-gray-600">
                  {activity.operation_type} - {activity.record_id}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(activity.operation_timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

## Implementation Plan

### Phase 1: Core Audit System (Week 1)
- [ ] Create enhanced audit database schema
- [ ] Implement audit triggers for all tables
- [ ] Create audit service and API endpoints
- [ ] Implement basic audit trail functionality

### Phase 2: Data Integrity Monitoring (Week 2)
- [ ] Create data integrity checks system
- [ ] Implement automated integrity monitoring
- [ ] Add integrity check scheduling
- [ ] Create integrity check reports

### Phase 3: Compliance Reporting (Week 3)
- [ ] Implement compliance report generation
- [ ] Create report templates and formats
- [ ] Add report scheduling and automation
- [ ] Implement report archiving

### Phase 4: Frontend Integration (Week 4)
- [ ] Create audit dashboard components
- [ ] Implement audit trail visualization
- [ ] Add compliance report viewer
- [ ] Create audit management interface

## Success Criteria
- [ ] Complete audit trail for all inventory operations
- [ ] Automated data integrity monitoring
- [ ] Compliance report generation
- [ ] User activity tracking and reporting
- [ ] Performance optimized audit system
- [ ] Regulatory compliance support

## Questions for Owner

1. **Audit Retention**: How long should audit logs be retained? (Suggested: 7 years for compliance)

2. **Data Integrity Checks**: What specific integrity checks are most important? (Foreign keys, data consistency, performance)

3. **Compliance Requirements**: Are there specific regulatory requirements to meet? (SOX, GDPR, industry-specific)

4. **Audit Access**: Who should have access to audit logs? (Admin only, managers, all users)

5. **Report Formats**: What report formats are needed? (PDF, Excel, CSV, JSON)

6. **Audit Alerts**: Should we implement alerts for suspicious activities? (Failed operations, unusual patterns)

7. **Performance Impact**: What's the acceptable performance impact for audit logging? (Minimal, moderate, comprehensive)

8. **Audit Export**: Should audit logs be exportable for external analysis?

## Next Steps
1. Review and approve the audit system design
2. Implement Phase 1 core functionality
3. Test with sample data
4. Iterate based on feedback
5. Implement remaining phases

---

**Priority**: High
**Estimated Time**: 4 weeks
**Dependencies**: None
**Status**: Ready for implementation
