"""
Database Consistency System Service
Automated validation and repair mechanisms
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from datetime import datetime, timedelta
import logging
import json

from ..models.consistency_system import (
    ConsistencyRule, ConsistencyCheck, ConsistencyViolation, 
    ConsistencyReport, ConsistencyRepairLog
)
from ..schemas.consistency_system import (
    ConsistencyRuleCreate, ConsistencyRuleUpdate, ConsistencyRuleResponse,
    ConsistencyCheckCreate, ConsistencyCheckUpdate, ConsistencyCheckResponse,
    ConsistencyViolationCreate, ConsistencyViolationUpdate, ConsistencyViolationResponse,
    ConsistencyReportCreate, ConsistencyReportResponse,
    ConsistencyRepairLogCreate, ConsistencyRepairLogResponse,
    ConsistencyDashboardStats, ConsistencyCheckRequest, ConsistencyRepairRequest,
    ConsistencyReportRequest, ConsistencyRuleTestRequest,
    RuleType, CheckType, SeverityLevel, CheckStatus, ViolationStatus, 
    ReportStatus, RepairStatus
)

logger = logging.getLogger(__name__)

class ConsistencyService:
    def __init__(self, db: Session):
        self.db = db

    # Consistency Rule Methods
    def create_consistency_rule(self, rule_data: ConsistencyRuleCreate) -> ConsistencyRule:
        """Create a new consistency rule"""
        try:
            db_rule = ConsistencyRule(**rule_data.dict())
            self.db.add(db_rule)
            self.db.commit()
            self.db.refresh(db_rule)
            
            # Create consistency check for the rule
            check_data = ConsistencyCheckCreate(
                rule_id=db_rule.id,
                check_name=f"{rule_data.rule_name} Check",
                check_type=CheckType(rule_data.rule_type.value),
                table_name=rule_data.table_name,
                check_query=rule_data.validation_query,
                expected_result="0"
            )
            self.create_consistency_check(check_data)
            
            return db_rule
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating consistency rule: {e}")
            raise e

    def get_consistency_rule(self, rule_id: int) -> Optional[ConsistencyRule]:
        """Get consistency rule by ID"""
        return self.db.query(ConsistencyRule).filter(ConsistencyRule.id == rule_id).first()

    def list_consistency_rules(self, active_only: bool = False) -> List[ConsistencyRule]:
        """List consistency rules"""
        query = self.db.query(ConsistencyRule)
        if active_only:
            query = query.filter(ConsistencyRule.is_active == True)
        return query.all()

    def update_consistency_rule(self, rule_id: int, rule_data: ConsistencyRuleUpdate) -> Optional[ConsistencyRule]:
        """Update consistency rule"""
        try:
            db_rule = self.get_consistency_rule(rule_id)
            if not db_rule:
                return None
            
            update_data = rule_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_rule, field, value)
            
            self.db.commit()
            self.db.refresh(db_rule)
            return db_rule
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating consistency rule: {e}")
            raise e

    def delete_consistency_rule(self, rule_id: int) -> bool:
        """Delete consistency rule"""
        try:
            db_rule = self.get_consistency_rule(rule_id)
            if not db_rule:
                return False
            
            self.db.delete(db_rule)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting consistency rule: {e}")
            raise e

    # Consistency Check Methods
    def create_consistency_check(self, check_data: ConsistencyCheckCreate) -> ConsistencyCheck:
        """Create a new consistency check"""
        try:
            db_check = ConsistencyCheck(**check_data.dict())
            self.db.add(db_check)
            self.db.commit()
            self.db.refresh(db_check)
            return db_check
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating consistency check: {e}")
            raise e

    def get_consistency_checks(
        self, 
        rule_id: Optional[int] = None,
        check_type: Optional[CheckType] = None,
        status: Optional[CheckStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConsistencyCheckResponse]:
        """Get consistency checks with filtering"""
        try:
            query = self.db.query(ConsistencyCheck)
            
            if rule_id:
                query = query.filter(ConsistencyCheck.rule_id == rule_id)
            if check_type:
                query = query.filter(ConsistencyCheck.check_type == check_type.value)
            if status:
                query = query.filter(ConsistencyCheck.status == status.value)
            
            query = query.order_by(desc(ConsistencyCheck.created_at))
            query = query.offset(offset).limit(limit)
            
            return [ConsistencyCheckResponse.from_orm(check) for check in query.all()]
        except Exception as e:
            logger.error(f"Error getting consistency checks: {e}")
            raise e

    def run_consistency_check(self, check_id: int) -> bool:
        """Run a consistency check"""
        try:
            # Use database function to run check
            result = self.db.execute(
                text("SELECT run_consistency_check(:check_id)"),
                {"check_id": check_id}
            ).scalar()
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error running consistency check: {e}")
            raise e

    def run_all_consistency_checks(self) -> Dict[str, Any]:
        """Run all active consistency checks"""
        try:
            # Use database function to run all checks
            result = self.db.execute(
                text("SELECT run_all_consistency_checks()")
            ).scalar()
            
            return result
        except Exception as e:
            logger.error(f"Error running all consistency checks: {e}")
            raise e

    # Consistency Violation Methods
    def get_consistency_violations(
        self,
        rule_id: Optional[int] = None,
        violation_type: Optional[str] = None,
        status: Optional[ViolationStatus] = None,
        severity: Optional[SeverityLevel] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConsistencyViolationResponse]:
        """Get consistency violations with filtering"""
        try:
            query = self.db.query(ConsistencyViolation)
            
            if rule_id:
                query = query.filter(ConsistencyViolation.rule_id == rule_id)
            if violation_type:
                query = query.filter(ConsistencyViolation.violation_type == violation_type)
            if status:
                query = query.filter(ConsistencyViolation.status == status.value)
            if severity:
                query = query.filter(ConsistencyViolation.severity == severity.value)
            
            query = query.order_by(desc(ConsistencyViolation.detected_at))
            query = query.offset(offset).limit(limit)
            
            return [ConsistencyViolationResponse.from_orm(violation) for violation in query.all()]
        except Exception as e:
            logger.error(f"Error getting consistency violations: {e}")
            raise e

    def repair_consistency_violation(self, request: ConsistencyRepairRequest) -> bool:
        """Repair a consistency violation"""
        try:
            # Use database function to repair violation
            result = self.db.execute(
                text("SELECT repair_consistency_violation(:violation_id, :repaired_by)"),
                {
                    "violation_id": request.violation_id,
                    "repaired_by": request.repaired_by
                }
            ).scalar()
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error repairing consistency violation: {e}")
            raise e

    def repair_all_violations(self, repaired_by: str) -> Dict[str, Any]:
        """Repair all repairable violations"""
        try:
            violations = self.db.query(ConsistencyViolation).filter(
                ConsistencyViolation.status == ViolationStatus.DETECTED
            ).all()
            
            results = {
                "total_violations": len(violations),
                "repaired": 0,
                "failed": 0,
                "ignored": 0,
                "details": []
            }
            
            for violation in violations:
                try:
                    success = self.repair_consistency_violation(
                        ConsistencyRepairRequest(
                            violation_id=violation.id,
                            repaired_by=repaired_by
                        )
                    )
                    
                    if success:
                        results["repaired"] += 1
                        results["details"].append({
                            "violation_id": violation.id,
                            "status": "REPAIRED"
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "violation_id": violation.id,
                            "status": "FAILED"
                        })
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "violation_id": violation.id,
                        "status": "ERROR",
                        "error": str(e)
                    })
            
            return results
        except Exception as e:
            logger.error(f"Error repairing all violations: {e}")
            raise e

    # Consistency Report Methods
    def generate_consistency_report(self, request: ConsistencyReportRequest) -> ConsistencyReport:
        """Generate a consistency report"""
        try:
            # Use database function to generate report
            result = self.db.execute(
                text("SELECT generate_consistency_report(:report_type, :report_name, :generated_by)"),
                {
                    "report_type": request.report_type,
                    "report_name": request.report_name,
                    "generated_by": request.generated_by or "system"
                }
            ).scalar()
            
            # Get the generated report
            report = self.db.query(ConsistencyReport).filter(ConsistencyReport.id == result).first()
            return report
        except Exception as e:
            logger.error(f"Error generating consistency report: {e}")
            raise e

    def get_consistency_reports(
        self, 
        report_type: Optional[str] = None,
        status: Optional[ReportStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConsistencyReportResponse]:
        """Get consistency reports"""
        try:
            query = self.db.query(ConsistencyReport)
            
            if report_type:
                query = query.filter(ConsistencyReport.report_type == report_type)
            if status:
                query = query.filter(ConsistencyReport.status == status.value)
            
            query = query.order_by(desc(ConsistencyReport.generated_at))
            query = query.offset(offset).limit(limit)
            
            return [ConsistencyReportResponse.from_orm(report) for report in query.all()]
        except Exception as e:
            logger.error(f"Error getting consistency reports: {e}")
            raise e

    # Consistency Repair Log Methods
    def get_consistency_repair_logs(
        self,
        rule_id: Optional[int] = None,
        violation_id: Optional[int] = None,
        status: Optional[RepairStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConsistencyRepairLogResponse]:
        """Get consistency repair logs"""
        try:
            query = self.db.query(ConsistencyRepairLog)
            
            if rule_id:
                query = query.filter(ConsistencyRepairLog.rule_id == rule_id)
            if violation_id:
                query = query.filter(ConsistencyRepairLog.violation_id == violation_id)
            if status:
                query = query.filter(ConsistencyRepairLog.status == status.value)
            
            query = query.order_by(desc(ConsistencyRepairLog.started_at))
            query = query.offset(offset).limit(limit)
            
            return [ConsistencyRepairLogResponse.from_orm(log) for log in query.all()]
        except Exception as e:
            logger.error(f"Error getting consistency repair logs: {e}")
            raise e

    # Dashboard and Statistics
    def get_consistency_dashboard_stats(self) -> ConsistencyDashboardStats:
        """Get consistency dashboard statistics"""
        try:
            # Get counts
            total_rules = self.db.query(ConsistencyRule).count()
            active_rules = self.db.query(ConsistencyRule).filter(ConsistencyRule.is_active == True).count()
            
            total_checks = self.db.query(ConsistencyCheck).count()
            passed_checks = self.db.query(ConsistencyCheck).filter(ConsistencyCheck.status == CheckStatus.PASSED).count()
            failed_checks = self.db.query(ConsistencyCheck).filter(ConsistencyCheck.status == CheckStatus.FAILED).count()
            
            total_violations = self.db.query(ConsistencyViolation).count()
            
            # Get violations by severity
            violations_by_severity = {}
            for severity in SeverityLevel:
                count = self.db.query(ConsistencyViolation).filter(
                    ConsistencyViolation.severity == severity.value
                ).count()
                violations_by_severity[severity.value] = count
            
            # Get violations by table
            violations_by_table = {}
            table_counts = self.db.query(
                ConsistencyViolation.table_name,
                func.count(ConsistencyViolation.id).label('count')
            ).group_by(ConsistencyViolation.table_name).all()
            
            for table_name, count in table_counts:
                violations_by_table[table_name] = count
            
            # Get recent violations
            recent_violations = self.db.query(ConsistencyViolation).order_by(
                desc(ConsistencyViolation.detected_at)
            ).limit(10).all()
            
            # Get recent repairs
            recent_repairs = self.db.query(ConsistencyRepairLog).order_by(
                desc(ConsistencyRepairLog.started_at)
            ).limit(10).all()
            
            return ConsistencyDashboardStats(
                total_rules=total_rules,
                active_rules=active_rules,
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                total_violations=total_violations,
                violations_by_severity=violations_by_severity,
                violations_by_table=violations_by_table,
                recent_violations=[
                    {
                        "id": violation.id,
                        "rule_id": violation.rule_id,
                        "violation_type": violation.violation_type,
                        "table_name": violation.table_name,
                        "severity": violation.severity,
                        "status": violation.status,
                        "detected_at": violation.detected_at.isoformat()
                    }
                    for violation in recent_violations
                ],
                recent_repairs=[
                    {
                        "id": log.id,
                        "rule_id": log.rule_id,
                        "violation_id": log.violation_id,
                        "repair_action": log.repair_action,
                        "status": log.status,
                        "started_at": log.started_at.isoformat()
                    }
                    for log in recent_repairs
                ]
            )
        except Exception as e:
            logger.error(f"Error getting consistency dashboard stats: {e}")
            raise e
