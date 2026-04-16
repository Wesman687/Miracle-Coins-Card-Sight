"""
Database Consistency System Models
Automated validation and repair mechanisms
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, CheckConstraint, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ConsistencyRule(Base):
    __tablename__ = "consistency_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), unique=True, nullable=False, index=True)
    rule_type = Column(String(50), nullable=False)  # CONSTRAINT, REFERENCE, BUSINESS_LOGIC, DATA_QUALITY
    table_name = Column(String(100), nullable=False, index=True)
    column_name = Column(String(100))
    rule_description = Column(Text, nullable=False)
    validation_query = Column(Text, nullable=False)
    repair_query = Column(Text)
    severity = Column(String(20), default='WARNING', index=True)  # INFO, WARNING, ERROR, CRITICAL
    is_active = Column(Boolean, default=True, index=True)
    auto_repair = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    checks = relationship("ConsistencyCheck", back_populates="rule")
    violations = relationship("ConsistencyViolation", back_populates="rule")
    repair_logs = relationship("ConsistencyRepairLog", back_populates="rule")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("rule_type IN ('CONSTRAINT', 'REFERENCE', 'BUSINESS_LOGIC', 'DATA_QUALITY')", name='check_rule_type_valid'),
        CheckConstraint("severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')", name='check_severity_valid'),
    )

class ConsistencyCheck(Base):
    __tablename__ = "consistency_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("consistency_rules.id"), nullable=False, index=True)
    check_name = Column(String(100), nullable=False)
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
    
    # Relationships
    rule = relationship("ConsistencyRule", back_populates="checks")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("check_type IN ('CONSTRAINT', 'REFERENCE', 'CONSISTENCY', 'BUSINESS_RULE')", name='check_check_type_valid'),
        CheckConstraint("status IN ('PENDING', 'PASSED', 'FAILED', 'ERROR')", name='check_check_status_valid'),
    )

class ConsistencyViolation(Base):
    __tablename__ = "consistency_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("consistency_rules.id"), nullable=False, index=True)
    violation_type = Column(String(50), nullable=False, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(100))
    column_name = Column(String(100))
    expected_value = Column(Text)
    actual_value = Column(Text)
    violation_details = Column(JSON)
    severity = Column(String(20), default='WARNING', index=True)  # INFO, WARNING, ERROR, CRITICAL
    status = Column(String(20), default='DETECTED', index=True)  # DETECTED, REPAIRING, REPAIRED, IGNORED, ESCALATED
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    repaired_at = Column(DateTime(timezone=True))
    repaired_by = Column(String(100))
    repair_notes = Column(Text)
    
    # Relationships
    rule = relationship("ConsistencyRule", back_populates="violations")
    repair_logs = relationship("ConsistencyRepairLog", back_populates="violation")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('DETECTED', 'REPAIRING', 'REPAIRED', 'IGNORED', 'ESCALATED')", name='check_violation_status_valid'),
        CheckConstraint("severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')", name='check_violation_severity_valid'),
    )

class ConsistencyReport(Base):
    __tablename__ = "consistency_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False, index=True)  # DAILY, WEEKLY, MONTHLY, ON_DEMAND
    report_name = Column(String(200), nullable=False)
    report_data = Column(JSON, nullable=False)
    total_violations = Column(Integer, default=0)
    violations_by_severity = Column(JSON)
    violations_by_table = Column(JSON)
    generated_by = Column(String(100))
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_to = Column(DateTime(timezone=True))
    status = Column(String(20), default='ACTIVE', index=True)  # ACTIVE, EXPIRED, ARCHIVED
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'EXPIRED', 'ARCHIVED')", name='check_report_status_valid'),
    )

class ConsistencyRepairLog(Base):
    __tablename__ = "consistency_repair_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("consistency_rules.id"), nullable=False, index=True)
    violation_id = Column(Integer, ForeignKey("consistency_violations.id"), nullable=False, index=True)
    repair_action = Column(String(100), nullable=False)
    repair_query = Column(Text)
    repair_result = Column(JSON)
    status = Column(String(20), default='PENDING', index=True)  # PENDING, SUCCESS, FAILED, ROLLBACK
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    repaired_by = Column(String(100))
    
    # Relationships
    rule = relationship("ConsistencyRule", back_populates="repair_logs")
    violation = relationship("ConsistencyViolation", back_populates="repair_logs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'SUCCESS', 'FAILED', 'ROLLBACK')", name='check_repair_status_valid'),
    )
