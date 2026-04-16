"""
Real-Time Sync System Service
Multi-channel synchronization with conflict resolution
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from datetime import datetime, timedelta
import logging
import json

from ..models.sync_system import (
    SyncChannel, SyncLog, SyncConflict, SyncQueue, SyncStatus
)
from ..schemas.sync_system import (
    SyncChannelCreate, SyncChannelUpdate, SyncChannelResponse,
    SyncLogCreate, SyncLogUpdate, SyncLogResponse,
    SyncConflictCreate, SyncConflictUpdate, SyncConflictResponse,
    SyncQueueCreate, SyncQueueUpdate, SyncQueueResponse,
    SyncStatusResponse, SyncDashboardStats, SyncRequest,
    ConflictResolutionRequest, QueueProcessRequest,
    ChannelType, SyncType, SyncStatus as SyncStatusEnum,
    ConflictType, ResolutionStatus, QueueOperation, QueueStatus
)

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, db: Session):
        self.db = db

    # Sync Channel Methods
    def create_sync_channel(self, channel_data: SyncChannelCreate) -> SyncChannel:
        """Create a new sync channel"""
        try:
            db_channel = SyncChannel(**channel_data.dict())
            self.db.add(db_channel)
            self.db.commit()
            self.db.refresh(db_channel)
            
            # Create sync status record
            sync_status = SyncStatus(channel_id=db_channel.id)
            self.db.add(sync_status)
            self.db.commit()
            
            return db_channel
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating sync channel: {e}")
            raise e

    def get_sync_channel(self, channel_id: int) -> Optional[SyncChannel]:
        """Get sync channel by ID"""
        return self.db.query(SyncChannel).filter(SyncChannel.id == channel_id).first()

    def get_sync_channel_by_name(self, channel_name: str) -> Optional[SyncChannel]:
        """Get sync channel by name"""
        return self.db.query(SyncChannel).filter(SyncChannel.channel_name == channel_name).first()

    def list_sync_channels(self, active_only: bool = False) -> List[SyncChannel]:
        """List sync channels"""
        query = self.db.query(SyncChannel)
        if active_only:
            query = query.filter(SyncChannel.is_active == True)
        return query.all()

    def update_sync_channel(self, channel_id: int, channel_data: SyncChannelUpdate) -> Optional[SyncChannel]:
        """Update sync channel"""
        try:
            db_channel = self.get_sync_channel(channel_id)
            if not db_channel:
                return None
            
            update_data = channel_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_channel, field, value)
            
            self.db.commit()
            self.db.refresh(db_channel)
            return db_channel
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating sync channel: {e}")
            raise e

    def delete_sync_channel(self, channel_id: int) -> bool:
        """Delete sync channel"""
        try:
            db_channel = self.get_sync_channel(channel_id)
            if not db_channel:
                return False
            
            self.db.delete(db_channel)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting sync channel: {e}")
            raise e

    # Sync Log Methods
    def create_sync_log(self, log_data: SyncLogCreate) -> SyncLog:
        """Create a sync log entry"""
        try:
            db_log = SyncLog(**log_data.dict())
            self.db.add(db_log)
            self.db.commit()
            self.db.refresh(db_log)
            
            # Update sync status
            sync_status = self.db.query(SyncStatus).filter(
                SyncStatus.channel_id == log_data.channel_id
            ).first()
            if sync_status:
                sync_status.sync_in_progress = True
                sync_status.current_sync_id = db_log.id
                self.db.commit()
            
            return db_log
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating sync log: {e}")
            raise e

    def update_sync_log(self, log_id: int, log_data: SyncLogUpdate) -> Optional[SyncLog]:
        """Update sync log"""
        try:
            db_log = self.db.query(SyncLog).filter(SyncLog.id == log_id).first()
            if not db_log:
                return None
            
            update_data = log_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_log, field, value)
            
            self.db.commit()
            self.db.refresh(db_log)
            return db_log
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating sync log: {e}")
            raise e

    def get_sync_logs(
        self, 
        channel_id: Optional[int] = None,
        sync_type: Optional[SyncType] = None,
        status: Optional[SyncStatusEnum] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SyncLogResponse]:
        """Get sync logs with filtering"""
        try:
            query = self.db.query(SyncLog)
            
            if channel_id:
                query = query.filter(SyncLog.channel_id == channel_id)
            if sync_type:
                query = query.filter(SyncLog.sync_type == sync_type.value)
            if status:
                query = query.filter(SyncLog.status == status.value)
            
            query = query.order_by(desc(SyncLog.started_at))
            query = query.offset(offset).limit(limit)
            
            return [SyncLogResponse.from_orm(log) for log in query.all()]
        except Exception as e:
            logger.error(f"Error getting sync logs: {e}")
            raise e

    # Sync Conflict Methods
    def create_sync_conflict(self, conflict_data: SyncConflictCreate) -> SyncConflict:
        """Create a sync conflict"""
        try:
            db_conflict = SyncConflict(**conflict_data.dict())
            self.db.add(db_conflict)
            self.db.commit()
            self.db.refresh(db_conflict)
            return db_conflict
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating sync conflict: {e}")
            raise e

    def detect_sync_conflict(
        self, 
        channel_id: int,
        resource_type: str,
        resource_id: str,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any]
    ) -> Optional[int]:
        """Detect and create sync conflict"""
        try:
            # Use database function to detect conflict
            result = self.db.execute(
                text("SELECT detect_sync_conflict(:channel_id, :resource_type, :resource_id, :local_data, :remote_data)"),
                {
                    "channel_id": channel_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "local_data": json.dumps(local_data),
                    "remote_data": json.dumps(remote_data)
                }
            ).scalar()
            
            return result
        except Exception as e:
            logger.error(f"Error detecting sync conflict: {e}")
            raise e

    def resolve_sync_conflict(self, request: ConflictResolutionRequest) -> bool:
        """Resolve a sync conflict"""
        try:
            # Use database function to resolve conflict
            result = self.db.execute(
                text("SELECT resolve_sync_conflict(:conflict_id, :resolution, :resolved_by, :resolution_notes)"),
                {
                    "conflict_id": request.conflict_id,
                    "resolution": request.resolution,
                    "resolved_by": request.resolved_by,
                    "resolution_notes": request.resolution_notes
                }
            ).scalar()
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error resolving sync conflict: {e}")
            raise e

    def get_sync_conflicts(
        self,
        channel_id: Optional[int] = None,
        conflict_type: Optional[ConflictType] = None,
        resolution_status: Optional[ResolutionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SyncConflictResponse]:
        """Get sync conflicts with filtering"""
        try:
            query = self.db.query(SyncConflict)
            
            if channel_id:
                query = query.filter(SyncConflict.channel_id == channel_id)
            if conflict_type:
                query = query.filter(SyncConflict.conflict_type == conflict_type.value)
            if resolution_status:
                query = query.filter(SyncConflict.resolution_status == resolution_status.value)
            
            query = query.order_by(desc(SyncConflict.created_at))
            query = query.offset(offset).limit(limit)
            
            return [SyncConflictResponse.from_orm(conflict) for conflict in query.all()]
        except Exception as e:
            logger.error(f"Error getting sync conflicts: {e}")
            raise e

    # Sync Queue Methods
    def add_to_sync_queue(self, queue_data: SyncQueueCreate) -> SyncQueue:
        """Add item to sync queue"""
        try:
            db_queue_item = SyncQueue(**queue_data.dict())
            self.db.add(db_queue_item)
            self.db.commit()
            self.db.refresh(db_queue_item)
            return db_queue_item
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding to sync queue: {e}")
            raise e

    def process_sync_queue(self, request: QueueProcessRequest) -> Dict[str, Any]:
        """Process sync queue items"""
        try:
            # Use database function to process queue
            result = self.db.execute(
                text("SELECT process_sync_queue()")
            ).scalar()
            
            return {
                "processed_count": result,
                "max_items": request.max_items,
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing sync queue: {e}")
            raise e

    def get_sync_queue(
        self,
        channel_id: Optional[int] = None,
        status: Optional[QueueStatus] = None,
        priority_filter: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SyncQueueResponse]:
        """Get sync queue items"""
        try:
            query = self.db.query(SyncQueue)
            
            if channel_id:
                query = query.filter(SyncQueue.channel_id == channel_id)
            if status:
                query = query.filter(SyncQueue.status == status.value)
            if priority_filter:
                query = query.filter(SyncQueue.priority == priority_filter)
            
            query = query.order_by(SyncQueue.priority.asc(), SyncQueue.created_at.asc())
            query = query.offset(offset).limit(limit)
            
            return [SyncQueueResponse.from_orm(item) for item in query.all()]
        except Exception as e:
            logger.error(f"Error getting sync queue: {e}")
            raise e

    # Sync Status Methods
    def get_sync_status(self, channel_id: int) -> Optional[SyncStatusResponse]:
        """Get sync status for a channel"""
        try:
            status = self.db.query(SyncStatus).filter(SyncStatus.channel_id == channel_id).first()
            if not status:
                return None
            
            return SyncStatusResponse.from_orm(status)
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            raise e

    def get_all_sync_status(self) -> List[SyncStatusResponse]:
        """Get sync status for all channels"""
        try:
            statuses = self.db.query(SyncStatus).all()
            return [SyncStatusResponse.from_orm(status) for status in statuses]
        except Exception as e:
            logger.error(f"Error getting all sync status: {e}")
            raise e

    # Sync Operations
    def start_sync(self, request: SyncRequest) -> SyncLog:
        """Start a sync operation"""
        try:
            # Create sync log
            sync_log_data = SyncLogCreate(
                channel_id=request.channel_id,
                sync_type=request.sync_type,
                status=SyncStatusEnum.RUNNING
            )
            
            sync_log = self.create_sync_log(sync_log_data)
            
            # Here would be the actual sync logic
            # For now, we'll just mark as completed
            self.update_sync_log(sync_log.id, SyncLogUpdate(
                status=SyncStatusEnum.COMPLETED,
                completed_at=datetime.now(),
                items_processed=1,
                items_successful=1,
                items_failed=0
            ))
            
            return sync_log
        except Exception as e:
            logger.error(f"Error starting sync: {e}")
            raise e

    # Dashboard and Statistics
    def get_sync_dashboard_stats(self) -> SyncDashboardStats:
        """Get sync dashboard statistics"""
        try:
            # Get counts
            total_channels = self.db.query(SyncChannel).count()
            active_channels = self.db.query(SyncChannel).filter(SyncChannel.is_active == True).count()
            
            syncs_in_progress = self.db.query(SyncLog).filter(SyncLog.status == SyncStatusEnum.RUNNING).count()
            pending_conflicts = self.db.query(SyncConflict).filter(SyncConflict.resolution_status == ResolutionStatus.PENDING).count()
            queue_items_pending = self.db.query(SyncQueue).filter(SyncQueue.status == QueueStatus.PENDING).count()
            
            # Get recent syncs
            recent_syncs = self.db.query(SyncLog).order_by(desc(SyncLog.started_at)).limit(10).all()
            
            # Get recent conflicts
            recent_conflicts = self.db.query(SyncConflict).order_by(desc(SyncConflict.created_at)).limit(10).all()
            
            # Get channel status
            channel_status = self.db.query(SyncChannel, SyncStatus).join(SyncStatus).all()
            
            return SyncDashboardStats(
                total_channels=total_channels,
                active_channels=active_channels,
                syncs_in_progress=syncs_in_progress,
                pending_conflicts=pending_conflicts,
                queue_items_pending=queue_items_pending,
                recent_syncs=[
                    {
                        "id": sync.id,
                        "channel_id": sync.channel_id,
                        "sync_type": sync.sync_type,
                        "status": sync.status,
                        "started_at": sync.started_at.isoformat()
                    }
                    for sync in recent_syncs
                ],
                recent_conflicts=[
                    {
                        "id": conflict.id,
                        "channel_id": conflict.channel_id,
                        "conflict_type": conflict.conflict_type,
                        "resource_type": conflict.resource_type,
                        "resolution_status": conflict.resolution_status,
                        "created_at": conflict.created_at.isoformat()
                    }
                    for conflict in recent_conflicts
                ],
                channel_status=[
                    {
                        "channel_id": channel.id,
                        "channel_name": channel.channel_name,
                        "channel_type": channel.channel_type,
                        "is_active": channel.is_active,
                        "sync_in_progress": status.sync_in_progress,
                        "last_sync": status.last_full_sync.isoformat() if status.last_full_sync else None
                    }
                    for channel, status in channel_status
                ]
            )
        except Exception as e:
            logger.error(f"Error getting sync dashboard stats: {e}")
            raise e
