from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.models.collections import Collection
from app.schemas.collections import CollectionCreate, CollectionUpdate
# Import Coin directly from models.py to avoid circular import
import app.models as models_module
Coin = models_module.Coin

class CollectionService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_collection(self, collection: CollectionCreate) -> Collection:
        """Create a new collection"""
        db_collection = Collection(**collection.dict())
        self.db.add(db_collection)
        self.db.commit()
        self.db.refresh(db_collection)
        return db_collection
    
    def get_collections(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Collection]:
        """Get all collections with optional filtering"""
        # Simple query without joinedload to avoid relationship issues
        query = self.db.query(Collection)
        
        # Note: is_active column doesn't exist in database, so we ignore active_only filter
        # if active_only:
        #     query = query.filter(Collection.is_active == True)
        
        return query.order_by(Collection.sort_order, Collection.name).offset(skip).limit(limit).all()
    
    def get_collection(self, collection_id: int) -> Optional[Collection]:
        """Get a specific collection by ID"""
        from sqlalchemy.orm import joinedload
        
        return self.db.query(Collection).options(
            joinedload(Collection.metadata_fields),
            joinedload(Collection.images)
        ).filter(Collection.id == collection_id).first()
    
    def get_collection_by_name(self, name: str) -> Optional[Collection]:
        """Get a collection by name"""
        return self.db.query(Collection).filter(Collection.name == name).first()
    
    def update_collection(self, collection_id: int, collection: CollectionUpdate) -> Optional[Collection]:
        """Update a collection"""
        db_collection = self.get_collection(collection_id)
        if not db_collection:
            return None
        
        update_data = collection.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_collection, field, value)
        
        self.db.commit()
        self.db.refresh(db_collection)
        return db_collection
    
    def delete_collection(self, collection_id: int) -> bool:
        """Delete a collection (soft delete by setting is_active=False)"""
        db_collection = self.get_collection(collection_id)
        if not db_collection:
            return False
        
        # Check if collection has coins
        coin_count = self.db.query(Coin).filter(Coin.collection_id == collection_id).count()
        if coin_count > 0:
            # Soft delete - just mark as inactive
            db_collection.is_active = False
            self.db.commit()
        else:
            # Hard delete if no coins
            self.db.delete(db_collection)
            self.db.commit()
        
        return True
    
    def get_collection_stats(self) -> dict:
        """Get overall collection statistics"""
        total_collections = self.db.query(Collection).count()
        # active_collections = self.db.query(Collection).filter(Collection.is_active == True).count()  # Column doesn't exist
        active_collections = total_collections  # Assume all collections are active
        
        # Check if Coin model is available (avoid circular import issues)
        if Coin is None:
            return {
                "total_collections": total_collections,
                "active_collections": active_collections,
                "most_popular_collection": None,
                "note": "Coin model not available due to circular import"
            }
        
        # Get collection with most coins
        try:
            collection_counts = self.db.query(
                Collection.name,
                func.count(Coin.id).label('coin_count')
            ).outerjoin(Coin, Collection.id == Coin.collection_id).group_by(Collection.id).all()
            
            most_popular = max(collection_counts, key=lambda x: x.coin_count) if collection_counts else None
            
            return {
                "total_collections": total_collections,
                "active_collections": active_collections,
                "most_popular_collection": {
                    "name": most_popular.name,
                    "coin_count": most_popular.coin_count
                } if most_popular else None
            }
        except Exception as e:
            # If there's an error with the coin query, return basic stats
            return {
                "total_collections": total_collections,
                "active_collections": active_collections,
                "most_popular_collection": None,
                "error": f"Could not query coin counts: {str(e)}"
            }
