# backend/app/routers/bulk_operations.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..services.bulk_operations_service import BulkOperationsService
from ..schemas.bulk_operations import (
    BulkOperationCreate, BulkOperationResponse, BulkOperationStatusResponse,
    BulkTransferRequest, BulkPriceUpdateRequest, BulkStatusChangeRequest,
    BulkOperationListResponse, BulkOperationStatsResponse
)

router = APIRouter(prefix="/api/bulk-operations", tags=["bulk-operations"])

@router.post("/purchase", response_model=BulkOperationResponse)
async def create_bulk_purchase(
    request: BulkOperationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create bulk purchase operation"""
    service = BulkOperationsService(db)
    
    try:
        # Create operation
        operation = await service.create_bulk_purchase(request)
        
        # Process in background
        background_tasks.add_task(
            service.process_bulk_operation, 
            operation.id
        )
        
        return operation
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfer", response_model=BulkOperationResponse)
async def create_bulk_transfer(
    request: BulkTransferRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create bulk transfer operation"""
    service = BulkOperationsService(db)
    
    try:
        # Create operation
        operation = await service.create_bulk_transfer(request)
        
        # Process in background
        background_tasks.add_task(
            service.process_bulk_operation, 
            operation.id
        )
        
        return operation
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/price-update", response_model=BulkOperationResponse)
async def create_bulk_price_update(
    request: BulkPriceUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create bulk price update operation"""
    service = BulkOperationsService(db)
    
    try:
        # Create operation
        operation = await service.create_bulk_price_update(request)
        
        # Process in background
        background_tasks.add_task(
            service.process_bulk_operation, 
            operation.id
        )
        
        return operation
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/status-change", response_model=BulkOperationResponse)
async def create_bulk_status_change(
    request: BulkStatusChangeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create bulk status change operation"""
    service = BulkOperationsService(db)
    
    try:
        # Create operation
        operation = await service.create_bulk_status_change(request)
        
        # Process in background
        background_tasks.add_task(
            service.process_bulk_operation, 
            operation.id
        )
        
        return operation
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{operation_id}/status", response_model=BulkOperationStatusResponse)
async def get_operation_status(
    operation_id: int,
    db: Session = Depends(get_db)
):
    """Get bulk operation status and progress"""
    service = BulkOperationsService(db)
    
    try:
        return await service.get_operation_status(operation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{operation_id}/cancel")
async def cancel_operation(
    operation_id: int,
    db: Session = Depends(get_db)
):
    """Cancel bulk operation"""
    service = BulkOperationsService(db)
    
    try:
        result = await service.cancel_operation(operation_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=BulkOperationListResponse)
async def list_operations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    operation_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List bulk operations with pagination"""
    service = BulkOperationsService(db)
    
    try:
        # Build query
        query = db.query(BulkOperation)
        
        if status:
            query = query.filter(BulkOperation.status == status)
        if operation_type:
            query = query.filter(BulkOperation.operation_type == operation_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        operations = query.order_by(BulkOperation.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return BulkOperationListResponse(
            operations=[BulkOperationResponse.from_orm(op) for op in operations],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=BulkOperationStatsResponse)
async def get_operation_stats(
    db: Session = Depends(get_db)
):
    """Get bulk operation statistics"""
    service = BulkOperationsService(db)
    
    try:
        return await service.get_operation_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{operation_id}", response_model=BulkOperationResponse)
async def get_operation(
    operation_id: int,
    db: Session = Depends(get_db)
):
    """Get specific bulk operation details"""
    operation = db.query(BulkOperation).filter(BulkOperation.id == operation_id).first()
    
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    return BulkOperationResponse.from_orm(operation)
