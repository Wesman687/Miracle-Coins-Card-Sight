from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict, Any
from app.models.collections import Collection
from app.models.collection_metadata import CollectionMetadata
from app.models.collection_images import CollectionImage
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CollectionAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_collection_analytics(self, collection_id: int) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific collection"""
        collection = self.db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            raise ValueError(f"Collection with id {collection_id} not found")
        
        # Basic collection info
        analytics = {
            "collection_id": collection_id,
            "collection_name": collection.name,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
            "days_since_creation": (datetime.utcnow() - collection.created_at).days,
            "days_since_update": (datetime.utcnow() - collection.updated_at).days
        }
        
        # Metadata analytics
        metadata_stats = self._get_metadata_analytics(collection_id)
        analytics.update(metadata_stats)
        
        # Image analytics
        image_stats = self._get_image_analytics(collection_id)
        analytics.update(image_stats)
        
        # Content analytics
        content_stats = self._get_content_analytics(collection)
        analytics.update(content_stats)
        
        # Engagement analytics (placeholder for future features)
        engagement_stats = self._get_engagement_analytics(collection_id)
        analytics.update(engagement_stats)
        
        return analytics
    
    def get_collections_overview(self) -> Dict[str, Any]:
        """Get overview analytics for all collections"""
        total_collections = self.db.query(Collection).count()
        
        # Recent activity
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_collections = self.db.query(Collection).filter(
            Collection.created_at >= last_week
        ).count()
        
        recent_updates = self.db.query(Collection).filter(
            Collection.updated_at >= last_week
        ).count()
        
        # Metadata usage
        collections_with_metadata = self.db.query(Collection).join(CollectionMetadata).distinct().count()
        
        # Image usage
        collections_with_images = self.db.query(Collection).join(CollectionImage).distinct().count()
        
        # Most active collections (by update frequency)
        most_active = self.db.query(
            Collection.id,
            Collection.name,
            func.count(Collection.id).label('update_count')
        ).filter(
            Collection.updated_at >= last_week
        ).group_by(Collection.id, Collection.name).order_by(desc('update_count')).limit(5).all()
        
        return {
            "total_collections": total_collections,
            "recent_collections": recent_collections,
            "recent_updates": recent_updates,
            "collections_with_metadata": collections_with_metadata,
            "collections_with_images": collections_with_images,
            "metadata_usage_percentage": (collections_with_metadata / total_collections * 100) if total_collections > 0 else 0,
            "image_usage_percentage": (collections_with_images / total_collections * 100) if total_collections > 0 else 0,
            "most_active_collections": [
                {
                    "id": col.id,
                    "name": col.name,
                    "update_count": col.update_count
                } for col in most_active
            ]
        }
    
    def get_metadata_analytics(self) -> Dict[str, Any]:
        """Get analytics about metadata usage across all collections"""
        # Field type distribution
        field_types = self.db.query(
            CollectionMetadata.field_type,
            func.count(CollectionMetadata.id).label('count')
        ).group_by(CollectionMetadata.field_type).all()
        
        # Most common field names
        common_fields = self.db.query(
            CollectionMetadata.field_name,
            func.count(CollectionMetadata.id).label('count')
        ).group_by(CollectionMetadata.field_name).order_by(desc('count')).limit(10).all()
        
        # Required vs optional fields
        required_fields = self.db.query(CollectionMetadata).filter(
            CollectionMetadata.is_required == True
        ).count()
        
        optional_fields = self.db.query(CollectionMetadata).filter(
            CollectionMetadata.is_required == False
        ).count()
        
        return {
            "field_type_distribution": {
                field_type: count for field_type, count in field_types
            },
            "most_common_fields": [
                {
                    "field_name": field_name,
                    "usage_count": count
                } for field_name, count in common_fields
            ],
            "required_vs_optional": {
                "required_fields": required_fields,
                "optional_fields": optional_fields,
                "required_percentage": (required_fields / (required_fields + optional_fields) * 100) if (required_fields + optional_fields) > 0 else 0
            }
        }
    
    def get_image_analytics(self) -> Dict[str, Any]:
        """Get analytics about image usage across all collections"""
        total_images = self.db.query(CollectionImage).count()
        featured_images = self.db.query(CollectionImage).filter(
            CollectionImage.is_featured == True
        ).count()
        
        # Image size distribution
        size_stats = self.db.query(
            func.avg(CollectionImage.file_size).label('avg_size'),
            func.min(CollectionImage.file_size).label('min_size'),
            func.max(CollectionImage.file_size).label('max_size'),
            func.sum(CollectionImage.file_size).label('total_size')
        ).filter(CollectionImage.file_size.isnot(None)).first()
        
        # Collections with most images
        collections_with_most_images = self.db.query(
            Collection.id,
            Collection.name,
            func.count(CollectionImage.id).label('image_count')
        ).join(CollectionImage).group_by(Collection.id, Collection.name).order_by(desc('image_count')).limit(5).all()
        
        return {
            "total_images": total_images,
            "featured_images": featured_images,
            "featured_percentage": (featured_images / total_images * 100) if total_images > 0 else 0,
            "size_statistics": {
                "average_size": int(size_stats.avg_size) if size_stats.avg_size else 0,
                "min_size": int(size_stats.min_size) if size_stats.min_size else 0,
                "max_size": int(size_stats.max_size) if size_stats.max_size else 0,
                "total_size": int(size_stats.total_size) if size_stats.total_size else 0
            },
            "collections_with_most_images": [
                {
                    "id": col.id,
                    "name": col.name,
                    "image_count": col.image_count
                } for col in collections_with_most_images
            ]
        }
    
    def _get_metadata_analytics(self, collection_id: int) -> Dict[str, Any]:
        """Get metadata analytics for a specific collection"""
        metadata_fields = self.db.query(CollectionMetadata).filter(
            CollectionMetadata.collection_id == collection_id
        ).all()
        
        if not metadata_fields:
            return {
                "metadata_fields_count": 0,
                "metadata_completion_percentage": 0,
                "field_types": {},
                "required_fields_completed": 0,
                "total_required_fields": 0
            }
        
        # Count fields with values
        fields_with_values = len([f for f in metadata_fields if f.field_value])
        required_fields = [f for f in metadata_fields if f.is_required]
        required_fields_completed = len([f for f in required_fields if f.field_value])
        
        # Field type distribution
        field_types = {}
        for field in metadata_fields:
            field_type = field.field_type
            field_types[field_type] = field_types.get(field_type, 0) + 1
        
        return {
            "metadata_fields_count": len(metadata_fields),
            "metadata_completion_percentage": (fields_with_values / len(metadata_fields) * 100) if metadata_fields else 0,
            "field_types": field_types,
            "required_fields_completed": required_fields_completed,
            "total_required_fields": len(required_fields),
            "required_fields_completion_percentage": (required_fields_completed / len(required_fields) * 100) if required_fields else 100
        }
    
    def _get_image_analytics(self, collection_id: int) -> Dict[str, Any]:
        """Get image analytics for a specific collection"""
        images = self.db.query(CollectionImage).filter(
            CollectionImage.collection_id == collection_id
        ).all()
        
        if not images:
            return {
                "images_count": 0,
                "has_featured_image": False,
                "total_image_size": 0,
                "average_image_size": 0
            }
        
        total_size = sum(img.file_size or 0 for img in images)
        featured_image = any(img.is_featured for img in images)
        
        return {
            "images_count": len(images),
            "has_featured_image": featured_image,
            "total_image_size": total_size,
            "average_image_size": total_size // len(images) if images else 0,
            "image_size_formatted": self._format_file_size(total_size)
        }
    
    def _get_content_analytics(self, collection: Collection) -> Dict[str, Any]:
        """Get content analytics for a collection"""
        description_length = len(collection.description or "")
        description_html_length = len(getattr(collection, 'description_html', None) or "")
        
        return {
            "description_length": description_length,
            "description_html_length": description_html_length,
            "has_description": bool(collection.description),
            "has_rich_description": bool(getattr(collection, 'description_html', None)),
            "has_shopify_integration": bool(collection.shopify_collection_id)
        }
    
    def _get_engagement_analytics(self, collection_id: int) -> Dict[str, Any]:
        """Get engagement analytics (placeholder for future features)"""
        # This would include metrics like:
        # - Views, clicks, interactions
        # - Search frequency
        # - User engagement
        # For now, return placeholder data
        
        return {
            "views": 0,  # Placeholder
            "searches": 0,  # Placeholder
            "interactions": 0,  # Placeholder
            "engagement_score": 0  # Placeholder
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
