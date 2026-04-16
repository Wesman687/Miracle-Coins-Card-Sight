"""
Audit Tools System Models
Comprehensive audit logging, compliance reporting, and data integrity monitoring
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False)
    operation = Column(String(20), nullable=False, index=True)  # INSERT, UPDATE, DELETE
    old_values = Column(JSON)
    new_values = Column(JSON)
    changed_by = Column(String(100), index=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    session_id = Column(String(100))
    
    # Constraints
    __table_args__ = (
        CheckConstraint("operation IN ('INSERT', 'UPDATE', 'DELETE')", name='check_operation_valid'),
        Index('idx_audit_logs_table_record', 'table_name', 'record_id'),
    )

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    details = Column(JSON)
    severity = Column(String(20), default='INFO', index=True)  # INFO, WARNING, ERROR, CRITICAL
    user_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')", name='check_severity_valid'),
    )

class ComplianceReport(Base):
    __tablename__ = "compliance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False, index=True)
    report_name = Column(String(200), nullable=False)
    report_data = Column(JSON, nullable=False)
    generated_by = Column(String(100))
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_to = Column(DateTime(timezone=True))
    status = Column(String(20), default='ACTIVE', index=True)  # ACTIVE, EXPIRED, ARCHIVED
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'EXPIRED', 'ARCHIVED')", name='check_status_valid'),
    )

class DataIntegrityCheck(Base):
    __tablename__ = "data_integrity_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    check_name = Column(String(100), nullable=False, index=True)
    check_type = Column(String(50), nullable=False, index=True)  # CONSTRAINT, REFERENCE, CONSISTENCY, BUSINESS_RULE
    table_name = Column(String(100), index=True)
    column_name = Column(String(100))
    check_query = Column(Text)
    expected_result = Column(Text)
    actual_result = Column(Text)
    status = Column(String(20), default='PENDING', index=True)  # PENDING, PASSED, FAILED, ERROR
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'PASSED', 'FAILED', 'ERROR')", name='check_status_valid'),
    )

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    session_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
