from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_admin_user
from app.services.collection_image_service import CollectionImageService
from app.schemas.collection_images import (
    CollectionImageCreate, CollectionImageUpdate, CollectionImageResponse,
    CollectionImageUpload, CollectionImageStats
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["collection-images"])

@router.post("/collections/{collection_id}/images", response_model=CollectionImageResponse)
async def create_image_record(
    collection_id: int,
    image_data: CollectionImageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new image record for a collection"""
    try:
        image_service = CollectionImageService(db)
        return image_service.create_image(collection_id, image_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create image record: {str(e)}")

@router.post("/collections/{collection_id}/images/upload", response_model=CollectionImageResponse)
async def upload_image(
    collection_id: int,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    is_featured: bool = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Upload an image file and create a record"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # TODO: Integrate with existing file uploader service
        # For now, we'll create a placeholder URL
        # In production, this would upload to the file server and return the actual URL
        
        # Simulate file upload (replace with actual file uploader integration)
        image_url = f"https://file-server.stream-lineai.com/collections/{collection_id}/{file.filename}"
        
        # Create image data
        image_data = CollectionImageCreate(
            image_url=image_url,
            alt_text=alt_text,
            caption=caption,
            is_featured=is_featured
        )
        
        image_service = CollectionImageService(db)
        return image_service.create_image(collection_id, image_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.get("/collections/{collection_id}/images", response_model=List[CollectionImageResponse])
async def get_images(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all images for a collection"""
    try:
        image_service = CollectionImageService(db)
        images = image_service.get_images(collection_id)
        return images
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get images: {str(e)}")

@router.get("/collections/{collection_id}/images/{image_id}", response_model=CollectionImageResponse)
async def get_image(
    collection_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get a specific image"""
    try:
        image_service = CollectionImageService(db)
        image = image_service.get_image(collection_id, image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        return image
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image: {str(e)}")

@router.get("/collections/{collection_id}/images/featured", response_model=CollectionImageResponse)
async def get_featured_image(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get the featured image for a collection"""
    try:
        image_service = CollectionImageService(db)
        image = image_service.get_featured_image(collection_id)
        if not image:
            raise HTTPException(status_code=404, detail="No featured image found")
        return image
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get featured image: {str(e)}")

@router.put("/collections/{collection_id}/images/{image_id}", response_model=CollectionImageResponse)
async def update_image(
    collection_id: int,
    image_id: int,
    image_data: CollectionImageUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update an image record"""
    try:
        image_service = CollectionImageService(db)
        image = image_service.update_image(collection_id, image_id, image_data)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        return image
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update image: {str(e)}")

@router.patch("/collections/{collection_id}/images/{image_id}/featured", response_model=CollectionImageResponse)
async def set_featured_image(
    collection_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Set an image as the featured image for a collection"""
    try:
        image_service = CollectionImageService(db)
        image = image_service.set_featured_image(collection_id, image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        return image
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set featured image: {str(e)}")

@router.delete("/collections/{collection_id}/images/{image_id}")
async def delete_image(
    collection_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete an image record and file"""
    try:
        image_service = CollectionImageService(db)
        success = image_service.delete_image(collection_id, image_id)
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        return {"message": "Image deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

@router.post("/collections/{collection_id}/images/reorder")
async def reorder_images(
    collection_id: int,
    image_orders: dict,  # {image_id: sort_order}
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Reorder images by updating their sort order"""
    try:
        image_service = CollectionImageService(db)
        success = image_service.reorder_images(collection_id, image_orders)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reorder images")
        return {"message": "Images reordered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reorder images: {str(e)}")

@router.get("/collections/{collection_id}/images/stats", response_model=CollectionImageStats)
async def get_image_stats(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get image statistics for a collection"""
    try:
        image_service = CollectionImageService(db)
        stats = image_service.get_image_stats(collection_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image stats: {str(e)}")

@router.post("/collections/{collection_id}/images/bulk-upload", response_model=List[CollectionImageResponse])
async def bulk_upload_images(
    collection_id: int,
    files: List[UploadFile] = File(...),
    alt_text: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    is_featured: bool = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Upload multiple images at once"""
    try:
        if len(files) > 10:  # Limit bulk uploads
            raise HTTPException(status_code=400, detail="Maximum 10 images allowed per bulk upload")
        
        # Validate all files
        for file in files:
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be an image")
        
        # TODO: Integrate with actual file uploader service
        # For now, create placeholder URLs
        image_urls = [f"https://file-server.stream-lineai.com/collections/{collection_id}/{file.filename}" for file in files]
        
        upload_data = CollectionImageUpload(
            alt_text=alt_text,
            caption=caption,
            is_featured=is_featured
        )
        
        image_service = CollectionImageService(db)
        images = image_service.bulk_upload_images(collection_id, image_urls, upload_data)
        return images
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk upload images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk upload images: {str(e)}")

