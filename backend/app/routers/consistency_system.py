"""
Database Consistency System Router
Automated validation and repair mechanisms
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..auth_utils import verify_admin_token
from ..services.consistency_service import ConsistencyService
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
router = APIRouter(prefix="/consistency", tags=["consistency"])

# Consistency Rule Endpoints
@router.post("/rules", response_model=ConsistencyRuleResponse)
def create_consistency_rule(
    rule_data: ConsistencyRuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Create a new consistency rule"""
    try:
        service = ConsistencyService(db)
        rule = service.create_consistency_rule(rule_data)
        return ConsistencyRuleResponse.from_orm(rule)
    except Exception as e:
        logger.error(f"Error creating consistency rule: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/rules/{rule_id}", response_model=ConsistencyRuleResponse)
def get_consistency_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Get consistency rule by ID"""
    try:
        service = ConsistencyService(db)
        rule = service.get_consistency_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consistency rule not found")
        return ConsistencyRuleResponse.from_orm(rule)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consistency rule: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/rules", response_model=List[ConsistencyRuleResponse])
def list_consistency_rules(
    active_only: bool = Query(False, description="Only return active rules"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """List consistency rules"""
    try:
        service = ConsistencyService(db)
        rules = service.list_consistency_rules(active_only=active_only)
        return [ConsistencyRuleResponse.from_orm(rule) for rule in rules]
    except Exception as e:
        logger.error(f"Error listing consistency rules: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/rules/{rule_id}", response_model=ConsistencyRuleResponse)
def update_consistency_rule(
    rule_id: int,
    rule_data: ConsistencyRuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Update consistency rule"""
    try:
        service = ConsistencyService(db)
        rule = service.update_consistency_rule(rule_id, rule_data)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consistency rule not found")
        return ConsistencyRuleResponse.from_orm(rule)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating consistency rule: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/rules/{rule_id}")
def delete_consistency_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Delete consistency rule"""
    try:
        service = ConsistencyService(db)
        success = service.delete_consistency_rule(rule_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consistency rule not found")
        return {"message": "Consistency rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting consistency rule: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Consistency Check Endpoints
@router.post("/checks", response_model=ConsistencyCheckResponse)
def create_consistency_check(
    check_data: ConsistencyCheckCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Create a new consistency check"""
    try:
        service = ConsistencyService(db)
        check = service.create_consistency_check(check_data)
        return ConsistencyCheckResponse.from_orm(check)
    except Exception as e:
        logger.error(f"Error creating consistency check: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/checks", response_model=List[ConsistencyCheckResponse])
def get_consistency_checks(
    rule_id: Optional[int] = Query(None, description="Filter by rule ID"),
    check_type: Optional[CheckType] = Query(None, description="Filter by check type"),
    status: Optional[CheckStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Get consistency checks with filtering"""
    try:
        service = ConsistencyService(db)
        checks = service.get_consistency_checks(
            rule_id=rule_id,
            check_type=check_type,
            status=status,
            limit=limit,
            offset=offset
        )
        return checks
    except Exception as e:
        logger.error(f"Error getting consistency checks: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/checks/{check_id}/run")
def run_consistency_check(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Run a consistency check"""
    try:
        service = ConsistencyService(db)
        success = service.run_consistency_check(check_id)
        return {"success": success, "message": "Consistency check completed"}
    except Exception as e:
        logger.error(f"Error running consistency check: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/checks/run-all")
def run_all_consistency_checks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Run all active consistency checks"""
    try:
        service = ConsistencyService(db)
        result = service.run_all_consistency_checks()
        return {"success": True, "result": result, "message": "All consistency checks completed"}
    except Exception as e:
        logger.error(f"Error running all consistency checks: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Consistency Violation Endpoints
@router.get("/violations", response_model=List[ConsistencyViolationResponse])
def get_consistency_violations(
    rule_id: Optional[int] = Query(None, description="Filter by rule ID"),
    violation_type: Optional[str] = Query(None, description="Filter by violation type"),
    status: Optional[ViolationStatus] = Query(None, description="Filter by status"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Get consistency violations with filtering"""
    try:
        service = ConsistencyService(db)
        violations = service.get_consistency_violations(
            rule_id=rule_id,
            violation_type=violation_type,
            status=status,
            severity=severity,
            limit=limit,
            offset=offset
        )
        return violations
    except Exception as e:
        logger.error(f"Error getting consistency violations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/violations/repair")
def repair_consistency_violation(
    request: ConsistencyRepairRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Repair a consistency violation"""
    try:
        service = ConsistencyService(db)
        success = service.repair_consistency_violation(request)
        return {"success": success, "message": "Violation repair completed"}
    except Exception as e:
        logger.error(f"Error repairing consistency violation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/violations/repair-all")
def repair_all_violations(
    repaired_by: str = Query(..., description="User performing the repair"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Repair all repairable violations"""
    try:
        service = ConsistencyService(db)
        result = service.repair_all_violations(repaired_by)
        return {"success": True, "result": result, "message": "All violations repair completed"}
    except Exception as e:
        logger.error(f"Error repairing all violations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Consistency Report Endpoints
@router.post("/reports", response_model=ConsistencyReportResponse)
def generate_consistency_report(
    request: ConsistencyReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Generate a consistency report"""
    try:
        service = ConsistencyService(db)
        report = service.generate_consistency_report(request)
        return ConsistencyReportResponse.from_orm(report)
    except Exception as e:
        logger.error(f"Error generating consistency report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/reports", response_model=List[ConsistencyReportResponse])
def get_consistency_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    status: Optional[ReportStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Get consistency reports"""
    try:
        service = ConsistencyService(db)
        reports = service.get_consistency_reports(
            report_type=report_type,
            status=status,
            limit=limit,
            offset=offset
        )
        return reports
    except Exception as e:
        logger.error(f"Error getting consistency reports: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Consistency Repair Log Endpoints
@router.get("/repair-logs", response_model=List[ConsistencyRepairLogResponse])
def get_consistency_repair_logs(
    rule_id: Optional[int] = Query(None, description="Filter by rule ID"),
    violation_id: Optional[int] = Query(None, description="Filter by violation ID"),
    status: Optional[RepairStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Get consistency repair logs"""
    try:
        service = ConsistencyService(db)
        logs = service.get_consistency_repair_logs(
            rule_id=rule_id,
            violation_id=violation_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return logs
    except Exception as e:
        logger.error(f"Error getting consistency repair logs: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Dashboard and Statistics
@router.get("/dashboard", response_model=ConsistencyDashboardStats)
def get_consistency_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Get consistency dashboard statistics"""
    try:
        service = ConsistencyService(db)
        stats = service.get_consistency_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting consistency dashboard stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
