from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_admin_user
from app.services.collection_service import CollectionService
from app.services.collection_metadata_service import CollectionMetadataService
from app.services.collection_image_service import CollectionImageService
from app.services.collection_analytics_service import CollectionAnalyticsService
from app.schemas.collections import CollectionCreate, CollectionUpdate, CollectionResponse, CollectionWithDetails

router = APIRouter(tags=["collections"])

@router.post("/", response_model=CollectionResponse)
async def create_collection(
    collection: CollectionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new collection"""
    collection_service = CollectionService(db)
    
    # Check if collection name already exists
    existing = collection_service.get_collection_by_name(collection.name)
    if existing:
        raise HTTPException(status_code=400, detail="Collection name already exists")
    
    return collection_service.create_collection(collection)

@router.get("", response_model=List[CollectionResponse])
@router.get("/", response_model=List[CollectionResponse])
async def get_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all collections with coin counts"""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Get collections with coin counts using coin_collections junction table
            collections_query = text('''
                SELECT c.id, c.name, c.description, c.color, c.icon, c.image_url,
                       c.shopify_collection_id, c.sort_order, c.default_markup, 
                       c.created_at, c.updated_at,
                       COALESCE(coin_counts.coin_count, 0) as coin_count
                FROM collections c
                LEFT JOIN (
                    SELECT collection_id, COUNT(*) as coin_count 
                    FROM coin_collections 
                    GROUP BY collection_id
                ) coin_counts ON c.id = coin_counts.collection_id
                ORDER BY c.sort_order, c.name 
                LIMIT :limit OFFSET :skip
            ''')
            
            collections_result = conn.execute(collections_query, {"limit": limit, "skip": skip})
            collections = collections_result.fetchall()
        
        responses = []
        for collection in collections:
            response_data = {
                "id": collection[0],
                "name": collection[1],
                "description": collection[2],
                "color": collection[3],
                "icon": collection[4],
                "image_url": collection[5],
                "shopify_collection_id": collection[6],
                "sort_order": collection[7] or 0,
                "default_markup": float(collection[8]) if collection[8] else 1.3,
                "created_at": collection[9].isoformat() if collection[9] else None,
                "updated_at": collection[10].isoformat() if collection[10] else None,
                "coin_count": collection[11],
                "metadata_fields": [],
                "images": [],
                "featured_image": None
            }
            responses.append(response_data)
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/stats")
async def get_collection_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get collection statistics"""
    collection_service = CollectionService(db)
    return collection_service.get_collection_stats()

@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get a specific collection by ID"""
    collection_service = CollectionService(db)
    
    collection = collection_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return collection

@router.get("/{collection_id}/details", response_model=CollectionWithDetails)
async def get_collection_details(
    collection_id: int,
    include_analytics: bool = Query(False, description="Include analytics data"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get a collection with full details including metadata, images, and analytics"""
    collection_service = CollectionService(db)
    
    collection = collection_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Get metadata and images
    metadata_service = CollectionMetadataService(db)
    image_service = CollectionImageService(db)
    
    metadata_fields = metadata_service.get_metadata_fields(collection_id)
    images = image_service.get_images(collection_id)
    featured_image = image_service.get_featured_image(collection_id)
    
    # Get analytics if requested
    analytics = None
    metadata_stats = None
    image_stats = None
    
    if include_analytics:
        analytics_service = CollectionAnalyticsService(db)
        analytics = analytics_service.get_collection_analytics(collection_id)
        metadata_stats = metadata_service.get_metadata_stats(collection_id)
        image_stats = image_service.get_image_stats(collection_id)
    
    # Build response
    response_data = {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "description_html": getattr(collection, 'description_html', None),
        "color": collection.color,
        "icon": collection.icon,
        "sort_order": collection.sort_order,
        "shopify_collection_id": collection.shopify_collection_id,
        "default_markup": collection.default_markup,
        "created_at": collection.created_at,
        "updated_at": collection.updated_at,
        "coin_count": collection.coin_count,
        "metadata_fields": metadata_fields,
        "images": images,
        "featured_image": featured_image,
        "metadata_stats": metadata_stats,
        "image_stats": image_stats,
        "analytics": analytics
    }
    
    return CollectionWithDetails(**response_data)

@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: int,
    collection: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update a collection"""
    collection_service = CollectionService(db)
    
    # Check if new name conflicts with existing collection
    if collection.name:
        existing = collection_service.get_collection_by_name(collection.name)
        if existing and existing.id != collection_id:
            raise HTTPException(status_code=400, detail="Collection name already exists")
    
    updated_collection = collection_service.update_collection(collection_id, collection)
    if not updated_collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return updated_collection

@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete a collection"""
    collection_service = CollectionService(db)
    
    success = collection_service.delete_collection(collection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return {"message": "Collection deleted successfully"}