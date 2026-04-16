"""
Audit Tools System Service
Comprehensive audit logging, compliance reporting, and data integrity monitoring
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
from datetime import datetime, timedelta
import logging
import json

from ..models.audit_system import (
    AuditLog, AuditEvent, ComplianceReport, DataIntegrityCheck, UserActivityLog
)
from ..schemas.audit_system import (
    AuditLogResponse, AuditEventCreate, AuditEventUpdate, AuditEventResponse,
    ComplianceReportCreate, ComplianceReportResponse, DataIntegrityCheckCreate,
    DataIntegrityCheckUpdate, DataIntegrityCheckResponse, UserActivityLogCreate,
    UserActivityLogResponse, AuditDashboardStats, AuditSearchRequest,
    ComplianceReportRequest, SeverityLevel, CheckStatus, ReportStatus
)

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    # Audit Log Methods
    def create_audit_log(
        self, 
        table_name: str, 
        record_id: int, 
        operation: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        changed_by: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        try:
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                old_values=old_values,
                new_values=new_values,
                changed_by=changed_by,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            return audit_log
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating audit log: {e}")
            raise e

    def get_audit_logs(self, request: AuditSearchRequest) -> List[AuditLogResponse]:
        """Get audit logs with filtering"""
        try:
            query = self.db.query(AuditLog)
            
            if request.table_name:
                query = query.filter(AuditLog.table_name == request.table_name)
            if request.operation:
                query = query.filter(AuditLog.operation == request.operation.value)
            if request.changed_by:
                query = query.filter(AuditLog.changed_by == request.changed_by)
            if request.start_date:
                query = query.filter(AuditLog.changed_at >= request.start_date)
            if request.end_date:
                query = query.filter(AuditLog.changed_at <= request.end_date)
            
            query = query.order_by(AuditLog.changed_at.desc())
            query = query.offset(request.offset).limit(request.limit)
            
            return [AuditLogResponse.from_orm(log) for log in query.all()]
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            raise e

    # Audit Event Methods
    def create_audit_event(self, event_data: AuditEventCreate) -> AuditEvent:
        """Create an audit event"""
        try:
            audit_event = AuditEvent(**event_data.dict())
            self.db.add(audit_event)
            self.db.commit()
            self.db.refresh(audit_event)
            return audit_event
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating audit event: {e}")
            raise e

    def get_audit_events(
        self, 
        event_type: Optional[str] = None,
        severity: Optional[SeverityLevel] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEventResponse]:
        """Get audit events with filtering"""
        try:
            query = self.db.query(AuditEvent)
            
            if event_type:
                query = query.filter(AuditEvent.event_type == event_type)
            if severity:
                query = query.filter(AuditEvent.severity == severity.value)
            if resolved is not None:
                if resolved:
                    query = query.filter(AuditEvent.resolved_at.isnot(None))
                else:
                    query = query.filter(AuditEvent.resolved_at.is_(None))
            
            query = query.order_by(AuditEvent.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            return [AuditEventResponse.from_orm(event) for event in query.all()]
        except Exception as e:
            logger.error(f"Error getting audit events: {e}")
            raise e

    def resolve_audit_event(self, event_id: int, resolution_notes: str) -> Optional[AuditEvent]:
        """Resolve an audit event"""
        try:
            event = self.db.query(AuditEvent).filter(AuditEvent.id == event_id).first()
            if not event:
                return None
            
            event.resolved_at = datetime.now()
            event.resolution_notes = resolution_notes
            
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resolving audit event: {e}")
            raise e

    # Compliance Report Methods
    def generate_compliance_report(self, request: ComplianceReportRequest) -> ComplianceReport:
        """Generate a compliance report"""
        try:
            # Use database function to generate report
            result = self.db.execute(
                text("SELECT generate_compliance_report(:report_type, :report_name, :generated_by)"),
                {
                    "report_type": request.report_type,
                    "report_name": request.report_name,
                    "generated_by": request.generated_by or "system"
                }
            ).scalar()
            
            # Get the generated report
            report = self.db.query(ComplianceReport).filter(ComplianceReport.id == result).first()
            return report
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise e

    def get_compliance_reports(
        self, 
        report_type: Optional[str] = None,
        status: Optional[ReportStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ComplianceReportResponse]:
        """Get compliance reports"""
        try:
            query = self.db.query(ComplianceReport)
            
            if report_type:
                query = query.filter(ComplianceReport.report_type == report_type)
            if status:
                query = query.filter(ComplianceReport.status == status.value)
            
            query = query.order_by(ComplianceReport.generated_at.desc())
            query = query.offset(offset).limit(limit)
            
            return [ComplianceReportResponse.from_orm(report) for report in query.all()]
        except Exception as e:
            logger.error(f"Error getting compliance reports: {e}")
            raise e

    # Data Integrity Check Methods
    def create_data_integrity_check(self, check_data: DataIntegrityCheckCreate) -> DataIntegrityCheck:
        """Create a data integrity check"""
        try:
            check = DataIntegrityCheck(**check_data.dict())
            self.db.add(check)
            self.db.commit()
            self.db.refresh(check)
            return check
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating data integrity check: {e}")
            raise e

    def get_data_integrity_checks(
        self, 
        check_type: Optional[str] = None,
        status: Optional[CheckStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DataIntegrityCheckResponse]:
        """Get data integrity checks"""
        try:
            query = self.db.query(DataIntegrityCheck)
            
            if check_type:
                query = query.filter(DataIntegrityCheck.check_type == check_type)
            if status:
                query = query.filter(DataIntegrityCheck.status == status.value)
            
            query = query.order_by(DataIntegrityCheck.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            return [DataIntegrityCheckResponse.from_orm(check) for check in query.all()]
        except Exception as e:
            logger.error(f"Error getting data integrity checks: {e}")
            raise e

    def run_data_integrity_check(self, check_id: int) -> bool:
        """Run a data integrity check"""
        try:
            # Use database function to run check
            result = self.db.execute(
                text("SELECT run_data_integrity_check(:check_id)"),
                {"check_id": check_id}
            ).scalar()
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error running data integrity check: {e}")
            raise e

    def run_all_data_integrity_checks(self) -> Dict[str, Any]:
        """Run all pending data integrity checks"""
        try:
            pending_checks = self.db.query(DataIntegrityCheck).filter(
                DataIntegrityCheck.status == CheckStatus.PENDING
            ).all()
            
            results = {
                "total_checks": len(pending_checks),
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "details": []
            }
            
            for check in pending_checks:
                try:
                    passed = self.run_data_integrity_check(check.id)
                    if passed:
                        results["passed"] += 1
                    else:
                        results["failed"] += 1
                    
                    results["details"].append({
                        "check_id": check.id,
                        "check_name": check.check_name,
                        "status": "PASSED" if passed else "FAILED"
                    })
                except Exception as e:
                    results["errors"] += 1
                    results["details"].append({
                        "check_id": check.id,
                        "check_name": check.check_name,
                        "status": "ERROR",
                        "error": str(e)
                    })
            
            return results
        except Exception as e:
            logger.error(f"Error running all data integrity checks: {e}")
            raise e

    # User Activity Log Methods
    def log_user_activity(self, activity_data: UserActivityLogCreate) -> UserActivityLog:
        """Log user activity"""
        try:
            activity = UserActivityLog(**activity_data.dict())
            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error logging user activity: {e}")
            raise e

    def get_user_activities(
        self, 
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserActivityLogResponse]:
        """Get user activities"""
        try:
            query = self.db.query(UserActivityLog)
            
            if user_id:
                query = query.filter(UserActivityLog.user_id == user_id)
            if action:
                query = query.filter(UserActivityLog.action == action)
            
            query = query.order_by(UserActivityLog.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            return [UserActivityLogResponse.from_orm(activity) for activity in query.all()]
        except Exception as e:
            logger.error(f"Error getting user activities: {e}")
            raise e

    # Dashboard and Statistics
    def get_audit_dashboard_stats(self) -> AuditDashboardStats:
        """Get audit dashboard statistics"""
        try:
            # Get counts
            total_audit_logs = self.db.query(AuditLog).count()
            total_audit_events = self.db.query(AuditEvent).count()
            total_compliance_reports = self.db.query(ComplianceReport).count()
            total_data_integrity_checks = self.db.query(DataIntegrityCheck).count()
            total_user_activities = self.db.query(UserActivityLog).count()
            
            # Get recent activities (last 24 hours)
            recent_activities = self.db.query(UserActivityLog).filter(
                UserActivityLog.created_at >= datetime.now() - timedelta(days=1)
            ).order_by(UserActivityLog.created_at.desc()).limit(10).all()
            
            # Get failed checks
            failed_checks = self.db.query(DataIntegrityCheck).filter(
                DataIntegrityCheck.status == CheckStatus.FAILED
            ).limit(10).all()
            
            # Get unresolved events
            unresolved_events = self.db.query(AuditEvent).filter(
                AuditEvent.resolved_at.is_(None)
            ).order_by(AuditEvent.created_at.desc()).limit(10).all()
            
            return AuditDashboardStats(
                total_audit_logs=total_audit_logs,
                total_audit_events=total_audit_events,
                total_compliance_reports=total_compliance_reports,
                total_data_integrity_checks=total_data_integrity_checks,
                total_user_activities=total_user_activities,
                recent_activities=[
                    {
                        "id": activity.id,
                        "user_id": activity.user_id,
                        "action": activity.action,
                        "created_at": activity.created_at.isoformat()
                    }
                    for activity in recent_activities
                ],
                failed_checks=[
                    {
                        "id": check.id,
                        "check_name": check.check_name,
                        "status": check.status,
                        "last_run": check.last_run.isoformat() if check.last_run else None
                    }
                    for check in failed_checks
                ],
                unresolved_events=[
                    {
                        "id": event.id,
                        "event_type": event.event_type,
                        "severity": event.severity,
                        "description": event.description,
                        "created_at": event.created_at.isoformat()
                    }
                    for event in unresolved_events
                ]
            )
        except Exception as e:
            logger.error(f"Error getting audit dashboard stats: {e}")
            raise e
