"""
Real-Time Sync System API Router
Multi-channel synchronization with conflict resolution
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.auth_utils import verify_admin_token
from app.services.sync_service import SyncService
from app.schemas.sync_system import (
    SyncChannelCreate, SyncChannelUpdate, SyncChannelResponse,
    SyncLogCreate, SyncLogUpdate, SyncLogResponse,
    SyncConflictCreate, SyncConflictUpdate, SyncConflictResponse,
    SyncQueueCreate, SyncQueueUpdate, SyncQueueResponse,
    SyncStatusResponse, SyncDashboardStats, SyncRequest,
    ConflictResolutionRequest, QueueProcessRequest,
    ChannelType, SyncType, SyncStatus, ConflictType, ResolutionStatus, QueueStatus
)

router = APIRouter(
    prefix="/sync",
    tags=["sync-management"],
    dependencies=[Depends(verify_admin_token)]
)

# Sync Channel Endpoints
@router.post("/channels", response_model=SyncChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_sync_channel(
    channel_data: SyncChannelCreate,
    db: Session = Depends(get_db)
):
    """Create a new sync channel"""
    service = SyncService(db)
    try:
        return service.create_sync_channel(channel_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/channels", response_model=List[SyncChannelResponse])
async def list_sync_channels(
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List sync channels"""
    service = SyncService(db)
    return service.list_sync_channels(active_only=active_only)

@router.get("/channels/{channel_id}", response_model=SyncChannelResponse)
async def get_sync_channel(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Get sync channel by ID"""
    service = SyncService(db)
    channel = service.get_sync_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel

@router.put("/channels/{channel_id}", response_model=SyncChannelResponse)
async def update_sync_channel(
    channel_id: int,
    channel_data: SyncChannelUpdate,
    db: Session = Depends(get_db)
):
    """Update sync channel"""
    service = SyncService(db)
    channel = service.update_sync_channel(channel_id, channel_data)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel

@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sync_channel(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Delete sync channel"""
    service = SyncService(db)
    success = service.delete_sync_channel(channel_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

# Sync Log Endpoints
@router.post("/logs", response_model=SyncLogResponse, status_code=status.HTTP_201_CREATED)
async def create_sync_log(
    log_data: SyncLogCreate,
    db: Session = Depends(get_db)
):
    """Create a sync log entry"""
    service = SyncService(db)
    try:
        return service.create_sync_log(log_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/logs", response_model=List[SyncLogResponse])
async def get_sync_logs(
    channel_id: Optional[int] = Query(None),
    sync_type: Optional[SyncType] = Query(None),
    status: Optional[SyncStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get sync logs with filtering"""
    service = SyncService(db)
    return service.get_sync_logs(
        channel_id=channel_id,
        sync_type=sync_type,
        status=status,
        limit=limit,
        offset=offset
    )

@router.put("/logs/{log_id}", response_model=SyncLogResponse)
async def update_sync_log(
    log_id: int,
    log_data: SyncLogUpdate,
    db: Session = Depends(get_db)
):
    """Update sync log"""
    service = SyncService(db)
    log = service.update_sync_log(log_id, log_data)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sync log not found")
    return log

# Sync Conflict Endpoints
@router.post("/conflicts", response_model=SyncConflictResponse, status_code=status.HTTP_201_CREATED)
async def create_sync_conflict(
    conflict_data: SyncConflictCreate,
    db: Session = Depends(get_db)
):
    """Create a sync conflict"""
    service = SyncService(db)
    try:
        return service.create_sync_conflict(conflict_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/conflicts", response_model=List[SyncConflictResponse])
async def get_sync_conflicts(
    channel_id: Optional[int] = Query(None),
    conflict_type: Optional[ConflictType] = Query(None),
    resolution_status: Optional[ResolutionStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get sync conflicts with filtering"""
    service = SyncService(db)
    return service.get_sync_conflicts(
        channel_id=channel_id,
        conflict_type=conflict_type,
        resolution_status=resolution_status,
        limit=limit,
        offset=offset
    )

@router.post("/conflicts/resolve", status_code=status.HTTP_200_OK)
async def resolve_sync_conflict(
    request: ConflictResolutionRequest,
    db: Session = Depends(get_db)
):
    """Resolve a sync conflict"""
    service = SyncService(db)
    try:
        success = service.resolve_sync_conflict(request)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")
        return {"message": "Conflict resolved successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Sync Queue Endpoints
@router.post("/queue", response_model=SyncQueueResponse, status_code=status.HTTP_201_CREATED)
async def add_to_sync_queue(
    queue_data: SyncQueueCreate,
    db: Session = Depends(get_db)
):
    """Add item to sync queue"""
    service = SyncService(db)
    try:
        return service.add_to_sync_queue(queue_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/queue", response_model=List[SyncQueueResponse])
async def get_sync_queue(
    channel_id: Optional[int] = Query(None),
    status: Optional[QueueStatus] = Query(None),
    priority_filter: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get sync queue items"""
    service = SyncService(db)
    return service.get_sync_queue(
        channel_id=channel_id,
        status=status,
        priority_filter=priority_filter,
        limit=limit,
        offset=offset
    )

@router.post("/queue/process", status_code=status.HTTP_200_OK)
async def process_sync_queue(
    request: QueueProcessRequest,
    db: Session = Depends(get_db)
):
    """Process sync queue items"""
    service = SyncService(db)
    try:
        result = service.process_sync_queue(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Sync Status Endpoints
@router.get("/status", response_model=List[SyncStatusResponse])
async def get_all_sync_status(
    db: Session = Depends(get_db)
):
    """Get sync status for all channels"""
    service = SyncService(db)
    return service.get_all_sync_status()

@router.get("/status/{channel_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Get sync status for a specific channel"""
    service = SyncService(db)
    status = service.get_sync_status(channel_id)
    if not status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return status

# Sync Operations
@router.post("/start", response_model=SyncLogResponse, status_code=status.HTTP_201_CREATED)
async def start_sync(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """Start a sync operation"""
    service = SyncService(db)
    try:
        return service.start_sync(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Dashboard Endpoints
@router.get("/dashboard/stats", response_model=SyncDashboardStats)
async def get_sync_dashboard_stats(
    db: Session = Depends(get_db)
):
    """Get sync dashboard statistics"""
    service = SyncService(db)
    try:
        return service.get_sync_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
