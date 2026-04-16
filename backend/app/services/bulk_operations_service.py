# backend/app/services/bulk_operations_service.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_
from datetime import datetime, timedelta
import asyncio
import logging
from ..models import BulkOperation, BulkOperationItem
# Import Coin directly from models.py file (not from models package)
import importlib.util
import os
models_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.py')
spec = importlib.util.spec_from_file_location("models_file", models_py_path)
models_file = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_file)
Coin = models_file.Coin
from ..schemas.bulk_operations import (
    BulkOperationCreate, BulkOperationResponse, BulkOperationStatusResponse,
    BulkTransferRequest, BulkPriceUpdateRequest, BulkStatusChangeRequest,
    BulkOperationStatsResponse, CoinData
)

logger = logging.getLogger(__name__)

class BulkOperationsService:
    def __init__(self, db: Session):
        self.db = db
        self.batch_size = 1000  # Process in batches of 1000
    
    async def create_bulk_purchase(
        self, 
        operation_data: BulkOperationCreate
    ) -> BulkOperationResponse:
        """Create bulk purchase operation with individual coin tracking"""
        
        try:
            # Create bulk operation record
            bulk_op = BulkOperation(
                operation_type=operation_data.operation_type.value,
                description=operation_data.description,
                total_items=len(operation_data.coins),
                created_by=operation_data.created_by,
                operation_metadata=operation_data.metadata or {}
            )
            self.db.add(bulk_op)
            self.db.flush()  # Get the ID without committing
            
            # Process coins in batches
            coins_created = []
            batch_items = []
            
            for i, coin_data in enumerate(operation_data.coins):
                try:
                    # Generate serial number
                    serial_number = f"{coin_data.sku}-{i+1:06d}"
                    
                    # Create individual coin for each quantity
                    for qty_idx in range(coin_data.quantity):
                        # Generate unique SKU for each coin
                        unique_sku = f"{coin_data.sku}-{i+1:06d}-{qty_idx+1:03d}"
                        coin = Coin(
                            sku=unique_sku,
                            name=coin_data.name,
                            year=coin_data.year,
                            denomination=coin_data.denomination,
                            mint_mark=coin_data.mint_mark,
                            grade=coin_data.grade,
                            category=coin_data.category,
                            description=coin_data.description,
                            condition_notes=coin_data.condition_notes,
                            is_silver=coin_data.is_silver,
                            silver_percent=coin_data.silver_percent,
                            silver_content_oz=coin_data.silver_content_oz,
                            paid_price=coin_data.paid_price,
                            price_strategy=coin_data.price_strategy,
                            quantity=1,  # Each coin is individual
                            status=coin_data.status,
                            bulk_operation_id=bulk_op.id,
                            bulk_sequence_number=i + 1,
                            serial_number=f"{serial_number}-{qty_idx+1:03d}",
                            created_by=str(operation_data.created_by or 1)
                        )
                        coins_created.append(coin)
                        self.db.add(coin)
                        
                        # Create bulk operation item
                        bulk_item = BulkOperationItem(
                            bulk_operation_id=bulk_op.id,
                            coin_id=None,  # Will be set after coin is committed
                            status='pending',
                            item_metadata={'coin_data': coin_data.dict()}
                        )
                        batch_items.append((bulk_item, coin))
                        
                        # Commit in batches
                        if len(coins_created) % self.batch_size == 0:
                            self.db.commit()
                            # Update bulk items with coin IDs
                            for item, coin in batch_items[-self.batch_size:]:
                                item.coin_id = coin.id
                            self.db.commit()
                            batch_items = []
                
                except Exception as e:
                    logger.error(f"Error creating coin {i}: {e}")
                    continue
            
            # Commit remaining items
            if coins_created:
                self.db.commit()
                # Update remaining bulk items with coin IDs
                for item, coin in batch_items:
                    item.coin_id = coin.id
                self.db.commit()
            
            # Update bulk operation with actual count
            bulk_op.total_items = len(coins_created)
            self.db.commit()
            
            return BulkOperationResponse.from_orm(bulk_op)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in bulk purchase: {e}")
            raise e
    
    async def process_bulk_operation(self, operation_id: int) -> Dict[str, Any]:
        """Process bulk operation with progress tracking"""
        
        bulk_op = self.db.query(BulkOperation).filter(
            BulkOperation.id == operation_id
        ).first()
        
        if not bulk_op:
            raise ValueError("Bulk operation not found")
        
        bulk_op.status = 'processing'
        self.db.commit()
        
        try:
            # Get pending items
            pending_items = self.db.query(BulkOperationItem).filter(
                and_(
                    BulkOperationItem.bulk_operation_id == operation_id,
                    BulkOperationItem.status == 'pending'
                )
            ).all()
            
            processed = 0
            failed = 0
            
            # Process items in batches
            for i in range(0, len(pending_items), self.batch_size):
                batch = pending_items[i:i + self.batch_size]
                
                for item in batch:
                    try:
                        # Process the item based on operation type
                        await self._process_item(item, bulk_op.operation_type)
                        item.status = 'completed'
                        item.processed_at = datetime.utcnow()
                        processed += 1
                        
                    except Exception as e:
                        item.status = 'failed'
                        item.error_message = str(e)
                        item.processed_at = datetime.utcnow()
                        failed += 1
                        logger.error(f"Error processing item {item.id}: {e}")
                
                # Update progress
                bulk_op.processed_items = processed
                bulk_op.failed_items = failed
                self.db.commit()
            
            # Complete operation
            if failed == 0:
                bulk_op.status = 'completed'
            else:
                bulk_op.status = 'failed' if processed == 0 else 'completed'
            
            bulk_op.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                'operation_id': operation_id,
                'status': bulk_op.status,
                'processed': processed,
                'failed': failed,
                'total': bulk_op.total_items
            }
            
        except Exception as e:
            bulk_op.status = 'failed'
            bulk_op.completed_at = datetime.utcnow()
            self.db.commit()
            logger.error(f"Error processing bulk operation {operation_id}: {e}")
            raise e
    
    async def _process_item(self, item: BulkOperationItem, operation_type: str):
        """Process individual bulk operation item"""
        
        if operation_type == 'purchase':
            # For purchase, items are already created, just mark as processed
            pass
        elif operation_type == 'transfer':
            # Update coin location
            coin = self.db.query(Coin).filter(Coin.id == item.coin_id).first()
            if coin:
                # Mark as transferred (coin transfer logic would go here)
                self.db.commit()
        elif operation_type == 'price_update':
            # Update coin pricing
            coin = self.db.query(Coin).filter(Coin.id == item.coin_id).first()
            if coin and item.item_metadata:
                price_data = item.item_metadata.get('price_data', {})
                if 'price_strategy' in price_data:
                    coin.price_strategy = price_data['price_strategy']
                if 'computed_price' in price_data:
                    coin.computed_price = price_data['computed_price']
                self.db.commit()
        elif operation_type == 'status_change':
            # Update coin status
            coin = self.db.query(Coin).filter(Coin.id == item.coin_id).first()
            if coin and item.item_metadata:
                new_status = item.item_metadata.get('new_status')
                if new_status:
                    coin.status = new_status
                    self.db.commit()
    
    async def get_operation_status(self, operation_id: int) -> BulkOperationStatusResponse:
        """Get bulk operation status and progress"""
        
        bulk_op = self.db.query(BulkOperation).filter(
            BulkOperation.id == operation_id
        ).first()
        
        if not bulk_op:
            raise ValueError("Bulk operation not found")
        
        progress_percentage = (
            (bulk_op.processed_items + bulk_op.failed_items) / bulk_op.total_items * 100
            if bulk_op.total_items > 0 else 0
        )
        
        # Get error messages
        errors = []
        if bulk_op.failed_items > 0:
            failed_items = self.db.query(BulkOperationItem).filter(
                and_(
                    BulkOperationItem.bulk_operation_id == operation_id,
                    BulkOperationItem.status == 'failed'
                )
            ).limit(10).all()
            errors = [item.error_message for item in failed_items if item.error_message]
        
        # Estimate completion time
        estimated_completion = None
        if bulk_op.status == 'processing' and bulk_op.processed_items > 0:
            # Simple estimation based on current progress
            remaining_items = bulk_op.total_items - bulk_op.processed_items - bulk_op.failed_items
            if remaining_items > 0:
                avg_time_per_item = 0.1  # seconds per item (rough estimate)
                estimated_seconds = remaining_items * avg_time_per_item
                estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
        
        return BulkOperationStatusResponse(
            id=operation_id,
            status=bulk_op.status,
            total_items=bulk_op.total_items,
            processed_items=bulk_op.processed_items,
            failed_items=bulk_op.failed_items,
            progress_percentage=round(progress_percentage, 2),
            estimated_completion=estimated_completion,
            errors=errors
        )
    
    async def cancel_operation(self, operation_id: int) -> Dict[str, Any]:
        """Cancel bulk operation"""
        
        bulk_op = self.db.query(BulkOperation).filter(
            BulkOperation.id == operation_id
        ).first()
        
        if not bulk_op:
            raise ValueError("Bulk operation not found")
        
        if bulk_op.status in ['completed', 'failed', 'cancelled']:
            raise ValueError(f"Cannot cancel operation with status: {bulk_op.status}")
        
        bulk_op.status = 'cancelled'
        bulk_op.completed_at = datetime.utcnow()
        
        # Cancel pending items
        pending_items = self.db.query(BulkOperationItem).filter(
            and_(
                BulkOperationItem.bulk_operation_id == operation_id,
                BulkOperationItem.status == 'pending'
            )
        ).all()
        
        for item in pending_items:
            item.status = 'failed'
            item.error_message = 'Operation cancelled'
            item.processed_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            'operation_id': operation_id,
            'status': 'cancelled',
            'cancelled_items': len(pending_items)
        }
    
    async def get_operation_stats(self) -> BulkOperationStatsResponse:
        """Get bulk operation statistics"""
        
        # Get basic stats
        total_ops = self.db.query(BulkOperation).count()
        completed_ops = self.db.query(BulkOperation).filter(
            BulkOperation.status == 'completed'
        ).count()
        failed_ops = self.db.query(BulkOperation).filter(
            BulkOperation.status == 'failed'
        ).count()
        pending_ops = self.db.query(BulkOperation).filter(
            BulkOperation.status.in_(['pending', 'processing'])
        ).count()
        
        # Get total coins processed
        total_coins = self.db.query(func.sum(BulkOperation.total_items)).scalar() or 0
        
        # Get average operation size
        avg_size = self.db.query(func.avg(BulkOperation.total_items)).scalar() or 0
        
        # Get success rate
        success_rate = (completed_ops / total_ops * 100) if total_ops > 0 else 0
        
        # Get last operation date
        last_op = self.db.query(BulkOperation).order_by(
            BulkOperation.created_at.desc()
        ).first()
        last_operation_date = last_op.created_at if last_op else None
        
        return BulkOperationStatsResponse(
            total_operations=total_ops,
            completed_operations=completed_ops,
            failed_operations=failed_ops,
            pending_operations=pending_ops,
            total_coins_processed=int(total_coins),
            average_operation_size=round(float(avg_size), 2),
            success_rate=round(success_rate, 2),
            last_operation_date=last_operation_date
        )
    
    async def create_bulk_transfer(
        self, 
        request: BulkTransferRequest
    ) -> BulkOperationResponse:
        """Create bulk transfer operation"""
        
        # Create bulk operation
        bulk_op = BulkOperation(
            operation_type=request.operation_type.value,
            description=request.description,
            total_items=len(request.coin_ids),
            created_by=request.created_by,
                operation_metadata=request.metadata or {}
        )
        self.db.add(bulk_op)
        self.db.flush()
        
        # Create bulk operation items
        for coin_id in request.coin_ids:
            bulk_item = BulkOperationItem(
                bulk_operation_id=bulk_op.id,
                coin_id=coin_id,
                status='pending',
                item_metadata={
                    'from_location': request.from_location,
                    'to_location': request.to_location
                }
            )
            self.db.add(bulk_item)
        
        self.db.commit()
        return BulkOperationResponse.from_orm(bulk_op)
    
    async def create_bulk_price_update(
        self, 
        request: BulkPriceUpdateRequest
    ) -> BulkOperationResponse:
        """Create bulk price update operation"""
        
        # Create bulk operation
        bulk_op = BulkOperation(
            operation_type=request.operation_type.value,
            description=request.description,
            total_items=len(request.coin_ids),
            created_by=request.created_by,
                operation_metadata=request.metadata or {}
        )
        self.db.add(bulk_op)
        self.db.flush()
        
        # Create bulk operation items
        for coin_id in request.coin_ids:
            bulk_item = BulkOperationItem(
                bulk_operation_id=bulk_op.id,
                coin_id=coin_id,
                status='pending',
                item_metadata={
                    'price_strategy': request.price_strategy,
                    'price_multiplier': request.price_multiplier,
                    'fixed_price': request.fixed_price
                }
            )
            self.db.add(bulk_item)
        
        self.db.commit()
        return BulkOperationResponse.from_orm(bulk_op)
    
    async def create_bulk_status_change(
        self, 
        request: BulkStatusChangeRequest
    ) -> BulkOperationResponse:
        """Create bulk status change operation"""
        
        # Create bulk operation
        bulk_op = BulkOperation(
            operation_type=request.operation_type.value,
            description=request.description,
            total_items=len(request.coin_ids),
            created_by=request.created_by,
                operation_metadata=request.metadata or {}
        )
        self.db.add(bulk_op)
        self.db.flush()
        
        # Create bulk operation items
        for coin_id in request.coin_ids:
            bulk_item = BulkOperationItem(
                bulk_operation_id=bulk_op.id,
                coin_id=coin_id,
                status='pending',
                item_metadata={
                    'new_status': request.new_status
                }
            )
            self.db.add(bulk_item)
        
        self.db.commit()
        return BulkOperationResponse.from_orm(bulk_op)
