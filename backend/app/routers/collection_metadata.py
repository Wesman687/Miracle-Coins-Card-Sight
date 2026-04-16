from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_admin_user
from app.services.collection_metadata_service import CollectionMetadataService
from app.schemas.collection_metadata import (
    CollectionMetadataCreate, CollectionMetadataUpdate, CollectionMetadataResponse,
    CollectionMetadataBulkCreate, MetadataFieldValueUpdate, CollectionMetadataStats
)

router = APIRouter(tags=["collection-metadata"])

@router.post("/collections/{collection_id}/metadata", response_model=CollectionMetadataResponse)
async def create_metadata_field(
    collection_id: int,
    metadata: CollectionMetadataCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new metadata field for a collection"""
    try:
        metadata_service = CollectionMetadataService(db)
        return metadata_service.create_metadata_field(collection_id, metadata)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create metadata field: {str(e)}")

@router.get("/collections/{collection_id}/metadata", response_model=List[CollectionMetadataResponse])
async def get_metadata_fields(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all metadata fields for a collection"""
    try:
        metadata_service = CollectionMetadataService(db)
        fields = metadata_service.get_metadata_fields(collection_id)
        return fields
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata fields: {str(e)}")

@router.get("/collections/{collection_id}/metadata/{field_id}", response_model=CollectionMetadataResponse)
async def get_metadata_field(
    collection_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get a specific metadata field"""
    try:
        metadata_service = CollectionMetadataService(db)
        field = metadata_service.get_metadata_field(collection_id, field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Metadata field not found")
        return field
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata field: {str(e)}")

@router.put("/collections/{collection_id}/metadata/{field_id}", response_model=CollectionMetadataResponse)
async def update_metadata_field(
    collection_id: int,
    field_id: int,
    metadata: CollectionMetadataUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update a metadata field"""
    try:
        metadata_service = CollectionMetadataService(db)
        field = metadata_service.update_metadata_field(collection_id, field_id, metadata)
        if not field:
            raise HTTPException(status_code=404, detail="Metadata field not found")
        return field
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metadata field: {str(e)}")

@router.patch("/collections/{collection_id}/metadata/{field_id}/value")
async def update_metadata_value(
    collection_id: int,
    field_id: int,
    value_update: MetadataFieldValueUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update just the value of a metadata field"""
    try:
        metadata_service = CollectionMetadataService(db)
        field = metadata_service.update_metadata_value(collection_id, field_id, value_update.field_value)
        if not field:
            raise HTTPException(status_code=404, detail="Metadata field not found")
        return {"message": "Metadata value updated successfully", "field": field}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metadata value: {str(e)}")

@router.delete("/collections/{collection_id}/metadata/{field_id}")
async def delete_metadata_field(
    collection_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete a metadata field"""
    try:
        metadata_service = CollectionMetadataService(db)
        success = metadata_service.delete_metadata_field(collection_id, field_id)
        if not success:
            raise HTTPException(status_code=404, detail="Metadata field not found")
        return {"message": "Metadata field deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete metadata field: {str(e)}")

@router.post("/collections/{collection_id}/metadata/bulk", response_model=List[CollectionMetadataResponse])
async def bulk_create_metadata_fields(
    collection_id: int,
    bulk_data: CollectionMetadataBulkCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create multiple metadata fields at once"""
    try:
        metadata_service = CollectionMetadataService(db)
        fields = metadata_service.bulk_create_metadata_fields(collection_id, bulk_data.metadata_fields)
        return fields
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create metadata fields: {str(e)}")

@router.get("/collections/{collection_id}/metadata/stats", response_model=CollectionMetadataStats)
async def get_metadata_stats(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get metadata statistics for a collection"""
    try:
        metadata_service = CollectionMetadataService(db)
        stats = metadata_service.get_metadata_stats(collection_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata stats: {str(e)}")

@router.get("/metadata/search")
async def search_collections_by_metadata(
    field_name: str = Query(..., description="Name of the metadata field to search"),
    field_value: str = Query(..., description="Value to search for"),
    field_type: Optional[str] = Query(None, description="Type of the metadata field"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Search collections by metadata field value"""
    try:
        metadata_service = CollectionMetadataService(db)
        collections = metadata_service.search_collections_by_metadata(field_name, field_value, field_type)
        return {
            "collections": collections,
            "search_criteria": {
                "field_name": field_name,
                "field_value": field_value,
                "field_type": field_type
            },
            "total_results": len(collections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search collections: {str(e)}")

