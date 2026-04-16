from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
# from .collection_metadata import CollectionMetadataResponse
# from .collection_images import CollectionImageResponse

class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    description_html: Optional[str] = None  # Rich text description - may not be in DB yet
    color: str = Field('#3b82f6', pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    icon: Optional[str] = None
    image_url: Optional[str] = None  # Single image URL
    shopify_collection_id: Optional[str] = None
    # Temporary: Keep these fields until migration is run
    sort_order: int = Field(0, ge=0)
    default_markup: float = Field(1.3, gt=0, description="Default markup multiplier")

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    description_html: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    icon: Optional[str] = None
    image_url: Optional[str] = None  # Single image URL
    shopify_collection_id: Optional[str] = None
    # Temporary: Keep these fields until migration is run
    sort_order: Optional[int] = Field(None, ge=0)
    default_markup: Optional[float] = Field(None, gt=0, description="Default markup multiplier")

class CollectionResponse(CollectionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    coin_count: int = 0 # Added for frontend display
    metadata_fields: List[Any] = []  # Use Any instead of specific schema
    images: List[Any] = []  # Use Any instead of specific schema
    featured_image: Optional[Any] = None  # Use Any instead of specific schema

    class Config:
        from_attributes = True
        
    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle missing fields"""
        data = obj.__dict__ if hasattr(obj, '__dict__') else obj
        # Handle any missing fields gracefully
        return super().model_validate(data)

class CollectionWithDetails(CollectionResponse):
    """Extended collection response with full details"""
    metadata_stats: Optional[dict] = None
    image_stats: Optional[dict] = None
    analytics: Optional[dict] = None

class CollectionStatsResponse(BaseModel):
    total_collections: int
    active_collections: int
    most_popular_collection: Optional[CollectionResponse] = None
    last_updated: datetime

    class Config:
        from_attributes = True
