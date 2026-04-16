from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict, Any
from app.models.collection_metadata import CollectionMetadata
from app.models.collections import Collection
from app.schemas.collection_metadata import (
    CollectionMetadataCreate, CollectionMetadataUpdate, 
    CollectionMetadataResponse, MetadataFieldType
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CollectionMetadataService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_metadata_field(self, collection_id: int, metadata: CollectionMetadataCreate) -> CollectionMetadata:
        """Create a new metadata field for a collection"""
        # Check if collection exists
        collection = self.db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            raise ValueError(f"Collection with id {collection_id} not found")
        
        # Check if field name already exists for this collection
        existing = self.db.query(CollectionMetadata).filter(
            and_(
                CollectionMetadata.collection_id == collection_id,
                CollectionMetadata.field_name == metadata.field_name
            )
        ).first()
        
        if existing:
            raise ValueError(f"Metadata field '{metadata.field_name}' already exists for this collection")
        
        # Validate field options for select fields
        if metadata.field_type == MetadataFieldType.SELECT and not metadata.field_options:
            raise ValueError("Select fields must have options defined")
        
        db_metadata = CollectionMetadata(
            collection_id=collection_id,
            **metadata.dict()
        )
        
        self.db.add(db_metadata)
        self.db.commit()
        self.db.refresh(db_metadata)
        
        logger.info(f"Created metadata field '{metadata.field_name}' for collection {collection_id}")
        return db_metadata
    
    def get_metadata_fields(self, collection_id: int) -> List[CollectionMetadata]:
        """Get all metadata fields for a collection"""
        return self.db.query(CollectionMetadata).filter(
            CollectionMetadata.collection_id == collection_id
        ).order_by(CollectionMetadata.sort_order, CollectionMetadata.field_name).all()
    
    def get_metadata_field(self, collection_id: int, field_id: int) -> Optional[CollectionMetadata]:
        """Get a specific metadata field"""
        return self.db.query(CollectionMetadata).filter(
            and_(
                CollectionMetadata.collection_id == collection_id,
                CollectionMetadata.id == field_id
            )
        ).first()
    
    def update_metadata_field(self, collection_id: int, field_id: int, metadata: CollectionMetadataUpdate) -> Optional[CollectionMetadata]:
        """Update a metadata field"""
        db_metadata = self.get_metadata_field(collection_id, field_id)
        if not db_metadata:
            return None
        
        # Check if new field name conflicts with existing field
        if metadata.field_name and metadata.field_name != db_metadata.field_name:
            existing = self.db.query(CollectionMetadata).filter(
                and_(
                    CollectionMetadata.collection_id == collection_id,
                    CollectionMetadata.field_name == metadata.field_name,
                    CollectionMetadata.id != field_id
                )
            ).first()
            
            if existing:
                raise ValueError(f"Metadata field '{metadata.field_name}' already exists for this collection")
        
        # Validate field options for select fields
        if metadata.field_type == MetadataFieldType.SELECT and not metadata.field_options:
            if not db_metadata.field_options:  # Only raise error if no existing options
                raise ValueError("Select fields must have options defined")
        
        update_data = metadata.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_metadata, field, value)
        
        self.db.commit()
        self.db.refresh(db_metadata)
        
        logger.info(f"Updated metadata field {field_id} for collection {collection_id}")
        return db_metadata
    
    def delete_metadata_field(self, collection_id: int, field_id: int) -> bool:
        """Delete a metadata field"""
        db_metadata = self.get_metadata_field(collection_id, field_id)
        if not db_metadata:
            return False
        
        self.db.delete(db_metadata)
        self.db.commit()
        
        logger.info(f"Deleted metadata field {field_id} for collection {collection_id}")
        return True
    
    def update_metadata_value(self, collection_id: int, field_id: int, value: str) -> Optional[CollectionMetadata]:
        """Update just the value of a metadata field"""
        db_metadata = self.get_metadata_field(collection_id, field_id)
        if not db_metadata:
            return None
        
        db_metadata.set_value(value)
        self.db.commit()
        self.db.refresh(db_metadata)
        
        return db_metadata
    
    def bulk_create_metadata_fields(self, collection_id: int, metadata_list: List[CollectionMetadataCreate]) -> List[CollectionMetadata]:
        """Create multiple metadata fields at once"""
        created_fields = []
        
        for metadata in metadata_list:
            try:
                field = self.create_metadata_field(collection_id, metadata)
                created_fields.append(field)
            except ValueError as e:
                logger.error(f"Failed to create metadata field '{metadata.field_name}': {str(e)}")
                # Continue with other fields
                continue
        
        return created_fields
    
    def get_metadata_stats(self, collection_id: int) -> Dict[str, Any]:
        """Get statistics about metadata fields for a collection"""
        fields = self.get_metadata_fields(collection_id)
        
        field_types = {}
        for field in fields:
            field_type = field.field_type
            field_types[field_type] = field_types.get(field_type, 0) + 1
        
        return {
            "total_fields": len(fields),
            "required_fields": len([f for f in fields if f.is_required]),
            "searchable_fields": len([f for f in fields if f.is_searchable]),
            "field_types": field_types
        }
    
    def search_collections_by_metadata(self, field_name: str, field_value: str, field_type: Optional[MetadataFieldType] = None) -> List[Collection]:
        """Search collections by metadata field value"""
        query = self.db.query(Collection).join(CollectionMetadata).filter(
            CollectionMetadata.field_name == field_name,
            CollectionMetadata.field_value.ilike(f"%{field_value}%")
        )
        
        if field_type:
            query = query.filter(CollectionMetadata.field_type == field_type)
        
        return query.all()
    
    def get_collections_with_metadata(self, metadata_filters: Dict[str, Any]) -> List[Collection]:
        """Get collections that match multiple metadata criteria"""
        query = self.db.query(Collection)
        
        for field_name, field_value in metadata_filters.items():
            query = query.join(CollectionMetadata).filter(
                CollectionMetadata.field_name == field_name,
                CollectionMetadata.field_value.ilike(f"%{field_value}%")
            )
        
        return query.distinct().all()
