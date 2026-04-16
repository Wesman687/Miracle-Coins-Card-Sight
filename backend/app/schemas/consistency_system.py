"""
Database Consistency System Schemas
Automated validation and repair mechanisms
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RuleType(str, Enum):
    CONSTRAINT = "CONSTRAINT"
    REFERENCE = "REFERENCE"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    DATA_QUALITY = "DATA_QUALITY"

class CheckType(str, Enum):
    CONSTRAINT = "CONSTRAINT"
    REFERENCE = "REFERENCE"
    CONSISTENCY = "CONSISTENCY"
    BUSINESS_RULE = "BUSINESS_RULE"

class SeverityLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class CheckStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"

class ViolationStatus(str, Enum):
    DETECTED = "DETECTED"
    REPAIRING = "REPAIRING"
    REPAIRED = "REPAIRED"
    IGNORED = "IGNORED"
    ESCALATED = "ESCALATED"

class ReportStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"

class RepairStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLBACK = "ROLLBACK"

# Consistency Rule Schemas
class ConsistencyRuleBase(BaseModel):
    rule_name: str = Field(..., max_length=100)
    rule_type: RuleType
    table_name: str = Field(..., max_length=100)
    column_name: Optional[str] = Field(None, max_length=100)
    rule_description: str
    validation_query: str
    repair_query: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.WARNING
    is_active: bool = True
    auto_repair: bool = False

class ConsistencyRuleCreate(ConsistencyRuleBase):
    pass

class ConsistencyRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=100)
    rule_type: Optional[RuleType] = None
    table_name: Optional[str] = Field(None, max_length=100)
    column_name: Optional[str] = Field(None, max_length=100)
    rule_description: Optional[str] = None
    validation_query: Optional[str] = None
    repair_query: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    is_active: Optional[bool] = None
    auto_repair: Optional[bool] = None

class ConsistencyRuleResponse(ConsistencyRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Consistency Check Schemas
class ConsistencyCheckBase(BaseModel):
    rule_id: int
    check_name: str = Field(..., max_length=100)
    check_type: CheckType
    table_name: Optional[str] = Field(None, max_length=100)
    column_name: Optional[str] = Field(None, max_length=100)
    check_query: Optional[str] = None
    expected_result: Optional[str] = None

class ConsistencyCheckCreate(ConsistencyCheckBase):
    pass

class ConsistencyCheckUpdate(BaseModel):
    actual_result: Optional[str] = None
    status: Optional[CheckStatus] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class ConsistencyCheckResponse(ConsistencyCheckBase):
    id: int
    actual_result: Optional[str] = None
    status: CheckStatus
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Consistency Violation Schemas
class ConsistencyViolationBase(BaseModel):
    rule_id: int
    violation_type: str = Field(..., max_length=50)
    table_name: str = Field(..., max_length=100)
    record_id: Optional[str] = Field(None, max_length=100)
    column_name: Optional[str] = Field(None, max_length=100)
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    violation_details: Optional[Dict[str, Any]] = None
    severity: SeverityLevel = SeverityLevel.WARNING
    status: ViolationStatus = ViolationStatus.DETECTED

class ConsistencyViolationCreate(ConsistencyViolationBase):
    pass

class ConsistencyViolationUpdate(BaseModel):
    status: Optional[ViolationStatus] = None
    repaired_at: Optional[datetime] = None
    repaired_by: Optional[str] = Field(None, max_length=100)
    repair_notes: Optional[str] = None

class ConsistencyViolationResponse(ConsistencyViolationBase):
    id: int
    detected_at: datetime
    repaired_at: Optional[datetime] = None
    repaired_by: Optional[str] = None
    repair_notes: Optional[str] = None
    
    class Config:
        from_attributes = True

# Consistency Report Schemas
class ConsistencyReportBase(BaseModel):
    report_type: str = Field(..., max_length=50)
    report_name: str = Field(..., max_length=200)
    report_data: Dict[str, Any]
    total_violations: int = 0
    violations_by_severity: Optional[Dict[str, Any]] = None
    violations_by_table: Optional[Dict[str, Any]] = None
    generated_by: Optional[str] = Field(None, max_length=100)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: ReportStatus = ReportStatus.ACTIVE

class ConsistencyReportCreate(ConsistencyReportBase):
    pass

class ConsistencyReportResponse(ConsistencyReportBase):
    id: int
    generated_at: datetime
    
    class Config:
        from_attributes = True

# Consistency Repair Log Schemas
class ConsistencyRepairLogBase(BaseModel):
    rule_id: int
    violation_id: int
    repair_action: str = Field(..., max_length=100)
    repair_query: Optional[str] = None
    repair_result: Optional[Dict[str, Any]] = None
    status: RepairStatus = RepairStatus.PENDING
    error_message: Optional[str] = None
    repaired_by: Optional[str] = Field(None, max_length=100)

class ConsistencyRepairLogCreate(ConsistencyRepairLogBase):
    pass

class ConsistencyRepairLogResponse(ConsistencyRepairLogBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Dashboard and Statistics Schemas
class ConsistencyDashboardStats(BaseModel):
    total_rules: int
    active_rules: int
    total_checks: int
    passed_checks: int
    failed_checks: int
    total_violations: int
    violations_by_severity: Dict[str, int]
    violations_by_table: Dict[str, int]
    recent_violations: List[Dict[str, Any]]
    recent_repairs: List[Dict[str, Any]]

class ConsistencyCheckRequest(BaseModel):
    check_id: int
    force_run: bool = False

class ConsistencyRepairRequest(BaseModel):
    violation_id: int
    repaired_by: str = Field(..., max_length=100)
    repair_notes: Optional[str] = None

class ConsistencyReportRequest(BaseModel):
    report_type: str = Field(..., max_length=50)
    report_name: str = Field(..., max_length=200)
    generated_by: Optional[str] = Field(None, max_length=100)
    include_violations: bool = True
    include_repairs: bool = True

class ConsistencyRuleTestRequest(BaseModel):
    rule_id: int
    test_data: Optional[Dict[str, Any]] = None
