"""
Audit Tools System Schemas
Comprehensive audit logging, compliance reporting, and data integrity monitoring
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OperationType(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class SeverityLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class CheckType(str, Enum):
    CONSTRAINT = "CONSTRAINT"
    REFERENCE = "REFERENCE"
    CONSISTENCY = "CONSISTENCY"
    BUSINESS_RULE = "BUSINESS_RULE"

class CheckStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"

class ReportStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"

# Audit Log Schemas
class AuditLogBase(BaseModel):
    table_name: str = Field(..., max_length=100)
    record_id: int = Field(..., ge=1)
    operation: OperationType
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_by: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = Field(None, max_length=100)

class AuditLogResponse(AuditLogBase):
    id: int
    changed_at: datetime
    
    class Config:
        from_attributes = True

# Audit Event Schemas
class AuditEventBase(BaseModel):
    event_type: str = Field(..., max_length=50)
    event_category: str = Field(..., max_length=50)
    description: str
    details: Optional[Dict[str, Any]] = None
    severity: SeverityLevel = SeverityLevel.INFO
    user_id: Optional[str] = Field(None, max_length=100)

class AuditEventCreate(AuditEventBase):
    pass

class AuditEventUpdate(BaseModel):
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class AuditEventResponse(AuditEventBase):
    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    class Config:
        from_attributes = True

# Compliance Report Schemas
class ComplianceReportBase(BaseModel):
    report_type: str = Field(..., max_length=50)
    report_name: str = Field(..., max_length=200)
    report_data: Dict[str, Any]
    generated_by: Optional[str] = Field(None, max_length=100)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: ReportStatus = ReportStatus.ACTIVE

class ComplianceReportCreate(ComplianceReportBase):
    pass

class ComplianceReportResponse(ComplianceReportBase):
    id: int
    generated_at: datetime
    
    class Config:
        from_attributes = True

# Data Integrity Check Schemas
class DataIntegrityCheckBase(BaseModel):
    check_name: str = Field(..., max_length=100)
    check_type: CheckType
    table_name: Optional[str] = Field(None, max_length=100)
    column_name: Optional[str] = Field(None, max_length=100)
    check_query: Optional[str] = None
    expected_result: Optional[str] = None

class DataIntegrityCheckCreate(DataIntegrityCheckBase):
    pass

class DataIntegrityCheckUpdate(BaseModel):
    actual_result: Optional[str] = None
    status: Optional[CheckStatus] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class DataIntegrityCheckResponse(DataIntegrityCheckBase):
    id: int
    actual_result: Optional[str] = None
    status: CheckStatus
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# User Activity Log Schemas
class UserActivityLogBase(BaseModel):
    user_id: str = Field(..., max_length=100)
    action: str = Field(..., max_length=100)
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[str] = Field(None, max_length=100)
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = Field(None, max_length=100)

class UserActivityLogCreate(UserActivityLogBase):
    pass

class UserActivityLogResponse(UserActivityLogBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard and Statistics Schemas
class AuditDashboardStats(BaseModel):
    total_audit_logs: int
    total_audit_events: int
    total_compliance_reports: int
    total_data_integrity_checks: int
    total_user_activities: int
    recent_activities: List[Dict[str, Any]]
    failed_checks: List[Dict[str, Any]]
    unresolved_events: List[Dict[str, Any]]

class AuditSearchRequest(BaseModel):
    table_name: Optional[str] = None
    operation: Optional[OperationType] = None
    changed_by: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class ComplianceReportRequest(BaseModel):
    report_type: str = Field(..., max_length=50)
    report_name: str = Field(..., max_length=200)
    generated_by: Optional[str] = Field(None, max_length=100)
    parameters: Optional[Dict[str, Any]] = None
