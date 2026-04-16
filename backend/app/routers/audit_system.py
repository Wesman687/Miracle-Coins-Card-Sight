"""
Audit Tools System API Router
Comprehensive audit logging, compliance reporting, and data integrity monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.auth_utils import verify_admin_token
from app.services.audit_service import AuditService
from app.schemas.audit_system import (
    AuditLogResponse, AuditEventCreate, AuditEventUpdate, AuditEventResponse,
    ComplianceReportCreate, ComplianceReportResponse, DataIntegrityCheckCreate,
    DataIntegrityCheckUpdate, DataIntegrityCheckResponse, UserActivityLogCreate,
    UserActivityLogResponse, AuditDashboardStats, AuditSearchRequest,
    ComplianceReportRequest, SeverityLevel, CheckStatus, ReportStatus
)

router = APIRouter(
    prefix="/audit",
    tags=["audit-management"],
    dependencies=[Depends(verify_admin_token)]
)

# Audit Logs Endpoints
@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    request: AuditSearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering"""
    service = AuditService(db)
    try:
        return service.get_audit_logs(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Audit Events Endpoints
@router.post("/events", response_model=AuditEventResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_event(
    event_data: AuditEventCreate,
    db: Session = Depends(get_db)
):
    """Create an audit event"""
    service = AuditService(db)
    try:
        return service.create_audit_event(event_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/events", response_model=List[AuditEventResponse])
async def get_audit_events(
    event_type: Optional[str] = Query(None),
    severity: Optional[SeverityLevel] = Query(None),
    resolved: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get audit events with filtering"""
    service = AuditService(db)
    try:
        return service.get_audit_events(
            event_type=event_type,
            severity=severity,
            resolved=resolved,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/events/{event_id}/resolve", response_model=AuditEventResponse)
async def resolve_audit_event(
    event_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db)
):
    """Resolve an audit event"""
    service = AuditService(db)
    try:
        event = service.resolve_audit_event(event_id, resolution_notes)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return event
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Compliance Reports Endpoints
@router.post("/reports/generate", response_model=ComplianceReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db: Session = Depends(get_db)
):
    """Generate a compliance report"""
    service = AuditService(db)
    try:
        return service.generate_compliance_report(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/reports", response_model=List[ComplianceReportResponse])
async def get_compliance_reports(
    report_type: Optional[str] = Query(None),
    status: Optional[ReportStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get compliance reports"""
    service = AuditService(db)
    try:
        return service.get_compliance_reports(
            report_type=report_type,
            status=status,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Data Integrity Checks Endpoints
@router.post("/integrity-checks", response_model=DataIntegrityCheckResponse, status_code=status.HTTP_201_CREATED)
async def create_data_integrity_check(
    check_data: DataIntegrityCheckCreate,
    db: Session = Depends(get_db)
):
    """Create a data integrity check"""
    service = AuditService(db)
    try:
        return service.create_data_integrity_check(check_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/integrity-checks", response_model=List[DataIntegrityCheckResponse])
async def get_data_integrity_checks(
    check_type: Optional[str] = Query(None),
    status: Optional[CheckStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get data integrity checks"""
    service = AuditService(db)
    try:
        return service.get_data_integrity_checks(
            check_type=check_type,
            status=status,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/integrity-checks/{check_id}/run", status_code=status.HTTP_200_OK)
async def run_data_integrity_check(
    check_id: int,
    db: Session = Depends(get_db)
):
    """Run a data integrity check"""
    service = AuditService(db)
    try:
        result = service.run_data_integrity_check(check_id)
        return {"check_id": check_id, "passed": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/integrity-checks/run-all", status_code=status.HTTP_200_OK)
async def run_all_data_integrity_checks(
    db: Session = Depends(get_db)
):
    """Run all pending data integrity checks"""
    service = AuditService(db)
    try:
        results = service.run_all_data_integrity_checks()
        return results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# User Activity Logs Endpoints
@router.post("/user-activities", response_model=UserActivityLogResponse, status_code=status.HTTP_201_CREATED)
async def log_user_activity(
    activity_data: UserActivityLogCreate,
    db: Session = Depends(get_db)
):
    """Log user activity"""
    service = AuditService(db)
    try:
        return service.log_user_activity(activity_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/user-activities", response_model=List[UserActivityLogResponse])
async def get_user_activities(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get user activities"""
    service = AuditService(db)
    try:
        return service.get_user_activities(
            user_id=user_id,
            action=action,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Dashboard Endpoints
@router.get("/dashboard/stats", response_model=AuditDashboardStats)
async def get_audit_dashboard_stats(
    db: Session = Depends(get_db)
):
    """Get audit dashboard statistics"""
    service = AuditService(db)
    try:
        return service.get_audit_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
