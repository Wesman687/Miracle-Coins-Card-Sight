from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict, Any
from app.models.collection_images import CollectionImage
from app.models.collections import Collection
from app.schemas.collection_images import (
    CollectionImageCreate, CollectionImageUpdate, 
    CollectionImageResponse, CollectionImageUpload
)
from datetime import datetime
import logging
import requests
from PIL import Image
import io

logger = logging.getLogger(__name__)

class CollectionImageService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_image(self, collection_id: int, image_data: CollectionImageCreate) -> CollectionImage:
        """Create a new image record for a collection"""
        # Check if collection exists
        collection = self.db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            raise ValueError(f"Collection with id {collection_id} not found")
        
        # If this is set as featured, unset other featured images
        if image_data.is_featured:
            self._unset_featured_images(collection_id)
        
        db_image = CollectionImage(
            collection_id=collection_id,
            **image_data.dict()
        )
        
        # Get image metadata if possible
        try:
            self._populate_image_metadata(db_image)
        except Exception as e:
            logger.warning(f"Could not populate image metadata: {str(e)}")
        
        self.db.add(db_image)
        self.db.commit()
        self.db.refresh(db_image)
        
        logger.info(f"Created image record for collection {collection_id}")
        return db_image
    
    def get_images(self, collection_id: int) -> List[CollectionImage]:
        """Get all images for a collection"""
        return self.db.query(CollectionImage).filter(
            CollectionImage.collection_id == collection_id
        ).order_by(CollectionImage.sort_order, CollectionImage.uploaded_at).all()
    
    def get_image(self, collection_id: int, image_id: int) -> Optional[CollectionImage]:
        """Get a specific image"""
        return self.db.query(CollectionImage).filter(
            and_(
                CollectionImage.collection_id == collection_id,
                CollectionImage.id == image_id
            )
        ).first()
    
    def get_featured_image(self, collection_id: int) -> Optional[CollectionImage]:
        """Get the featured image for a collection"""
        return self.db.query(CollectionImage).filter(
            and_(
                CollectionImage.collection_id == collection_id,
                CollectionImage.is_featured == True
            )
        ).first()
    
    def update_image(self, collection_id: int, image_id: int, image_data: CollectionImageUpdate) -> Optional[CollectionImage]:
        """Update an image record"""
        db_image = self.get_image(collection_id, image_id)
        if not db_image:
            return None
        
        # If setting as featured, unset other featured images
        if image_data.is_featured and not db_image.is_featured:
            self._unset_featured_images(collection_id)
        
        update_data = image_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_image, field, value)
        
        self.db.commit()
        self.db.refresh(db_image)
        
        logger.info(f"Updated image {image_id} for collection {collection_id}")
        return db_image
    
    def delete_image(self, collection_id: int, image_id: int) -> bool:
        """Delete an image record"""
        db_image = self.get_image(collection_id, image_id)
        if not db_image:
            return False
        
        # TODO: Delete actual image file from storage
        # This would integrate with the file uploader service
        
        self.db.delete(db_image)
        self.db.commit()
        
        logger.info(f"Deleted image {image_id} for collection {collection_id}")
        return True
    
    def set_featured_image(self, collection_id: int, image_id: int) -> Optional[CollectionImage]:
        """Set an image as the featured image for a collection"""
        db_image = self.get_image(collection_id, image_id)
        if not db_image:
            return None
        
        # Unset other featured images
        self._unset_featured_images(collection_id)
        
        # Set this image as featured
        db_image.is_featured = True
        self.db.commit()
        self.db.refresh(db_image)
        
        logger.info(f"Set image {image_id} as featured for collection {collection_id}")
        return db_image
    
    def reorder_images(self, collection_id: int, image_orders: Dict[int, int]) -> bool:
        """Reorder images by updating their sort_order"""
        try:
            for image_id, sort_order in image_orders.items():
                db_image = self.get_image(collection_id, image_id)
                if db_image:
                    db_image.sort_order = sort_order
            
            self.db.commit()
            logger.info(f"Reordered images for collection {collection_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reorder images: {str(e)}")
            self.db.rollback()
            return False
    
    def get_image_stats(self, collection_id: int) -> Dict[str, Any]:
        """Get statistics about images for a collection"""
        images = self.get_images(collection_id)
        
        if not images:
            return {
                "total_images": 0,
                "featured_images": 0,
                "total_size": 0,
                "total_size_formatted": "0 B",
                "average_size": 0,
                "average_size_formatted": "0 B"
            }
        
        total_size = sum(img.file_size or 0 for img in images)
        featured_count = len([img for img in images if img.is_featured])
        average_size = total_size // len(images) if images else 0
        
        return {
            "total_images": len(images),
            "featured_images": featured_count,
            "total_size": total_size,
            "total_size_formatted": self._format_file_size(total_size),
            "average_size": average_size,
            "average_size_formatted": self._format_file_size(average_size)
        }
    
    def _unset_featured_images(self, collection_id: int):
        """Unset all featured images for a collection"""
        self.db.query(CollectionImage).filter(
            and_(
                CollectionImage.collection_id == collection_id,
                CollectionImage.is_featured == True
            )
        ).update({"is_featured": False})
    
    def _populate_image_metadata(self, db_image: CollectionImage):
        """Populate image metadata from the image URL"""
        try:
            # Download image to get metadata
            response = requests.get(db_image.image_url, timeout=10)
            response.raise_for_status()
            
            # Get file size
            db_image.file_size = len(response.content)
            
            # Get image dimensions and MIME type
            image = Image.open(io.BytesIO(response.content))
            db_image.width, db_image.height = image.size
            db_image.mime_type = response.headers.get('content-type', 'image/jpeg')
            
        except Exception as e:
            logger.warning(f"Could not populate metadata for image {db_image.image_url}: {str(e)}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def bulk_upload_images(self, collection_id: int, image_urls: List[str], upload_data: CollectionImageUpload) -> List[CollectionImage]:
        """Bulk upload multiple images"""
        created_images = []
        
        for i, image_url in enumerate(image_urls):
            try:
                image_data = CollectionImageCreate(
                    image_url=image_url,
                    alt_text=upload_data.alt_text,
                    caption=upload_data.caption,
                    is_featured=upload_data.is_featured and i == 0,  # Only first image can be featured
                    sort_order=i
                )
                
                image = self.create_image(collection_id, image_data)
                created_images.append(image)
                
            except Exception as e:
                logger.error(f"Failed to create image record for {image_url}: {str(e)}")
                continue
        
        return created_images
