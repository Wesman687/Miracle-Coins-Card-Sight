"""
Two-Part SKU System Service
Format: [PREFIX]-[SEQUENCE] (e.g., ASE-001, MOR-002)
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime
import logging

from ..models.sku_system import SKUPrefix, SKUSequence
from ..schemas.sku_system import (
    SKUPrefixCreate, SKUPrefixUpdate, SKUGenerationRequest, 
    SKUGenerationResponse, SKUBulkOperationRequest, SKUBulkOperationResponse,
    SKUStatsResponse
)

logger = logging.getLogger(__name__)

class SKUService:
    def __init__(self, db: Session):
        self.db = db

    def create_prefix(self, prefix_data: SKUPrefixCreate) -> SKUPrefix:
        """Create a new SKU prefix"""
        try:
            db_prefix = SKUPrefix(
                prefix=prefix_data.prefix.upper(),
                description=prefix_data.description,
                auto_increment=prefix_data.auto_increment,
                current_sequence=0
            )
            self.db.add(db_prefix)
            self.db.commit()
            self.db.refresh(db_prefix)
            return db_prefix
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating SKU prefix: {e}")
            raise e

    def get_prefix(self, prefix_id: int) -> Optional[SKUPrefix]:
        """Get SKU prefix by ID"""
        return self.db.query(SKUPrefix).filter(SKUPrefix.id == prefix_id).first()

    def get_prefix_by_name(self, prefix: str) -> Optional[SKUPrefix]:
        """Get SKU prefix by name"""
        return self.db.query(SKUPrefix).filter(SKUPrefix.prefix == prefix.upper()).first()

    def list_prefixes(self, skip: int = 0, limit: int = 100) -> List[SKUPrefix]:
        """List all SKU prefixes"""
        return self.db.query(SKUPrefix).offset(skip).limit(limit).all()

    def update_prefix(self, prefix_id: int, prefix_data: SKUPrefixUpdate) -> Optional[SKUPrefix]:
        """Update SKU prefix"""
        try:
            db_prefix = self.get_prefix(prefix_id)
            if not db_prefix:
                return None
            
            update_data = prefix_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'prefix':
                    setattr(db_prefix, field, value.upper())
                else:
                    setattr(db_prefix, field, value)
            
            self.db.commit()
            self.db.refresh(db_prefix)
            return db_prefix
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating SKU prefix: {e}")
            raise e

    def delete_prefix(self, prefix_id: int) -> bool:
        """Delete SKU prefix (only if no sequences used)"""
        try:
            db_prefix = self.get_prefix(prefix_id)
            if not db_prefix:
                return False
            
            # Check if any sequences are used
            used_sequences = self.db.query(SKUSequence).filter(
                SKUSequence.prefix == db_prefix.prefix
            ).count()
            
            if used_sequences > 0:
                raise ValueError(f"Cannot delete prefix {db_prefix.prefix} - {used_sequences} sequences are in use")
            
            self.db.delete(db_prefix)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting SKU prefix: {e}")
            raise e

    def generate_next_sku(self, prefix: str) -> str:
        """Generate next SKU for a prefix"""
        try:
            # Use database function for atomic operation
            result = self.db.execute(
                text("SELECT generate_next_sku(:prefix)"),
                {"prefix": prefix.upper()}
            ).scalar()
            
            return result
        except Exception as e:
            logger.error(f"Error generating next SKU: {e}")
            raise e

    def generate_sku_range(self, prefix: str, count: int) -> Tuple[int, int]:
        """Generate a range of sequence numbers for bulk operations"""
        try:
            result = self.db.execute(
                text("SELECT * FROM get_next_sequence_range(:prefix, :count)"),
                {"prefix": prefix.upper(), "count": count}
            ).fetchone()
            
            return result[0], result[1]  # start_seq, end_seq
        except Exception as e:
            logger.error(f"Error generating SKU range: {e}")
            raise e

    def create_sku_sequence(self, prefix: str, sequence_number: int, coin_id: Optional[int] = None) -> SKUSequence:
        """Create a SKU sequence record"""
        try:
            db_sequence = SKUSequence(
                prefix=prefix.upper(),
                sequence_number=sequence_number,
                coin_id=coin_id
            )
            self.db.add(db_sequence)
            self.db.commit()
            self.db.refresh(db_sequence)
            return db_sequence
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating SKU sequence: {e}")
            raise e

    def get_sku_stats(self) -> SKUStatsResponse:
        """Get SKU system statistics"""
        try:
            # Total prefixes
            total_prefixes = self.db.query(SKUPrefix).count()
            
            # Total sequences used
            total_sequences = self.db.query(SKUSequence).count()
            
            # Most used prefix
            most_used = self.db.query(
                SKUSequence.prefix,
                func.count(SKUSequence.id).label('count')
            ).group_by(SKUSequence.prefix).order_by(
                func.count(SKUSequence.id).desc()
            ).first()
            
            # Least used prefix
            least_used = self.db.query(
                SKUSequence.prefix,
                func.count(SKUSequence.id).label('count')
            ).group_by(SKUSequence.prefix).order_by(
                func.count(SKUSequence.id).asc()
            ).first()
            
            # Recent activity
            recent_activity = self.db.query(SKUSequence).order_by(
                SKUSequence.used_at.desc()
            ).limit(10).all()
            
            return SKUStatsResponse(
                total_prefixes=total_prefixes,
                total_sequences_used=total_sequences,
                most_used_prefix=most_used[0] if most_used else None,
                least_used_prefix=least_used[0] if least_used else None,
                recent_activity=[
                    {
                        "prefix": seq.prefix,
                        "sequence": seq.sequence_number,
                        "used_at": seq.used_at.isoformat(),
                        "coin_id": seq.coin_id
                    }
                    for seq in recent_activity
                ]
            )
        except Exception as e:
            logger.error(f"Error getting SKU stats: {e}")
            raise e

    def migrate_existing_skus(self) -> Dict[str, Any]:
        """Migrate existing SKUs to new two-part format"""
        try:
            # This would be implemented to convert existing complex SKUs
            # to the new simple format
            # For now, return a placeholder
            return {
                "status": "migration_placeholder",
                "message": "Migration logic to be implemented based on existing SKU patterns"
            }
        except Exception as e:
            logger.error(f"Error migrating existing SKUs: {e}")
            raise e
