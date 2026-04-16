from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.auth import get_current_admin_user
from app.services.collection_analytics_service import CollectionAnalyticsService

router = APIRouter(tags=["collection-analytics"])

@router.get("/collections/{collection_id}/analytics")
async def get_collection_analytics(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get comprehensive analytics for a specific collection"""
    try:
        analytics_service = CollectionAnalyticsService(db)
        analytics = analytics_service.get_collection_analytics(collection_id)
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection analytics: {str(e)}")

@router.get("/collections/analytics/overview")
async def get_collections_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get overview analytics for all collections"""
    try:
        analytics_service = CollectionAnalyticsService(db)
        overview = analytics_service.get_collections_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collections overview: {str(e)}")

@router.get("/collections/analytics/metadata")
async def get_metadata_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get analytics about metadata usage across all collections"""
    try:
        analytics_service = CollectionAnalyticsService(db)
        analytics = analytics_service.get_metadata_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata analytics: {str(e)}")

@router.get("/collections/analytics/images")
async def get_image_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get analytics about image usage across all collections"""
    try:
        analytics_service = CollectionAnalyticsService(db)
        analytics = analytics_service.get_image_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image analytics: {str(e)}")

