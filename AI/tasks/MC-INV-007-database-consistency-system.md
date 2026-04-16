# MC-INV-007: Database Consistency and Data Validation

## Overview
Implement comprehensive database consistency checks, data validation, and integrity monitoring to ensure data quality and prevent inconsistencies across the inventory system.

## Requirements Analysis

### Current State
- Basic database schema exists
- Limited data validation
- No consistency monitoring
- Potential data inconsistencies

### Key Requirements

#### 1. **Data Validation**
- Validate all data before database operations
- Ensure data integrity constraints
- Handle validation errors gracefully
- Provide clear error messages

#### 2. **Consistency Monitoring**
- Monitor database consistency in real-time
- Detect and report inconsistencies
- Automatically fix minor inconsistencies
- Alert on major consistency issues

#### 3. **Data Integrity**
- Ensure referential integrity
- Validate business rules
- Check data completeness
- Monitor data quality metrics

## Technical Implementation

### Database Schema Updates

#### 1. **Data Validation Tables**
```sql
-- Data validation rules table
CREATE TABLE data_validation_rules (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'required', 'format', 'range', 'reference', 'custom'
    rule_definition JSONB NOT NULL,
    error_message TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data validation results table
CREATE TABLE data_validation_results (
    id SERIAL PRIMARY KEY,
    validation_rule_id INTEGER REFERENCES data_validation_rules(id),
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    validation_status VARCHAR(20) NOT NULL, -- 'passed', 'failed', 'warning'
    validation_message TEXT,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_by INTEGER REFERENCES users(id)
);

-- Data consistency checks table
CREATE TABLE data_consistency_checks (
    id SERIAL PRIMARY KEY,
    check_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL, -- 'referential', 'business_rule', 'data_quality', 'performance'
    check_query TEXT NOT NULL,
    expected_result TEXT,
    actual_result TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'passed', 'failed', 'error'
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    run_frequency_minutes INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data quality metrics table
CREATE TABLE data_quality_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'completeness', 'accuracy', 'consistency', 'timeliness'
    table_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    target_value DECIMAL(10,4),
    measurement_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default validation rules
INSERT INTO data_validation_rules (table_name, column_name, rule_type, rule_definition, error_message) VALUES
('coins', 'sku', 'required', '{"required": true}', 'SKU is required'),
('coins', 'sku', 'format', '{"pattern": "^[A-Z0-9-]+$", "min_length": 3, "max_length": 50}', 'SKU must be 3-50 characters, alphanumeric with hyphens'),
('coins', 'name', 'required', '{"required": true}', 'Coin name is required'),
('coins', 'year', 'range', '{"min": 1800, "max": 2030}', 'Year must be between 1800 and 2030'),
('coins', 'bought_price', 'range', '{"min": 0, "max": 1000000}', 'Bought price must be between 0 and 1,000,000'),
('inventory_items', 'quantity', 'range', '{"min": 0, "max": 10000}', 'Quantity must be between 0 and 10,000'),
('inventory_items', 'coin_id', 'reference', '{"table": "coins", "column": "id"}', 'Coin ID must reference existing coin'),
('inventory_items', 'location_id', 'reference', '{"table": "locations", "column": "id"}', 'Location ID must reference existing location');

-- Insert default consistency checks
INSERT INTO data_consistency_checks (check_name, check_type, check_query, expected_result) VALUES
('Orphaned Inventory Items', 'referential', 'SELECT COUNT(*) FROM inventory_items WHERE coin_id NOT IN (SELECT id FROM coins)', '0'),
('Orphaned Inventory Movements', 'referential', 'SELECT COUNT(*) FROM inventory_movements WHERE coin_id NOT IN (SELECT id FROM coins)', '0'),
('Invalid Location References', 'referential', 'SELECT COUNT(*) FROM inventory_items WHERE location_id NOT IN (SELECT id FROM locations)', '0'),
('Negative Quantities', 'business_rule', 'SELECT COUNT(*) FROM inventory_items WHERE quantity < 0', '0'),
('Duplicate SKUs', 'business_rule', 'SELECT COUNT(*) FROM (SELECT sku, COUNT(*) as cnt FROM coins GROUP BY sku HAVING COUNT(*) > 1) as duplicates', '0'),
('Missing Collection References', 'referential', 'SELECT COUNT(*) FROM coins WHERE collection_id IS NOT NULL AND collection_id NOT IN (SELECT id FROM collections)', '0'),
('Invalid Price Ranges', 'business_rule', 'SELECT COUNT(*) FROM coins WHERE bought_price < 0 OR sold_price < 0', '0'),
('Orphaned Barcodes', 'referential', 'SELECT COUNT(*) FROM barcodes WHERE coin_id NOT IN (SELECT id FROM coins)', '0');
```

#### 2. **Enhanced Constraints**
```sql
-- Add additional constraints to existing tables
ALTER TABLE coins ADD CONSTRAINT check_sku_format CHECK (sku ~ '^[A-Z0-9-]+$');
ALTER TABLE coins ADD CONSTRAINT check_year_range CHECK (year >= 1800 AND year <= 2030);
ALTER TABLE coins ADD CONSTRAINT check_bought_price_positive CHECK (bought_price >= 0);
ALTER TABLE coins ADD CONSTRAINT check_sold_price_positive CHECK (sold_price IS NULL OR sold_price >= 0);

ALTER TABLE inventory_items ADD CONSTRAINT check_quantity_positive CHECK (quantity >= 0);
ALTER TABLE inventory_items ADD CONSTRAINT check_quantity_max CHECK (quantity <= 10000);

ALTER TABLE inventory_movements ADD CONSTRAINT check_movement_quantity_positive CHECK (quantity > 0);
ALTER TABLE inventory_movements ADD CONSTRAINT check_movement_dates CHECK (created_at <= updated_at);

-- Add unique constraints
ALTER TABLE coins ADD CONSTRAINT unique_sku UNIQUE (sku);
ALTER TABLE barcodes ADD CONSTRAINT unique_barcode_value UNIQUE (barcode_value);
```

### Backend Implementation

#### 1. **Data Validation Service**
```python
# backend/app/services/data_validation_service.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
from datetime import datetime
from ..models import (
    DataValidationRule, DataValidationResult, 
    DataConsistencyCheck, DataQualityMetric
)
from ..schemas.validation import ValidationResult, ConsistencyCheckResult

class DataValidationService:
    def __init__(self, db: Session):
        self.db = db
    
    def validate_record(
        self, 
        table_name: str, 
        record_data: Dict[str, Any],
        record_id: Optional[int] = None
    ) -> List[ValidationResult]:
        """Validate a single record against all applicable rules"""
        
        # Get validation rules for the table
        rules = self.db.query(DataValidationRule).filter(
            DataValidationRule.table_name == table_name,
            DataValidationRule.is_active == True
        ).all()
        
        results = []
        
        for rule in rules:
            try:
                validation_result = self._validate_field(
                    rule, 
                    record_data.get(rule.column_name),
                    record_data
                )
                
                # Store validation result
                db_result = DataValidationResult(
                    validation_rule_id=rule.id,
                    table_name=table_name,
                    record_id=record_id,
                    validation_status=validation_result.status,
                    validation_message=validation_result.message
                )
                self.db.add(db_result)
                
                results.append(validation_result)
                
            except Exception as e:
                error_result = ValidationResult(
                    field=rule.column_name,
                    status='error',
                    message=f"Validation error: {str(e)}"
                )
                results.append(error_result)
        
        self.db.commit()
        return results
    
    def _validate_field(
        self, 
        rule: DataValidationRule, 
        value: Any, 
        full_record: Dict[str, Any]
    ) -> ValidationResult:
        """Validate a single field against a rule"""
        
        rule_def = rule.rule_definition
        
        if rule.rule_type == 'required':
            if rule_def.get('required', False) and (value is None or value == ''):
                return ValidationResult(
                    field=rule.column_name,
                    status='failed',
                    message=rule.error_message
                )
        
        elif rule.rule_type == 'format':
            if value is not None and value != '':
                pattern = rule_def.get('pattern')
                if pattern and not re.match(pattern, str(value)):
                    return ValidationResult(
                        field=rule.column_name,
                        status='failed',
                        message=rule.error_message
                    )
                
                min_length = rule_def.get('min_length')
                max_length = rule_def.get('max_length')
                if min_length and len(str(value)) < min_length:
                    return ValidationResult(
                        field=rule.column_name,
                        status='failed',
                        message=f"{rule.error_message} (minimum length: {min_length})"
                    )
                if max_length and len(str(value)) > max_length:
                    return ValidationResult(
                        field=rule.column_name,
                        status='failed',
                        message=f"{rule.error_message} (maximum length: {max_length})"
                    )
        
        elif rule.rule_type == 'range':
            if value is not None:
                min_val = rule_def.get('min')
                max_val = rule_def.get('max')
                
                try:
                    num_value = float(value)
                    if min_val is not None and num_value < min_val:
                        return ValidationResult(
                            field=rule.column_name,
                            status='failed',
                            message=f"{rule.error_message} (minimum: {min_val})"
                        )
                    if max_val is not None and num_value > max_val:
                        return ValidationResult(
                            field=rule.column_name,
                            status='failed',
                            message=f"{rule.error_message} (maximum: {max_val})"
                        )
                except (ValueError, TypeError):
                    return ValidationResult(
                        field=rule.column_name,
                        status='failed',
                        message=f"{rule.error_message} (invalid number format)"
                    )
        
        elif rule.rule_type == 'reference':
            if value is not None:
                ref_table = rule_def.get('table')
                ref_column = rule_def.get('column')
                
                if ref_table and ref_column:
                    # Check if referenced record exists
                    query = f"SELECT COUNT(*) FROM {ref_table} WHERE {ref_column} = :value"
                    result = self.db.execute(text(query), {'value': value}).fetchone()
                    
                    if result[0] == 0:
                        return ValidationResult(
                            field=rule.column_name,
                            status='failed',
                            message=f"{rule.error_message} (referenced record not found)"
                        )
        
        elif rule.rule_type == 'custom':
            # Custom validation logic
            custom_function = rule_def.get('function')
            if custom_function:
                # This would require implementing custom validation functions
                pass
        
        return ValidationResult(
            field=rule.column_name,
            status='passed',
            message='Validation passed'
        )
    
    def run_consistency_checks(self) -> List[ConsistencyCheckResult]:
        """Run all active consistency checks"""
        
        checks = self.db.query(DataConsistencyCheck).filter(
            DataConsistencyCheck.is_active == True
        ).all()
        
        results = []
        
        for check in checks:
            try:
                # Execute the check query
                result = self.db.execute(text(check.check_query)).fetchone()
                
                if result and len(result) > 0:
                    actual_result = str(result[0])
                    
                    if actual_result == check.expected_result:
                        check.status = 'passed'
                        status = 'passed'
                    else:
                        check.status = 'failed'
                        status = 'failed'
                    
                    check.actual_result = actual_result
                else:
                    check.status = 'failed'
                    status = 'failed'
                
                check.last_run = datetime.utcnow()
                check.next_run = datetime.utcnow() + timedelta(minutes=check.run_frequency_minutes)
                
                results.append(ConsistencyCheckResult(
                    check_name=check.check_name,
                    check_type=check.check_type,
                    status=status,
                    expected_result=check.expected_result,
                    actual_result=check.actual_result,
                    last_run=check.last_run
                ))
                
            except Exception as e:
                check.status = 'error'
                check.actual_result = str(e)
                
                results.append(ConsistencyCheckResult(
                    check_name=check.check_name,
                    check_type=check.check_type,
                    status='error',
                    expected_result=check.expected_result,
                    actual_result=str(e),
                    last_run=datetime.utcnow()
                ))
        
        self.db.commit()
        return results
    
    def calculate_data_quality_metrics(self) -> List[DataQualityMetric]:
        """Calculate data quality metrics for all tables"""
        
        metrics = []
        tables = ['coins', 'inventory_items', 'inventory_movements', 'collections', 'barcodes']
        
        for table in tables:
            # Completeness metric
            completeness = self._calculate_completeness(table)
            if completeness is not None:
                metric = DataQualityMetric(
                    metric_name=f'{table}_completeness',
                    metric_type='completeness',
                    table_name=table,
                    metric_value=completeness,
                    target_value=0.95,  # 95% completeness target
                    measurement_date=datetime.utcnow().date()
                )
                metrics.append(metric)
                self.db.add(metric)
            
            # Consistency metric
            consistency = self._calculate_consistency(table)
            if consistency is not None:
                metric = DataQualityMetric(
                    metric_name=f'{table}_consistency',
                    metric_type='consistency',
                    table_name=table,
                    metric_value=consistency,
                    target_value=0.98,  # 98% consistency target
                    measurement_date=datetime.utcnow().date()
                )
                metrics.append(metric)
                self.db.add(metric)
        
        self.db.commit()
        return metrics
    
    def _calculate_completeness(self, table_name: str) -> Optional[float]:
        """Calculate completeness metric for a table"""
        
        try:
            # Get total records
            total_query = f"SELECT COUNT(*) FROM {table_name}"
            total_result = self.db.execute(text(total_query)).fetchone()
            total_records = total_result[0] if total_result else 0
            
            if total_records == 0:
                return None
            
            # Get records with missing required fields
            # This is a simplified example - actual implementation would check specific required fields
            missing_query = f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE sku IS NULL OR sku = '' 
                OR name IS NULL OR name = ''
            """
            missing_result = self.db.execute(text(missing_query)).fetchone()
            missing_records = missing_result[0] if missing_result else 0
            
            completeness = (total_records - missing_records) / total_records
            return completeness
            
        except Exception as e:
            print(f"Error calculating completeness for {table_name}: {e}")
            return None
    
    def _calculate_consistency(self, table_name: str) -> Optional[float]:
        """Calculate consistency metric for a table"""
        
        try:
            # Get total records
            total_query = f"SELECT COUNT(*) FROM {table_name}"
            total_result = self.db.execute(text(total_query)).fetchone()
            total_records = total_result[0] if total_result else 0
            
            if total_records == 0:
                return None
            
            # Get records with consistency issues
            # This is a simplified example - actual implementation would check specific consistency rules
            if table_name == 'coins':
                issues_query = """
                    SELECT COUNT(*) FROM coins 
                    WHERE bought_price < 0 
                    OR sold_price < 0 
                    OR year < 1800 
                    OR year > 2030
                """
            elif table_name == 'inventory_items':
                issues_query = """
                    SELECT COUNT(*) FROM inventory_items 
                    WHERE quantity < 0 
                    OR quantity > 10000
                """
            else:
                return None
            
            issues_result = self.db.execute(text(issues_query)).fetchone()
            issues_records = issues_result[0] if issues_result else 0
            
            consistency = (total_records - issues_records) / total_records
            return consistency
            
        except Exception as e:
            print(f"Error calculating consistency for {table_name}: {e}")
            return None
    
    def fix_common_issues(self) -> Dict[str, Any]:
        """Automatically fix common data issues"""
        
        fixes_applied = {
            'negative_quantities': 0,
            'invalid_years': 0,
            'missing_skus': 0,
            'duplicate_skus': 0
        }
        
        try:
            # Fix negative quantities
            fix_query = "UPDATE inventory_items SET quantity = 0 WHERE quantity < 0"
            result = self.db.execute(text(fix_query))
            fixes_applied['negative_quantities'] = result.rowcount
            
            # Fix invalid years
            fix_query = "UPDATE coins SET year = 1900 WHERE year < 1800 OR year > 2030"
            result = self.db.execute(text(fix_query))
            fixes_applied['invalid_years'] = result.rowcount
            
            # Fix missing SKUs
            fix_query = """
                UPDATE coins 
                SET sku = 'UNKNOWN-' || id 
                WHERE sku IS NULL OR sku = ''
            """
            result = self.db.execute(text(fix_query))
            fixes_applied['missing_skus'] = result.rowcount
            
            # Fix duplicate SKUs
            fix_query = """
                UPDATE coins 
                SET sku = sku || '-' || id 
                WHERE sku IN (
                    SELECT sku FROM coins 
                    GROUP BY sku 
                    HAVING COUNT(*) > 1
                )
            """
            result = self.db.execute(text(fix_query))
            fixes_applied['duplicate_skus'] = result.rowcount
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            raise e
        
        return fixes_applied
```

#### 2. **Data Validation Router**
```python
# backend/app/routers/data_validation.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..services.data_validation_service import DataValidationService
from ..schemas.validation import (
    ValidationResult, 
    ConsistencyCheckResult,
    DataQualityMetricResponse
)

router = APIRouter(prefix="/api/validation", tags=["data-validation"])

@router.post("/validate/{table_name}", response_model=List[ValidationResult])
async def validate_record(
    table_name: str,
    record_data: Dict[str, Any],
    record_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Validate a record against validation rules"""
    service = DataValidationService(db)
    return service.validate_record(table_name, record_data, record_id)

@router.post("/consistency-checks", response_model=List[ConsistencyCheckResult])
async def run_consistency_checks(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run all consistency checks"""
    service = DataValidationService(db)
    
    # Run checks in background
    background_tasks.add_task(service.run_consistency_checks)
    
    return {"message": "Consistency checks started"}

@router.get("/consistency-checks/results", response_model=List[ConsistencyCheckResult])
async def get_consistency_check_results(
    db: Session = Depends(get_db)
):
    """Get latest consistency check results"""
    service = DataValidationService(db)
    return service.run_consistency_checks()

@router.post("/quality-metrics", response_model=List[DataQualityMetricResponse])
async def calculate_quality_metrics(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Calculate data quality metrics"""
    service = DataValidationService(db)
    
    # Calculate metrics in background
    background_tasks.add_task(service.calculate_data_quality_metrics)
    
    return {"message": "Quality metrics calculation started"}

@router.get("/quality-metrics/latest", response_model=List[DataQualityMetricResponse])
async def get_latest_quality_metrics(
    db: Session = Depends(get_db)
):
    """Get latest data quality metrics"""
    service = DataValidationService(db)
    return service.calculate_data_quality_metrics()

@router.post("/fix-issues")
async def fix_common_issues(
    db: Session = Depends(get_db)
):
    """Automatically fix common data issues"""
    service = DataValidationService(db)
    return service.fix_common_issues()

@router.get("/rules")
async def get_validation_rules(
    table_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get validation rules"""
    service = DataValidationService(db)
    return service.get_validation_rules(table_name)

@router.post("/rules")
async def create_validation_rule(
    rule_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new validation rule"""
    service = DataValidationService(db)
    return service.create_validation_rule(rule_data)
```

### Frontend Implementation

#### 1. **Data Validation Dashboard**
```typescript
// frontend/components/DataValidationDashboard.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataValidationService } from '../lib/api';

export const DataValidationDashboard: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<string>('coins');
  const queryClient = useQueryClient();
  
  const { data: consistencyResults, isLoading: consistencyLoading } = useQuery({
    queryKey: ['consistency-check-results'],
    queryFn: DataValidationService.getConsistencyCheckResults
  });
  
  const { data: qualityMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['quality-metrics-latest'],
    queryFn: DataValidationService.getLatestQualityMetrics
  });
  
  const { data: validationRules } = useQuery({
    queryKey: ['validation-rules', selectedTable],
    queryFn: () => DataValidationService.getValidationRules(selectedTable)
  });
  
  const runConsistencyChecks = useMutation({
    mutationFn: DataValidationService.runConsistencyChecks,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['consistency-check-results'] });
    }
  });
  
  const calculateQualityMetrics = useMutation({
    mutationFn: DataValidationService.calculateQualityMetrics,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quality-metrics-latest'] });
    }
  });
  
  const fixCommonIssues = useMutation({
    mutationFn: DataValidationService.fixCommonIssues,
    onSuccess: (data) => {
      alert(`Fixed ${Object.values(data).reduce((a, b) => a + b, 0)} issues`);
      queryClient.invalidateQueries({ queryKey: ['consistency-check-results'] });
    }
  });
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Data Validation Dashboard</h1>
      
      {/* Actions */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex space-x-4">
          <button
            onClick={() => runConsistencyChecks.mutate()}
            disabled={runConsistencyChecks.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {runConsistencyChecks.isPending ? 'Running...' : 'Run Consistency Checks'}
          </button>
          
          <button
            onClick={() => calculateQualityMetrics.mutate()}
            disabled={calculateQualityMetrics.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            {calculateQualityMetrics.isPending ? 'Calculating...' : 'Calculate Quality Metrics'}
          </button>
          
          <button
            onClick={() => fixCommonIssues.mutate()}
            disabled={fixCommonIssues.isPending}
            className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
          >
            {fixCommonIssues.isPending ? 'Fixing...' : 'Fix Common Issues'}
          </button>
        </div>
      </div>
      
      {/* Quality Metrics */}
      {qualityMetrics && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-4">Data Quality Metrics</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {qualityMetrics.map((metric) => (
              <div key={metric.metric_name} className="p-4 border rounded-lg">
                <h3 className="font-semibold">{metric.metric_name}</h3>
                <div className="mt-2">
                  <div className="flex justify-between text-sm">
                    <span>Current</span>
                    <span className="font-semibold">
                      {(metric.metric_value * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Target</span>
                    <span>{(metric.target_value * 100).toFixed(1)}%</span>
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        metric.metric_value >= metric.target_value ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${(metric.metric_value * 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Consistency Check Results */}
      {consistencyResults && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-4">Consistency Check Results</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">Check Name</th>
                  <th className="border border-gray-300 p-2">Type</th>
                  <th className="border border-gray-300 p-2">Status</th>
                  <th className="border border-gray-300 p-2">Expected</th>
                  <th className="border border-gray-300 p-2">Actual</th>
                  <th className="border border-gray-300 p-2">Last Run</th>
                </tr>
              </thead>
              <tbody>
                {consistencyResults.map((result) => (
                  <tr key={result.check_name}>
                    <td className="border border-gray-300 p-2">{result.check_name}</td>
                    <td className="border border-gray-300 p-2">{result.check_type}</td>
                    <td className="border border-gray-300 p-2">
                      <span className={`px-2 py-1 rounded text-sm ${
                        result.status === 'passed' ? 'bg-green-100 text-green-800' :
                        result.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {result.status}
                      </span>
                    </td>
                    <td className="border border-gray-300 p-2">{result.expected_result}</td>
                    <td className="border border-gray-300 p-2">{result.actual_result}</td>
                    <td className="border border-gray-300 p-2">
                      {result.last_run ? new Date(result.last_run).toLocaleString() : 'Never'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Validation Rules */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Validation Rules</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Select Table</label>
          <select
            value={selectedTable}
            onChange={(e) => setSelectedTable(e.target.value)}
            className="p-2 border rounded"
          >
            <option value="coins">Coins</option>
            <option value="inventory_items">Inventory Items</option>
            <option value="inventory_movements">Inventory Movements</option>
            <option value="collections">Collections</option>
            <option value="barcodes">Barcodes</option>
          </select>
        </div>
        
        {validationRules && (
          <div className="space-y-4">
            {validationRules.map((rule) => (
              <div key={rule.id} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{rule.column_name}</h3>
                  <span className={`px-2 py-1 rounded text-sm ${
                    rule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {rule.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 mb-2">
                  <p><strong>Type:</strong> {rule.rule_type}</p>
                  <p><strong>Message:</strong> {rule.error_message}</p>
                </div>
                
                <div className="text-xs text-gray-500">
                  <p><strong>Definition:</strong> {JSON.stringify(rule.rule_definition)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
```

## Implementation Plan

### Phase 1: Core Validation System (Week 1)
- [ ] Create validation database schema
- [ ] Implement data validation service
- [ ] Create API endpoints for validation
- [ ] Implement basic validation rules

### Phase 2: Consistency Monitoring (Week 2)
- [ ] Implement consistency check system
- [ ] Create automated consistency monitoring
- [ ] Add consistency check scheduling
- [ ] Implement consistency reporting

### Phase 3: Data Quality Metrics (Week 3)
- [ ] Implement data quality calculation
- [ ] Create quality metrics dashboard
- [ ] Add quality monitoring and alerts
- [ ] Implement quality improvement tracking

### Phase 4: Frontend Integration (Week 4)
- [ ] Create validation dashboard
- [ ] Implement validation rule management
- [ ] Add consistency check interface
- [ ] Create data quality visualization

## Success Criteria
- [ ] Comprehensive data validation for all tables
- [ ] Automated consistency monitoring
- [ ] Data quality metrics and reporting
- [ ] Automatic fixing of common issues
- [ ] Performance optimized validation system
- [ ] User-friendly validation interface

## Questions for Owner

1. **Validation Rules**: What validation rules are most important? (Required fields, format validation, range validation)

2. **Consistency Checks**: What consistency checks are critical? (Referential integrity, business rules, data quality)

3. **Quality Targets**: What are acceptable quality targets? (95% completeness, 98% consistency)

4. **Auto-Fix**: Should we automatically fix common issues? (Negative quantities, invalid years, missing SKUs)

5. **Validation Frequency**: How often should consistency checks run? (Every hour, daily, weekly)

6. **Error Handling**: How should validation errors be handled? (Block operations, log warnings, send alerts)

7. **Quality Alerts**: Should we implement alerts for quality issues? (Email notifications, dashboard alerts)

8. **Validation Performance**: What's the acceptable performance impact? (Minimal, moderate, comprehensive)

## Next Steps
1. Review and approve the validation system design
2. Implement Phase 1 core functionality
3. Test with sample data
4. Iterate based on feedback
5. Implement remaining phases

---

**Priority**: High
**Estimated Time**: 4 weeks
**Dependencies**: None
**Status**: Ready for implementation
